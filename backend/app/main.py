from fastapi import FastAPI
from .database import engine, Base
from . import models

# Ensure all database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GENESIS Backend", version="0.1.0")

# Enable CORS for local development
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from .routers import projects, candidates, knowledge, chemistry, docking, visualization, screening, qsar_adme, ingestion, predictive_models, generation, iterative_loop

# app.include_router(api.router)  # removed: no api module
app.include_router(projects.router)
app.include_router(candidates.router)
app.include_router(knowledge.router)
app.include_router(chemistry.router)
app.include_router(docking.router)
app.include_router(visualization.router)
app.include_router(screening.router)
app.include_router(qsar_adme.router)
app.include_router(ingestion.router)
app.include_router(predictive_models.router)
app.include_router(generation.router)
app.include_router(iterative_loop.router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


# Mount production frontend (SPA) if dist bundle exists
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .runtime_config import FRONTEND_DIST

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        api_prefixes = (
            "docs", "openapi.json", "redoc", "health",
            "projects", "candidates", "knowledge", "chem",
            "docking", "visualization", "screening", "ai_models",
            "ingestion", "iterative_loop", "models_ai"
        )
        if full_path and any(full_path.startswith(p) for p in api_prefixes):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API endpoint not found")

        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

