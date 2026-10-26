"""Projekt 3: optymalizacja funkcji kwadratowej za pomocą PyGAD."""
from __future__ import annotations

import random
import time
from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np
import pygad
import benchmark_functions as bf
from opfunu import cec_based
from opfunu.name_based.a_func import Ackley01

Representation = Literal["binary", "real"]
Objective = Literal["minimize", "maximize"]


@dataclass(frozen=True)
class GAConfig:
    function_key: str = "quadratic"
    representation: Representation = "binary"
    dimensions: int = 2
    num_genes: int = 60
    lower_bound: float = 0.0
    upper_bound: float = 1.0
    num_generations: int = 100
    sol_per_pop: int = 40
    num_parents_mating: int = 20
    mutation_num_genes: int = 2
    parent_selection_type: Literal["tournament", "rws", "random"] = "tournament"
    crossover_type: str = "single_point"
    mutation_type: Literal["random", "swap", "gaussian"] = "random"
    mutation_probability: float = 0.02
    crossover_probability: float = 0.8
    keep_elitism: int = 1
    tournament_size: int = 3
    objective: Objective = "minimize"

    def validate(self) -> None:
        if self.representation not in {"binary", "real"}:
            raise ValueError("Reprezentacja musi być binarna albo rzeczywista.")
        if self.dimensions < 1 or self.num_genes < self.dimensions:
            raise ValueError("Liczba genów musi być nie mniejsza od liczby zmiennych.")
        if self.representation == "binary" and self.num_genes % self.dimensions:
            raise ValueError("Dla reprezentacji binarnej num_genes musi dzielić się przez dimensions.")
        if self.lower_bound >= self.upper_bound:
            raise ValueError("Dolna granica musi być mniejsza od górnej.")
        if self.sol_per_pop < 2 or not 2 <= self.num_parents_mating <= self.sol_per_pop:
            raise ValueError("Nieprawidłowy rozmiar populacji lub liczba rodziców.")
        if self.num_generations < 1 or not 0 <= self.mutation_probability <= 1 or not 0 <= self.crossover_probability <= 1:
            raise ValueError("Nieprawidłowa liczba pokoleń albo prawdopodobieństwo.")
        if self.mutation_num_genes < 1 or self.tournament_size < 2:
            raise ValueError("Parametry mutacji i turnieju muszą być dodatnie.")
        if self.parent_selection_type not in {"tournament", "rws", "random"}:
            raise ValueError("Nieznana selekcja.")
        if self.crossover_type not in {"single_point", "two_points", "uniform", "arithmetic", "blend_alpha", "blend_alpha_beta", "average"}:
            raise ValueError("Nieznane krzyżowanie.")
        if self.mutation_type not in {"random", "swap", "gaussian"}:
            raise ValueError("Nieznana mutacja.")
        if self.function_key not in {"quadratic", "hyperellipsoid", "ackley01", "cec2014_f3"}:
            raise ValueError("Nieznana funkcja benchmarkowa.")

    @property
    def bits_per_variable(self) -> int:
        return self.num_genes // self.dimensions


@dataclass(frozen=True)
class GenerationStats:
    epoch: int
    best: float
    worst: float
    mean: float
    standard_deviation: float


@dataclass(frozen=True)
class GARunResult:
    best_values: tuple[float, ...]
    best_objective: float
    elapsed_seconds: float
    history: tuple[GenerationStats, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"best_values": list(self.best_values), "best_objective": self.best_objective,
                "elapsed_seconds": self.elapsed_seconds, "history": [asdict(x) for x in self.history]}


def decodeInd(individual: Any, dimensions: int = 2) -> list[float]:
    """Dzieli chromosom na bloki bitów i dekoduje każdy blok do [0, 1]."""
    genes = np.asarray(individual).astype(int).tolist()
    if dimensions < 1 or len(genes) % dimensions:
        raise ValueError("Chromosom musi składać się z równych bloków bitów.")
    width = len(genes) // dimensions
    maximum = (1 << width) - 1
    return [sum(bit << (width - index - 1) for index, bit in enumerate(genes[start:start + width])) / maximum
            if maximum else 0.0 for start in range(0, len(genes), width)]


def objective_function(values: Any, function_key: str = "quadratic") -> float:
    """Funkcja z treści zadania; dodatkowe zmienne są karane kwadratem."""
    values = np.asarray([float(value) for value in values])
    if function_key == "hyperellipsoid":
        function = bf.Hyperellipsoid(n_dimensions=len(values))
        return float(function(values))
    if function_key == "ackley01":
        return float(Ackley01(ndim=len(values)).evaluate(values))
    if function_key == "cec2014_f3":
        return float(cec_based.cec2014.F32014(ndim=len(values)).evaluate(values))
    values = values.tolist()
    if len(values) == 1:
        return (values[0] - 1.0) ** 2
    result = (values[0] + 2 * values[1] - 7) ** 2 + (2 * values[0] + values[1] - 5) ** 2
    return result + sum(value * value for value in values[2:])


def fitnessFunction(individual: Any, dimensions: int = 2, function_key: str = "quadratic") -> tuple[float]:
    """Wersja funkcji celu zgodna z poleceniem (zwraca krotkę)."""
    return (objective_function(decodeInd(individual, dimensions), function_key),)


