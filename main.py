from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.web import router as web_router

app = FastAPI(title="Behavioral Context Engine", version="1.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(web_router)

@app.get("/health")
def health():
    return {"status": "ok"}
