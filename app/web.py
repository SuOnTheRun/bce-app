import os
import json
from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.models import DecisionMap
from app.excel import generate_template_xlsx, parse_template_xlsx
from app.llm_router import generate_structured, generate_text, provider  # keep your offline/openai/gemini router

from app.prompts import (
    PASS_A_SYSTEM, PASS_A_USER_TEMPLATE,
    PASS_B_SYSTEM, PASS_B_USER_TEMPLATE
)

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
            "LLM quota is not available for the current API key.\n\n"
            "No-pay workaround:\n"
            "- Set LLM_PROVIDER=offline in Render.\n"
        )
    if "OPENAI_API_KEY is not set" in msg or "GEMINI_API_KEY is not set" in msg:
        return (
            "API key missing.\n\n"
            "No-pay workaround:\n"
            "- Set LLM_PROVIDER=offline in Render.\n"
        )
    return msg

def _group_signals(dm: dict) -> dict:
    # dm["observable_signals"] items look like: {"signal": "...", "classification": "Observed|Inferred|Hypothesis", ...}
    observed, inferred, hypothesis = [], [], []
    for s in dm.get("observable_signals", []) or []:
        txt = (s.get("signal") or "").strip()
        cls = (s.get("classification") or "").strip().lower()
        if not txt:
            continue
        if cls == "observed":
            observed.append(txt)
        elif cls == "inferred":
            inferred.append(txt)
        elif cls == "hypothesis":
            hypothesis.append(txt)
        else:
            inferred.append(txt)
    return {"observed": observed, "inferred": inferred, "hypothesis": hypothesis}

def _derive_headline(dm: dict) -> tuple[str, str]:
    # Tight, executive-style headline + subhead
    decision = (dm.get("decision_being_influenced") or "").strip()
    tension = (dm.get("behavioral_tension", {}) or {}).get("tradeoff", "")
    why = (dm.get("behavioral_tension", {}) or {}).get("why_this_tension_exists", "")

    headline = decision if decision else "A decision becomes influenceable when context collapses friction and creates a go-now reason."
    subhead_parts = []
    if tension:
        subhead_parts.append(f"Tension: {tension}.")
    if why:
        subhead_parts.append(why)
    subhead = " ".join(subhead_parts).strip()
    return headline, subhead

def _derive_why_this_works(dm: dict) -> list[str]:
    # Use strategic levers if available; otherwise fall back to planning implications.
    levers = dm.get("strategic_levers") or []
    bullets = [x.strip() for x in levers if isinstance(x, str) and x.strip()]

    if len(bullets) >= 3:
        return bullets[:3]

    pi = dm.get("planning_implications") or {}
    # fallback bullets crafted from planning implication text (shortened)
    fallback = []
    if pi.get("what_to_prioritize"):
        fallback.append("Detour cost collapses when inventory is route-adjacent and dayparted correctly.")
    if pi.get("channel_role_logic"):
        fallback.append("DOOH validates in-moment; Display enables follow-through when attention returns to mobile.")
    bt = dm.get("behavioral_tension") or {}
    if bt.get("tradeoff"):
        fallback.append(f"The message works when it resolves the tension: {bt.get('tradeoff')}.")
    combined = bullets + fallback
    # dedupe preserving order
    seen, out = set(), []
    for b in combined:
        if b not in seen:
            out.append(b); seen.add(b)
    return out[:3] if out else ["Route adjacency + urgency framing reduces friction and increases visit probability."]

@router.get("/health")
def health():
    return {"status": "ok"}

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
        # 1) Input
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

        # 2) Pass A: Structured decision map
        pass_a_model = os.getenv("PASS_A_MODEL", "gpt-4o-mini").strip()
        pass_a_user = PASS_A_USER_TEMPLATE.format(campaign_json=campaign_json)

        decision_map_obj = generate_structured(
            model=pass_a_model,
            system_instruction=PASS_A_SYSTEM,
            user_prompt=pass_a_user,
            response_model=DecisionMap,
        )
        dm = decision_map_obj.model_dump()
        decision_map_json = json.dumps(dm, ensure_ascii=False, indent=2)

        # 3) Pass B: Narrative brief (optional; you can keep or remove)
        pass_b_model = os.getenv("PASS_B_MODEL", "gpt-4o").strip()
        pass_b_user = PASS_B_USER_TEMPLATE.format(decision_map_json=decision_map_json)

        brief_text = generate_text(
            model=pass_b_model,
            system_instruction=PASS_B_SYSTEM,
            user_prompt=pass_b_user,
            decision_map_json=decision_map_json,
        )

        # 4) Derivations for the redesigned UI
        headline, subhead = _derive_headline(dm)
        signals = _group_signals(dm)
        why_this_works = _derive_why_this_works(dm)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "output": {
                # legacy (kept)
                "brief": brief_text,
                "decision_map_json": decision_map_json,

                # new structured payload for the UI
                "dm": dm,
                "headline": headline,
                "subhead": subhead,
                "signals": signals,
                "why_this_works": why_this_works,

                # metadata
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
