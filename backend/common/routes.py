from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.common.csv_export import create_run_csv_response
from backend.common.run_service import (
    get_chart_comparison_file,
    get_chart_artifacts,
    get_chart_file,
    get_run,
    delete_project_runs,
    list_chart_comparisons,
    list_runs,
    save_chart_comparison,
    save_chart_png,
)
from backend.database import get_db
from backend.models.chart_artifact import ChartArtifact
from backend.models.chart_comparison import ChartComparison
from backend.schemas.runs import ChartArtifactRead, ChartComparisonRead, RunRead

router = APIRouter(prefix="/api/runs", tags=["runs"])
ARTIFACT_ROOT = Path(__file__).resolve().parents[1] / "data"
MAX_CHART_BYTES = 10 * 1024 * 1024


@router.get("", response_model=list[RunRead])
def runs_list(session: Annotated[Session, Depends(get_db)], project_key: Annotated[str | None, Query(pattern=r"^p[1-4]$")] = None, limit: Annotated[int, Query(ge=1, le=200)] = 50) -> list[RunRead]:
    return [
        RunRead.model_validate(run)
        for run in list_runs(session, project_key=project_key, limit=limit)
    ]


@router.delete("/project/{project_key}")
def clear_project_runs(project_key: str, session: Annotated[Session, Depends(get_db)]) -> dict[str, int | str]:
    deleted_runs = delete_project_runs(
        session,
        project_key=project_key,
        artifact_root=ARTIFACT_ROOT,
    )
    return {"project_key": project_key, "deleted_runs": deleted_runs}


@router.get("/comparisons", response_model=list[ChartComparisonRead])
def comparisons_list(
    session: Annotated[Session, Depends(get_db)],
    project_key: Annotated[str, Query(pattern=r"^p[1-4]$")] = "p1",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ChartComparisonRead]:
    return [
        ChartComparisonRead.model_validate(comparison)
        for comparison in list_chart_comparisons(
            session,
            project_key=project_key,
            limit=limit,
        )
    ]


@router.post("/comparisons", response_model=ChartComparisonRead, status_code=201)
async def create_comparison(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    project_key: Annotated[str, Query(pattern=r"^p[1-4]$")],
    metric: Annotated[str, Query(min_length=1, max_length=32)],
    run_ids: Annotated[list[str], Query()],
) -> ChartComparison:
    if len(run_ids) < 2 or len(run_ids) > 200:
        raise HTTPException(status_code=422, detail="Wybierz od 2 do 200 uruchomień.")
    content_type = request.headers.get("content-type", "").split(";", maxsplit=1)[0]
    if content_type != "image/png":
        raise HTTPException(status_code=415, detail="Wymagany jest obraz PNG.")

    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_CHART_BYTES:
            raise HTTPException(status_code=413, detail="Obraz przekracza limit 10 MiB.")
        content.extend(chunk)

    return save_chart_comparison(
        session,
        project_key=project_key,
        run_ids=run_ids,
        metric=metric,
        content=bytes(content),
        artifact_root=ARTIFACT_ROOT,
    )


@router.get("/comparisons/{comparison_id}/image")
def download_comparison_image(
    comparison_id: str,
    session: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    comparison = session.get(ChartComparison, comparison_id)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono zapisanego porównania.")
    return FileResponse(
        get_chart_comparison_file(comparison, ARTIFACT_ROOT),
        media_type="image/png",
        filename=f"comparison-{comparison.id}.png",
    )


@router.get("/{run_id}", response_model=RunRead)
def run_details(run_id: str, session: Annotated[Session, Depends(get_db)],) -> RunRead:
    return RunRead.model_validate(get_run(session, run_id))


@router.get("/{run_id}/export.csv")
def run_csv(run_id: str, session: Annotated[Session, Depends(get_db)],) -> Response:
    return create_run_csv_response(get_run(session, run_id))


@router.get("/{run_id}/charts", response_model=list[ChartArtifactRead])
def run_charts(run_id: str, session: Annotated[Session, Depends(get_db)],) -> list[ChartArtifactRead]:
    return [
        ChartArtifactRead.model_validate(artifact)
        for artifact in get_chart_artifacts(session, run_id)
    ]


@router.post("/{run_id}/charts", response_model=ChartArtifactRead, status_code=201)
async def upload_run_chart(run_id: str, request: Request, session: Annotated[Session, Depends(get_db)], name: Annotated[str, Query(min_length=1, max_length=120)]) -> ChartArtifact:
    content_type = request.headers.get("content-type", "").split(";", maxsplit=1)[0]
    if content_type != "image/png":
        raise HTTPException(status_code=415, detail="Wymagany jest obraz PNG.")
    
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_CHART_BYTES:
            raise HTTPException(status_code=413, detail="Obraz przekracza limit 10 MiB.")
        content.extend(chunk)

    run = get_run(session, run_id)
    return save_chart_png(
        session,
        run=run,
        name=name,
        content=bytes(content),
        artifact_root=ARTIFACT_ROOT,
    )


@router.get("/{run_id}/charts/{artifact_id}")
def download_run_chart(run_id: str, artifact_id: str, session: Annotated[Session, Depends(get_db)]) -> FileResponse:
    get_run(session, run_id)
    artifact = session.get(ChartArtifact, artifact_id)
    if artifact is None or artifact.run_id != run_id:
        raise HTTPException(status_code=404, detail="Nie znaleziono wykresu.")
    
    return FileResponse(
        get_chart_file(artifact, ARTIFACT_ROOT),
        media_type=artifact.media_type,
        filename=f"chart-{artifact.id}.png",
    )
