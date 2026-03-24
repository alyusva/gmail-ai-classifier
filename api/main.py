"""
Gmail Classifier — FastAPI multi-usuario
Arrancar: uvicorn api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import extract, classify, apply, stats

app = FastAPI(
    title="Gmail Classifier API",
    description="Backend multi-usuario para clasificar emails con IA",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://tu-dominio.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract.router,  prefix="/extract",  tags=["extract"])
app.include_router(classify.router, prefix="/classify", tags=["classify"])
app.include_router(apply.router,    prefix="/apply",    tags=["apply"])
app.include_router(stats.router,    prefix="/stats",    tags=["stats"])


@app.get("/health")
def health():
    return {"status": "ok"}
