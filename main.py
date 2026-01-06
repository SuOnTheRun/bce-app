from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.web import router as web_router

app = FastAPI(title="Behavioral Context Engine", version="1.0")

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)
app.include_router(web_router)

@app.get("/health")
def health():
    return {"status": "ok"}
