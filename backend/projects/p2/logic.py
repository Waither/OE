"""Algorytm genetyczny z rzeczywistą reprezentacją chromosomu (Projekt 2)."""
from __future__ import annotations

import random
import time
from dataclasses import asdict, dataclass
from typing import Callable, Literal

import numpy as np
import benchmark_functions as bf
from opfunu import cec_based
from opfunu.cec_based.cec2014 import F12014
from opfunu.name_based.a_func import Ackley01

Objective = Literal["minimize", "maximize"]
CrossoverName = Literal["arithmetic", "linear", "blend_alpha", "blend_alpha_beta", "average"]
MutationName = Literal["uniform", "gaussian"]


@dataclass(frozen=True)
class BenchmarkDefinition:
    key: str
    name: str
    source: str
    dimensions: tuple[int, ...]
    minimum: float
    maximum: float
    optimum: float
    factory: Callable[[int], object]

    def create(self, dimensions: int) -> object:
        if dimensions not in self.dimensions:
            raise ValueError(f"Funkcja {self.key} obsługuje wymiary: {self.dimensions}.")
        return self.factory(dimensions)


BENCHMARKS = {
    "ackley01": BenchmarkDefinition("ackley01", "Ackley 01", "opfunu.name_based.a_func.Ackley01", tuple(range(2, 31)), -35.0, 35.0, 0.0, lambda n: Ackley01(ndim=n)),
    "hyperellipsoid": BenchmarkDefinition("hyperellipsoid", "Hyperellipsoid", "benchmark_functions.Hyperellipsoid", tuple(range(2, 31)), -65.536, 65.536, 0.0, lambda n: bf.Hyperellipsoid(n_dimensions=n)),
    "cec2014_f1": BenchmarkDefinition("cec2014_f1", "CEC 2014 F1 (Rotated High Conditioned Elliptic)", "opfunu.cec_based.cec2014.F12014", (10, 20, 30, 50, 100), -100.0, 100.0, 100.0, lambda n: F12014(ndim=n)),
    "cec2014_f3": BenchmarkDefinition("cec2014_f3", "CEC 2014 F3", "opfunu.cec_based.cec2014.F32014", (10, 20, 30, 50, 100), -100.0, 100.0, 300.0, lambda n: cec_based.cec2014.F32014(ndim=n)),
}


@dataclass(frozen=True)
class GAConfig:
    function_key: str = "ackley01"
    dimensions: int = 5
    precision: int = 8
    population_size: int = 40
    epochs: int = 100
    objective: Objective = "minimize"
    selection: Literal["best", "worst", "roulette", "tournament"] = "tournament"
    tournament_size: int = 3
    crossover: CrossoverName = "blend_alpha"
    crossover_probability: float = 0.8
    mutation: MutationName = "gaussian"
    mutation_probability: float = 0.02
    inversion_probability: float = 0.0
    elite_mode: Literal["count", "percentage"] = "count"
    elite_value: float = 2
    grain_probability: float = 0.5
    alpha: float = 0.5
    beta: float = 0.25
    gaussian_sigma: float = 0.1

    def validate(self) -> None:
        if self.function_key not in BENCHMARKS:
            raise ValueError(f"Nieznana funkcja celu: {self.function_key}.")
        definition = BENCHMARKS[self.function_key]
        if self.dimensions not in definition.dimensions:
            raise ValueError(f"Funkcja {self.function_key} nie obsługuje wymiaru {self.dimensions}.")
        if self.population_size < 2 or self.population_size % 2:
            raise ValueError("Populacja musi mieć parzysty rozmiar co najmniej 2.")
        if self.epochs < 1:
            raise ValueError("Liczba epok musi być dodatnia.")
        if self.selection == "tournament" and not 2 <= self.tournament_size <= self.population_size:
            raise ValueError("Rozmiar turnieju musi być od 2 do rozmiaru populacji.")
        if self.crossover not in {"arithmetic", "linear", "blend_alpha", "blend_alpha_beta", "average"}:
            raise ValueError(f"Nieznane krzyżowanie: {self.crossover}.")
        if self.mutation not in {"uniform", "gaussian"}:
            raise ValueError(f"Nieznana mutacja: {self.mutation}.")
        if not 0 <= self.crossover_probability <= 1 or not 0 <= self.mutation_probability <= 1:
            raise ValueError("Prawdopodobieństwa muszą być w zakresie 0-1.")
        if self.alpha < 0 or self.beta < 0 or self.gaussian_sigma < 0:
            raise ValueError("Parametry alfa, beta i sigma nie mogą być ujemne.")
        if self.elite_mode == "count" and not 0 <= self.elite_value < self.population_size:
            raise ValueError("Liczba elit musi być mniejsza od rozmiaru populacji.")
        if self.elite_mode == "percentage" and not 0 <= self.elite_value < 100:
            raise ValueError("Procent elit musi być w zakresie 0-100.")

    @property
    def effective_elite_count(self) -> int:
        value = self.population_size * self.elite_value / 100 if self.elite_mode == "percentage" else self.elite_value
        return min(self.population_size - 1, max(0, round(value)))


