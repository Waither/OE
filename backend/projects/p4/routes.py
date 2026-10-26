from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from backend.common.randomness import create_random_generator
from backend.common.run_service import create_run
from backend.database import get_db
from backend.projects.p4.logic import ABCConfig, BENCHMARKS, available_benchmarks, run

router = APIRouter()


class ABCRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    function_key: Literal["quadratic", "ackley01", "hyperellipsoid", "cec2014_f3", "cec2014_f1"] = "ackley01"
    dimensions: int = Field(5, ge=1, le=100)
    population_size: int = Field(40, ge=5, le=2000)
    epochs: int = Field(100, ge=1, le=10000)
    n_limits: int = Field(25, ge=1, le=10000)
    objective: Literal["min", "max"] = "min"
    seed: int | None = Field(None, ge=0, lt=2**63)

    @model_validator(mode="after")
    def validate_configuration(self) -> "ABCRunRequest":
        ABCConfig(**self.model_dump(exclude={"seed"})).validate()
        return self


class ABCExperimentRequest(ABCRunRequest):
    repetitions: int = Field(10, ge=1, le=100)


def _config(request: ABCRunRequest) -> ABCConfig:
    return ABCConfig(**request.model_dump(exclude={"seed", "repetitions"}))


@router.get("/benchmarks")
def benchmarks() -> list[dict[str, object]]:
    return available_benchmarks()


@router.post("/run", status_code=201)
def run_abc(request: ABCRunRequest, session: Session = Depends(get_db)) -> dict[str, Any]:
    actual_seed, _ = create_random_generator(request.seed)
    config = _config(request)
    result = run(config, actual_seed)
    record = create_run(session, project_key="p4", seed=actual_seed, algorithm_version="p4-abc-mealpy-1.0",
                        parameters=config.__dict__, result_data=result.as_dict())
    return {"run_id": record.id, "seed": actual_seed, "seed_exact": str(actual_seed),
            "function": BENCHMARKS[config.function_key].name, "result": result.as_dict()}


@router.post("/experiment", status_code=201)
def run_experiment(request: ABCExperimentRequest, session: Session = Depends(get_db)) -> dict[str, Any]:
    actual_seed, generator = create_random_generator(request.seed)
    config = _config(request)
    experiment_id = str(uuid4())
    runs = []
    for index in range(request.repetitions):
        seed = generator.randrange(2**63)
        result = run(config, seed)
        record = create_run(session, project_key="p4", seed=seed, algorithm_version="p4-abc-mealpy-1.0",
                            parameters={**config.__dict__, "experiment": {"id": experiment_id, "index": index}},
                            result_data=result.as_dict())
        runs.append({"run_id": record.id, "seed": seed, "result": result.as_dict()})
    values = [item["result"]["best_objective"] for item in runs]
    return {"experiment_id": experiment_id, "seed": actual_seed, "seed_exact": str(actual_seed),
            "repetitions": request.repetitions, "configuration": config.__dict__, "runs": runs,
            "summary": {"average_objective": sum(values) / len(values),
                        "best_objective": min(values) if config.objective == "min" else max(values),
                        "worst_objective": max(values) if config.objective == "min" else min(values)}}
