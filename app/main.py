from fastapi import FastAPI

from app.core.config import get_settings
from app.core.db import Base, engine
from app.api.routes import ingest, summary

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.app_name}


app.include_router(ingest.router, prefix="", tags=["ingest"])
app.include_router(summary.router, prefix="", tags=["summary"])