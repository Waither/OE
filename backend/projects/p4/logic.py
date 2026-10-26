"""Projekt 4 — Artificial Bee Colony (ABC) z biblioteki MealPy."""
from __future__ import annotations

import random
import time
from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np
from mealpy.swarm_based import ABC
from mealpy import FloatVar
from opfunu import cec_based
from opfunu.cec_based.cec2014 import F12014
from opfunu.name_based.a_func import Ackley01
import benchmark_functions as bf


@dataclass(frozen=True)
class BenchmarkDefinition:
    key: str
    name: str
    dimensions: tuple[int, ...]
    lower: float
    upper: float
    optimum: float


BENCHMARKS = {
    "quadratic": BenchmarkDefinition("quadratic", "Funkcja kwadratowa", (2,), 0.0, 1.0, 20.0),
    "ackley01": BenchmarkDefinition("ackley01", "Ackley 01", tuple(range(2, 31)), -35.0, 35.0, 0.0),
    "hyperellipsoid": BenchmarkDefinition("hyperellipsoid", "Hyperellipsoid", tuple(range(2, 31)), -65.536, 65.536, 0.0),
    "cec2014_f3": BenchmarkDefinition("cec2014_f3", "CEC 2014 F3", (10, 20, 30, 50, 100), -100.0, 100.0, 300.0),
    "cec2014_f1": BenchmarkDefinition("cec2014_f1", "CEC 2014 F1", (10, 20, 30, 50, 100), -100.0, 100.0, 100.0),
}


@dataclass(frozen=True)
class ABCConfig:
    function_key: str = "ackley01"
    dimensions: int = 5
    population_size: int = 40
    epochs: int = 100
    n_limits: int = 25
    objective: Literal["min", "max"] = "min"

    def validate(self) -> None:
        if self.function_key not in BENCHMARKS:
            raise ValueError(f"Nieznana funkcja: {self.function_key}.")
        definition = BENCHMARKS[self.function_key]
        if self.dimensions not in definition.dimensions:
            raise ValueError(f"Funkcja {self.function_key} nie obsługuje wymiaru {self.dimensions}.")
        if self.population_size < 5 or self.epochs < 1 or self.n_limits < 1:
            raise ValueError("Populacja, liczba epok i limit prób muszą być dodatnie.")


@dataclass(frozen=True)
class GenerationStats:
    epoch: int
    best: float
    worst: float
    mean: float
    standard_deviation: float


@dataclass(frozen=True)
class ABCResult:
    best_values: tuple[float, ...]
    best_objective: float
    elapsed_seconds: float
    history: tuple[GenerationStats, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"best_values": list(self.best_values), "best_objective": self.best_objective,
                "elapsed_seconds": self.elapsed_seconds, "history": [asdict(item) for item in self.history]}


def objective_function(values: Any, function_key: str = "quadratic") -> float:
    values = np.asarray(values, dtype=float)
    if function_key == "quadratic":
        return float((values[0] + 2 * values[1] - 7) ** 2 + (2 * values[0] + values[1] - 5) ** 2)
    if function_key == "ackley01":
        return float(Ackley01(ndim=len(values)).evaluate(values))
    if function_key == "hyperellipsoid":
        return float(bf.Hyperellipsoid(n_dimensions=len(values))(values))
    if function_key == "cec2014_f3":
        return float(cec_based.cec2014.F32014(ndim=len(values)).evaluate(values))
    if function_key == "cec2014_f1":
        return float(F12014(ndim=len(values)).evaluate(values))
    raise ValueError(f"Nieznana funkcja: {function_key}.")


def run(config: ABCConfig, seed: int | None = None) -> ABCResult:
    config.validate()
    definition = BENCHMARKS[config.function_key]
    actual_seed = random.SystemRandom().randrange(2**63) if seed is None else seed
    history: list[GenerationStats] = []

    def objective(solution: np.ndarray) -> float:
        return objective_function(solution, config.function_key)

    problem = {
        "bounds": [FloatVar(lb=[definition.lower] * config.dimensions, ub=[definition.upper] * config.dimensions, name="x")],
        "minmax": config.objective,
        "obj_func": objective,
        "name": definition.name,
    }
    started = time.perf_counter()
    model = ABC.OriginalABC(epoch=config.epochs, pop_size=config.population_size, n_limits=config.n_limits, log_to=None)
    best_agent = model.solve(problem, seed=actual_seed)
    for epoch, agent in enumerate(model.history.list_global_best, start=1):
        current = model.history.list_current_best[epoch - 1]
        scores = [float(current.target.fitness)]
        best = float(agent.target.fitness)
        history.append(GenerationStats(epoch, best, max(scores) if scores else best,
                                        float(np.mean(scores)) if scores else best,
                                        float(np.std(scores)) if scores else 0.0))
    values = tuple(float(value) for value in best_agent.solution)
    return ABCResult(values, objective_function(values, config.function_key), time.perf_counter() - started, tuple(history))


def available_benchmarks() -> list[dict[str, object]]:
    return [asdict(item) for item in BENCHMARKS.values()]