def _real_crossover(parents: np.ndarray, offspring_size: tuple[int, int], ga_instance: Any) -> np.ndarray:
    offspring = []
    for index in range(offspring_size[0]):
        first = parents[index % len(parents)].copy()
        second = parents[(index + 1) % len(parents)]
        kind = getattr(ga_instance, "p3_crossover_type", "single_point")
        if kind == "single_point":
            point = np.random.randint(0, offspring_size[1])
            child = first
            child[point:] = second[point:]
        elif kind == "two_points":
            points = sorted(np.random.choice(offspring_size[1], size=2, replace=False)) if offspring_size[1] > 1 else [0, 0]
            child = first
            child[points[0]:points[1]] = second[points[0]:points[1]]
        elif kind == "uniform":
            child = np.where(np.random.random(offspring_size[1]) < 0.5, first, second)
        elif kind == "arithmetic":
            alpha = 0.5
            child = alpha * first + (1 - alpha) * second
        elif kind == "blend_alpha":
            low, high = np.minimum(first, second), np.maximum(first, second)
            width = high - low
            child = np.random.uniform(low - 0.5 * width, high + 0.5 * width)
        elif kind == "blend_alpha_beta":
            distance = np.abs(first - second)
            child = np.random.uniform(np.minimum(first, second) - 0.5 * distance,
                                      np.maximum(first, second) + 0.25 * distance)
        else:
            child = (first + second) / 2
        offspring.append(np.clip(child, ga_instance.p3_lower_bound, ga_instance.p3_upper_bound))
    return np.asarray(offspring, dtype=float)


def _gaussian_mutation(offspring: np.ndarray, ga_instance: Any) -> np.ndarray:
    sigma = float(getattr(ga_instance, "p3_gaussian_sigma", 0.1))
    low = float(getattr(ga_instance, "p3_lower_bound", 0.0))
    high = float(getattr(ga_instance, "p3_upper_bound", 1.0))
    return np.clip(offspring + np.random.normal(0, sigma, offspring.shape), low, high)


def run(config: GAConfig, seed: int | None = None) -> GARunResult:
    config.validate()
    actual_seed = random.SystemRandom().randrange(2**63) if seed is None else seed
    # PyGAD accepts random_seed values in the unsigned 32-bit range.
    # The public API allows larger Python integers, so normalize once for
    # both NumPy and PyGAD instead of passing an invalid 64-bit seed through.
    actual_seed = actual_seed % (2**32)
    np.random.seed(actual_seed)
    history: list[GenerationStats] = []
    started = time.perf_counter()

    def fitness(_ga: Any, solution: np.ndarray, _index: int) -> float:
        values = solution.tolist() if config.representation == "real" else decodeInd(solution, config.dimensions)
        score = objective_function(values, config.function_key)
        return 1.0 / (1.0 + score) if config.objective == "minimize" else score

    def on_generation(ga: Any) -> None:
        objectives = [objective_function(s.tolist() if config.representation == "real" else decodeInd(s, config.dimensions), config.function_key) for s in ga.population]
        history.append(GenerationStats(ga.generations_completed, min(objectives), max(objectives), float(np.mean(objectives)), float(np.std(objectives))))

    kwargs: dict[str, Any] = dict(num_generations=config.num_generations, sol_per_pop=config.sol_per_pop,
        num_parents_mating=config.num_parents_mating, num_genes=config.num_genes, fitness_func=fitness,
        parent_selection_type=config.parent_selection_type, K_tournament=config.tournament_size,
        crossover_probability=config.crossover_probability, mutation_type=config.mutation_type,
        mutation_probability=config.mutation_probability, mutation_num_genes=config.mutation_num_genes,
        keep_elitism=config.keep_elitism, on_generation=on_generation, random_seed=actual_seed)
    if config.mutation_type == "gaussian":
        kwargs["mutation_type"] = _gaussian_mutation
    if config.representation == "binary":
        kwargs.update(init_range_low=0, init_range_high=2, gene_type=int, gene_space=[0, 1],
                      crossover_type=config.crossover_type,
                      mutation_by_replacement=config.mutation_type == "random")
    else:
        kwargs.update(init_range_low=config.lower_bound, init_range_high=config.upper_bound, gene_type=float,
                      crossover_type=_real_crossover, random_mutation_min_val=config.lower_bound,
                      random_mutation_max_val=config.upper_bound,
                      mutation_by_replacement=config.mutation_type == "random")
    ga = pygad.GA(**kwargs)
    ga.p3_crossover_type = config.crossover_type
    ga.p3_gaussian_sigma = (config.upper_bound - config.lower_bound) * 0.1
    ga.p3_lower_bound, ga.p3_upper_bound = config.lower_bound, config.upper_bound
    ga.run()
    solution, _fitness, _index = ga.best_solution()
    values = solution.tolist() if config.representation == "real" else decodeInd(solution, config.dimensions)
    return GARunResult(tuple(float(value) for value in values), objective_function(values, config.function_key),
                       time.perf_counter() - started, tuple(history))
