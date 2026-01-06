import os
import json
from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.models import DecisionMap
from app.prompts import (
    PASS_A_SYSTEM, PASS_A_USER_TEMPLATE,
    PASS_B_SYSTEM, PASS_B_USER_TEMPLATE
)
from app.excel import generate_template_xlsx, parse_template_xlsx
from app.llm_router import generate_structured, generate_text, provider

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def _required(value: str, name: str) -> str:
    v = (value or "").strip()
    if not v:
        raise ValueError(f"Missing required field: {name}")
    return v

def _friendly_error(e: Exception) -> str:
    msg = str(e)
    if "insufficient_quota" in msg or "You exceeded your current quota" in msg:
        return (
            "API quota is not available for the current key.\n\n"
            "No-pay workaround enabled:\n"
            "Set LLM_PROVIDER=offline in Render and redeploy.\n"
        )
    return msg

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "output": None,
        "error": None,
        "input_used": None
    })

@router.get("/template")
def download_template():
    content = generate_template_xlsx()
    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bce_campaign_template.xlsx"}
    )

@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    tone: str = Form(default="Internal"),
    category: str = Form(default=""),
    objective: str = Form(default=""),
    channels: str = Form(default=""),
    market: str = Form(default=""),
    flight_dates: str = Form(default=""),
    audience_logic: str = Form(default=""),
    creative_notes: str = Form(default=""),
    measurement_type: str = Form(default=""),
    key_result: str = Form(default=""),
    poi_context: str = Form(default=""),
    notes: str = Form(default=""),
    excel: UploadFile | None = File(default=None),
):
    try:
        if excel and excel.filename:
            raw = await excel.read()
            campaign = parse_template_xlsx(raw)
            input_used = {"source": "excel", "campaign": campaign}
        else:
            campaign = {
                "Category": _required(category, "Category"),
                "Objective": _required(objective, "Objective"),
                "Channels": _required(channels, "Channels"),
                "Market": _required(market, "Market"),
                "Flight_Dates": (flight_dates or "").strip(),
                "Audience_Logic": _required(audience_logic, "Audience_Logic"),
                "Creative_Notes": (creative_notes or "").strip(),
                "Measurement_Type": (measurement_type or "").strip(),
                "Key_Result": (key_result or "").strip(),
                "POI_Context": (poi_context or "").strip(),
                "Notes": (notes or "").strip(),
            }
            input_used = {"source": "manual", "campaign": campaign}

        campaign_json = json.dumps(campaign, ensure_ascii=False, indent=2)

        pass_a_model = os.getenv("PASS_A_MODEL", "gpt-4o-mini").strip()
        pass_b_model = os.getenv("PASS_B_MODEL", "gpt-4o").strip()

        pass_a_user = PASS_A_USER_TEMPLATE.format(campaign_json=campaign_json)
        decision_map = generate_structured(
            model=pass_a_model,
            system_instruction=PASS_A_SYSTEM,
            user_prompt=pass_a_user,
            response_model=DecisionMap,
        )

        decision_map_json = decision_map.model_dump_json(indent=2)

        pass_b_user = PASS_B_USER_TEMPLATE.format(decision_map_json=decision_map_json)
        brief_text = generate_text(
            model=pass_b_model,
            system_instruction=PASS_B_SYSTEM,
            user_prompt=pass_b_user,
            decision_map_json=decision_map_json,
        )

        return templates.TemplateResponse("index.html", {
            "request": request,
            "output": {
                "brief": brief_text,
                "decision_map_json": decision_map_json,
                "confidence": decision_map.confidence_assessment.model_dump(),
                "provider": provider(),
                "models": {"pass_a": pass_a_model, "pass_b": pass_b_model},
            },
            "error": None,
            "input_used": input_used,
            "tone": tone
        })

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "output": None,
            "error": _friendly_error(e),
            "input_used": None
        })