@dataclass
class Individual:
    genes: list[float]
    values: list[float] | None = None
    fitness: float | None = None

    def clone(self) -> "Individual":
        return Individual(self.genes.copy(), None if self.values is None else self.values.copy(), self.fitness)


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

    def as_dict(self) -> dict[str, object]:
        return {"best_values": list(self.best_values), "best_objective": self.best_objective, "elapsed_seconds": self.elapsed_seconds, "history": [asdict(x) for x in self.history]}


class RealChromosome:
    def __init__(self, dimensions: int, minimum: float, maximum: float) -> None:
        if dimensions < 1 or minimum >= maximum:
            raise ValueError("Nieprawidłowa dziedzina chromosomu.")
        self.dimensions, self.minimum, self.maximum = dimensions, minimum, maximum

    def random_genes(self, rng: random.Random) -> list[float]:
        return [rng.uniform(self.minimum, self.maximum) for _ in range(self.dimensions)]

    def clip(self, genes: list[float]) -> list[float]:
        return [min(self.maximum, max(self.minimum, float(x))) for x in genes]


def _rank(population: list[Individual], objective: Objective) -> list[Individual]:
    return sorted(population, key=lambda x: x.fitness or 0.0, reverse=objective == "maximize")


def select(population: list[Individual], config: GAConfig, rng: random.Random) -> Individual:
    ordered = _rank(population, config.objective)
    if config.selection == "best": return ordered[0].clone()
    if config.selection == "worst": return ordered[-1].clone()
    if config.selection == "tournament": return _rank(rng.sample(population, config.tournament_size), config.objective)[0].clone()
    scores = [x.fitness or 0.0 for x in population]
    scores = [max(scores) - x for x in scores] if config.objective == "minimize" else [x - min(scores) for x in scores]
    total = sum(scores)
    if total <= 0: return rng.choice(population).clone()
    target = rng.random() * total
    for item, score in zip(population, scores):
        target -= score
        if target <= 0: return item.clone()
    return population[-1].clone()


