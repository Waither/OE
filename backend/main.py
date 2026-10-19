from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from backend.common.routes import router as runs_router
from backend.database import engine
from backend.models import Base
from backend.projects.p1.routes import router as p1_router
from backend.projects.p2.routes import router as p2_router
from backend.projects.p3.routes import router as p3_router
from backend.projects.p4.routes import router as p4_router

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="OE API", lifespan=lifespan)

app.include_router(runs_router)
app.include_router(p1_router, prefix="/api/p1", tags=["P1"])
app.include_router(p2_router, prefix="/api/p2", tags=["P2"])
app.include_router(p3_router, prefix="/api/p3", tags=["P3"])
app.include_router(p4_router, prefix="/api/p4", tags=["P4"])

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
PROJECT_ROUTES = frozenset({"1", "2", "3", "4", "history"})


@app.get("/api/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def serve_frontend(path: Path) -> FileResponse:
    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail="Frontend nie został jeszcze zbudowany. Uruchom `npm run build` w katalogu frontend.",
        )
    return FileResponse(path)


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return serve_frontend(FRONTEND_DIST / "index.html")


@app.get("/{project_id}", include_in_schema=False)
def project_page(project_id: str) -> FileResponse:
    if project_id not in PROJECT_ROUTES:
        raise HTTPException(status_code=404, detail="Nie znaleziono projektu.")
    return serve_frontend(FRONTEND_DIST / "index.html")


@app.get("/{asset_path:path}", include_in_schema=False)
def frontend_asset(asset_path: str) -> FileResponse:
    frontend_root = FRONTEND_DIST.resolve()
    asset = (frontend_root / asset_path).resolve()
    if not asset.is_relative_to(frontend_root) or not asset.is_file():
        raise HTTPException(status_code=404, detail="Nie znaleziono zasobu.")
    return FileResponse(asset)
