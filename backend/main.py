from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(
    title="LegalEase API",
    description="AI-powered legal document drafting backend.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "LegalEase API",
        "status": "running",
        "docs": "/docs",
    }


app.include_router(router)
