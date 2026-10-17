from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.models.chart_artifact import ChartArtifact
from backend.models.run_record import RunRecord

ALLOWED_PROJECTS = frozenset({"p1", "p2", "p3", "p4"})
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def create_run(session: Session, *, project_key: str, seed: int, algorithm_version: str, parameters: dict[str, Any], result_data: Any) -> RunRecord:
    if project_key not in ALLOWED_PROJECTS:
        raise ValueError(f"Nieobsługiwany projekt: {project_key}")
    if not 0 <= seed < 2**63:
        raise ValueError("Seed musi być liczbą z zakresu 0–2**63-1.")
    if not algorithm_version or len(algorithm_version) > 64:
        raise ValueError("Wersja algorytmu musi mieć od 1 do 64 znaków.")

    run = RunRecord(
        project_key=project_key,
        seed=seed,
        algorithm_version=algorithm_version,
        parameters=parameters,
        result_data=result_data,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: str) -> RunRecord:
    run = session.get(RunRecord, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono uruchomienia.")
    return run


def list_runs(session: Session, *, project_key: str | None, limit: int) -> Sequence[RunRecord]:
    statement = select(RunRecord).order_by(RunRecord.created_at.desc()).limit(limit)
    if project_key is not None:
        if project_key not in ALLOWED_PROJECTS:
            raise HTTPException(status_code=404, detail="Nie znaleziono projektu.")
        statement = statement.where(RunRecord.project_key == project_key)
    return session.scalars(statement).all()


def save_chart_png(session: Session, *, run: RunRecord, name: str, content: bytes, artifact_root: Path) -> ChartArtifact:
    if not content.startswith(PNG_SIGNATURE):
        raise HTTPException(status_code=415, detail="Plik nie jest prawidłowym obrazem PNG.")
    if not name.strip() or len(name) > 120:
        raise HTTPException(status_code=422, detail="Nazwa wykresu musi mieć 1–120 znaków.")

    artifact_id = str(uuid4())
    relative_path = Path("artifacts") / run.id / f"{artifact_id}.png"
    destination = artifact_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)

    artifact = ChartArtifact(
        id=artifact_id,
        run_id=run.id,
        name=name.strip(),
        file_path=relative_path.as_posix(),
    )
    session.add(artifact)
    
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        destination.unlink(missing_ok=True)
        raise
    session.refresh(artifact)
    return artifact


def get_chart_artifacts(session: Session, run_id: str) -> Sequence[ChartArtifact]:
    get_run(session, run_id)
    statement = (
        select(ChartArtifact)
        .where(ChartArtifact.run_id == run_id)
        .order_by(ChartArtifact.created_at.asc())
    )
    return session.scalars(statement).all()


def get_chart_file(artifact: ChartArtifact, artifact_root: Path) -> Path:
    root = artifact_root.resolve()
    file_path = (root / artifact.file_path).resolve()
    if not file_path.is_relative_to(root) or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Nie znaleziono pliku wykresu.")
    return file_path
