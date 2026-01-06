from io import BytesIO
import pandas as pd

TEMPLATE_COLUMNS = [
    "Category",
    "Objective",
    "Channels",
    "Market",
    "Flight_Dates",
    "Audience_Logic",
    "Creative_Notes",
    "Measurement_Type",
    "Key_Result",
    "POI_Context",
    "Notes"
]

def generate_template_xlsx() -> bytes:
    sample = pd.DataFrame([{
        "Category": "Retail",
        "Objective": "Drive in-store footfall during promo window",
        "Channels": "DOOH, Display",
        "Market": "US - NYC",
        "Flight_Dates": "2026-02-01 to 2026-02-28",
        "Audience_Logic": "People frequently present near retail corridors and competitor clusters",
        "Creative_Notes": "Promo-led message + convenience framing, debranded",
        "Measurement_Type": "Footfall",
        "Key_Result": "Directional: uplift observed",
        "POI_Context": "Big-box retail parks + transit-adjacent retail",
        "Notes": "Promo window coincides with payday week"
    }], columns=TEMPLATE_COLUMNS)

    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        sample.to_excel(writer, sheet_name="Campaign_Input", index=False)
    return bio.getvalue()

def parse_template_xlsx(file_bytes: bytes) -> dict:
    bio = BytesIO(file_bytes)
    df = pd.read_excel(bio, sheet_name="Campaign_Input")
    if df.empty:
        raise ValueError("Excel sheet 'Campaign_Input' is empty.")

    row = df.iloc[0].to_dict()

    cleaned = {k: ("" if pd.isna(v) else str(v).strip()) for k, v in row.items()}

    missing = [c for c in ["Category", "Objective", "Channels", "Market", "Audience_Logic"] if not cleaned.get(c)]
    if missing:
        raise ValueError(f"Missing required fields in Excel: {', '.join(missing)}")

    return cleaned
