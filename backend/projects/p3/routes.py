from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from backend.common.randomness import create_random_generator
from backend.common.run_service import create_run
from backend.database import get_db
from backend.projects.p3.logic import GAConfig, run

router = APIRouter()


class GARunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    function_key: Literal["quadratic", "hyperellipsoid", "ackley01", "cec2014_f3"] = "quadratic"
    representation: Literal["binary", "real"] = "binary"
    dimensions: int = Field(2, ge=1, le=20)
    num_genes: int = Field(60, ge=1, le=1000)
    lower_bound: float = 0
    upper_bound: float = 1
    num_generations: int = Field(100, ge=1, le=10000)
    sol_per_pop: int = Field(40, ge=2, le=2000)
    num_parents_mating: int = Field(20, ge=2, le=2000)
    mutation_num_genes: int = Field(2, ge=1, le=1000)
    parent_selection_type: Literal["tournament", "rws", "random"] = "tournament"
    crossover_type: Literal["single_point", "two_points", "uniform", "arithmetic", "blend_alpha", "blend_alpha_beta", "average"] = "single_point"
    mutation_type: Literal["random", "swap", "gaussian"] = "random"
    mutation_probability: float = Field(.02, ge=0, le=1)
    crossover_probability: float = Field(.8, ge=0, le=1)
    keep_elitism: int = Field(1, ge=0, le=1999)
    tournament_size: int = Field(3, ge=2, le=2000)
    objective: Literal["minimize", "maximize"] = "minimize"
    seed: int | None = Field(None, ge=0, lt=2**63)

    @model_validator(mode="after")
    def validate_configuration(self) -> "GARunRequest":
        GAConfig(**self.model_dump(exclude={"seed", "repetitions"})).validate()
        return self


class GAExperimentRequest(GARunRequest):
    repetitions: int = Field(10, ge=1, le=100)


def _config(request: GARunRequest) -> GAConfig:
    return GAConfig(**request.model_dump(exclude={"seed", "repetitions"}))


@router.post("/run", status_code=201)
def run_genetic_algorithm(request: GARunRequest, session: Session = Depends(get_db)) -> dict[str, Any]:
    actual_seed, _ = create_random_generator(request.seed)
    config = _config(request)
    result = run(config, actual_seed)
    record = create_run(session, project_key="p3", seed=actual_seed, algorithm_version="p3-pygad-1.0",
                        parameters=config.__dict__, result_data=result.as_dict())
    return {"run_id": record.id, "seed": actual_seed, "seed_exact": str(actual_seed), "result": result.as_dict()}


@router.post("/experiment", status_code=201)
def run_experiment(request: GAExperimentRequest, session: Session = Depends(get_db)) -> dict[str, Any]:
    actual_seed, generator = create_random_generator(request.seed)
    config = _config(request)
    runs = []
    for index in range(request.repetitions):
        seed = generator.randrange(2**63)
        result = run(config, seed)
        record = create_run(session, project_key="p3", seed=seed, algorithm_version="p3-pygad-1.0",
                            parameters={**config.__dict__, "experiment": {"id": str(uuid4()), "index": index}}, result_data=result.as_dict())
        runs.append({"run_id": record.id, "seed": seed, "result": result.as_dict()})
    objectives = [x["result"]["best_objective"] for x in runs]
    return {"seed": actual_seed, "seed_exact": str(actual_seed), "repetitions": request.repetitions,
            "configuration": config.__dict__, "runs": runs,
            "summary": {"average_objective": sum(objectives) / len(objectives),
                        "best_objective": min(objectives) if config.objective == "minimize" else max(objectives),
                        "worst_objective": max(objectives) if config.objective == "minimize" else min(objectives)}}
