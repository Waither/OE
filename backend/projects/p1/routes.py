from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.common.randomness import create_random_generator
from backend.common.run_service import create_run
from backend.database import get_db
from backend.projects.p1.logic import (
    BENCHMARKS,
    GAConfig,
    GeneticAlgorithm,
    available_benchmarks,
)

router = APIRouter()


class GARunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    function_key: str = "ackley01"
    dimensions: int = Field(default=5, ge=1, le=100)
    precision: int = Field(default=8, ge=1, le=24)
    population_size: int = Field(default=40, ge=2, le=2000)
    epochs: int = Field(default=100, ge=1, le=10000)
    objective: Literal["minimize", "maximize"] = "minimize"
    selection: Literal["best", "worst", "roulette", "tournament"] = "tournament"
    tournament_size: int = Field(default=3, ge=2, le=2000)
    crossover: Literal["one_point", "two_point", "uniform", "grain"] = "two_point"
    crossover_probability: float = Field(default=0.8, ge=0, le=1)
    mutation: Literal["boundary", "one_point", "two_point"] = "one_point"
    mutation_probability: float = Field(default=0.02, ge=0, le=1)
    inversion_probability: float = Field(default=0.05, ge=0, le=1)
    elite_count: int = Field(default=2, ge=0, le=1999)
    grain_probability: float = Field(default=0.5, ge=0, le=1)
    seed: int | None = Field(default=None, ge=0, lt=2**63)


@router.get("/benchmarks")
def benchmarks() -> list[dict[str, object]]:
    return available_benchmarks()


@router.post("/run", status_code=201)
def run_genetic_algorithm(
    request: GARunRequest,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    config = GAConfig(**request.model_dump(exclude={"seed"}))
    actual_seed, _ = create_random_generator(request.seed)
    result = GeneticAlgorithm(config, seed=actual_seed).run()
    record = create_run(
        session,
        project_key="p1",
        seed=actual_seed,
        algorithm_version="p1-ga-1.0",
        parameters=config.__dict__,
        result_data=result.as_dict(),
    )
    return {
        "run_id": record.id,
        "seed": actual_seed,
        "function": BENCHMARKS[config.function_key].name,
        "result": result.as_dict(),
    }