def crossover(first: list[float], second: list[float], config: GAConfig, rng: random.Random, chromosome: RealChromosome) -> tuple[list[float], list[float]]:
    if rng.random() >= config.crossover_probability: return first.copy(), second.copy()
    a, b = np.asarray(first), np.asarray(second)
    if config.crossover == "arithmetic":
        child_a, child_b = config.alpha * a + (1 - config.alpha) * b, (1 - config.alpha) * a + config.alpha * b
    elif config.crossover == "linear":
        child_a, child_b = 0.5 * a + 0.5 * b, 1.5 * a - 0.5 * b
    elif config.crossover == "blend_alpha":
        low, high = np.minimum(a, b), np.maximum(a, b)
        width = high - low
        child_a = np.asarray([rng.uniform(float(lo - config.alpha * d), float(hi + config.alpha * d)) for lo, hi, d in zip(low, high, width)])
        child_b = np.asarray([rng.uniform(float(lo - config.alpha * d), float(hi + config.alpha * d)) for lo, hi, d in zip(low, high, width)])
    elif config.crossover == "blend_alpha_beta":
        child_a = np.asarray([rng.uniform(float(x - config.alpha * abs(x - y)), float(y + config.beta * abs(x - y))) for x, y in zip(a, b)])
        child_b = np.asarray([rng.uniform(float(y - config.alpha * abs(x - y)), float(x + config.beta * abs(x - y))) for x, y in zip(a, b)])
    else:
        child_a = child_b = (a + b) / 2
    return chromosome.clip(child_a.tolist()), chromosome.clip(child_b.tolist())


def mutate(genes: list[float], config: GAConfig, rng: random.Random, chromosome: RealChromosome) -> list[float]:
    result = genes.copy()
    if rng.random() >= config.mutation_probability: return result
    if config.mutation == "uniform":
        result[rng.randrange(len(result))] = rng.uniform(chromosome.minimum, chromosome.maximum)
    else:
        for index in range(len(result)):
            result[index] += rng.gauss(0, config.gaussian_sigma * (chromosome.maximum - chromosome.minimum))
    return chromosome.clip(result)


class GeneticAlgorithm:
    def __init__(self, config: GAConfig, seed: int | None = None) -> None:
        config.validate()
        self.config, self.seed = config, random.SystemRandom().randrange(2**63) if seed is None else seed
        self.rng = random.Random(self.seed)
        definition = BENCHMARKS[config.function_key]
        self.benchmark = definition.create(config.dimensions)
        self.chromosome = RealChromosome(config.dimensions, definition.minimum, definition.maximum)

    def _evaluate(self, population: list[Individual]) -> None:
        for individual in population:
            individual.values = self.chromosome.clip(individual.genes)
            evaluator = getattr(self.benchmark, "evaluate", self.benchmark)
            individual.fitness = float(evaluator(np.asarray(individual.values)))

    def _stats(self, epoch: int, population: list[Individual]) -> GenerationStats:
        scores = [x.fitness for x in population if x.fitness is not None]
        return GenerationStats(epoch, min(scores) if self.config.objective == "minimize" else max(scores), max(scores) if self.config.objective == "minimize" else min(scores), float(np.mean(scores)), float(np.std(scores)))

    def run(self) -> GARunResult:
        started = time.perf_counter()
        population = [Individual(self.chromosome.random_genes(self.rng)) for _ in range(self.config.population_size)]
        self._evaluate(population)
        history = []
        for epoch in range(self.config.epochs):
            history.append(self._stats(epoch, population))
            ordered = _rank(population, self.config.objective)
            next_population = [x.clone() for x in ordered[: self.config.effective_elite_count]]
            while len(next_population) < self.config.population_size:
                first, second = select(population, self.config, self.rng), select(population, self.config, self.rng)
                child_a, child_b = crossover(first.genes, second.genes, self.config, self.rng, self.chromosome)
                next_population.append(Individual(mutate(child_a, self.config, self.rng, self.chromosome)))
                if len(next_population) < self.config.population_size: next_population.append(Individual(mutate(child_b, self.config, self.rng, self.chromosome)))
            population = next_population
            self._evaluate(population)
        history.append(self._stats(self.config.epochs, population))
        best = _rank(population, self.config.objective)[0]
        return GARunResult(tuple(best.values or ()), float(best.fitness), time.perf_counter() - started, tuple(history))


def available_benchmarks() -> list[dict[str, object]]:
    return [{"key": x.key, "name": x.name, "source": x.source, "dimensions": list(x.dimensions), "minimum": x.minimum, "maximum": x.maximum, "optimum": x.optimum, "optimum_arguments": {str(n): [0.0] * n for n in x.dimensions}} for x in BENCHMARKS.values()]
