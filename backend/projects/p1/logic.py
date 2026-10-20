"""Klasyczny binarny algorytm genetyczny

Funkcje celu pochodza z biblioteki opfunu. Kod projektu odpowiada za
reprezentacje chromosomu i operatory algorytmu.
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass
from typing import Callable, Literal

import numpy as np
from opfunu.cec_based.cec2014 import F12014
from opfunu.name_based.a_func import Ackley01

Objective = Literal["minimize", "maximize"]
SelectionName = Literal["best", "worst", "roulette", "tournament"]
CrossoverName = Literal["one_point", "two_point", "uniform", "grain"]
MutationName = Literal["boundary", "one_point", "two_point"]
EliteMode = Literal["count", "percentage"]


@dataclass(frozen=True)
class BenchmarkDefinition:
    key: str
    name: str
    source: str
    dimensions: tuple[int, ...]
    minimum: float
    maximum: float
    optimum: float
    optimum_arguments: tuple[float, ...]
    factory: Callable[[int], object]

    def create(self, dimensions: int) -> object:
        if dimensions not in self.dimensions:
            raise ValueError(f"Funkcja {self.key} obsluguje wymiary: {', '.join(map(str, self.dimensions))}.")
            
        return self.factory(dimensions)


BENCHMARKS: dict[str, BenchmarkDefinition] = {
    "ackley01": BenchmarkDefinition(
        key="ackley01",
        name="Ackley 01",
        source="opfunu.name_based.a_func.Ackley01",
        dimensions=tuple(range(2, 31)),
        minimum=-35.0,
        maximum=35.0,
        optimum=0.0,
        optimum_arguments=(0.0,),
        factory=lambda dimensions: Ackley01(ndim=dimensions),
    ),
    "cec2014_f1": BenchmarkDefinition(
        key="cec2014_f1",
        name="CEC 2014 F1 (Rotated High Conditioned Elliptic)",
        source="opfunu.cec_based.cec2014.F12014",
        dimensions=(10, 20, 30, 50, 100),
        minimum=-100.0,
        maximum=100.0,
        optimum=100.0,
        optimum_arguments=(),
        factory=lambda dimensions: F12014(ndim=dimensions),
    ),
}


@dataclass(frozen=True)
class GAConfig:
    function_key: str = "ackley01"
    dimensions: int = 5
    precision: int = 8
    population_size: int = 40
    epochs: int = 100
    objective: Objective = "minimize"
    selection: SelectionName = "tournament"
    tournament_size: int = 3
    crossover: CrossoverName = "two_point"
    crossover_probability: float = 0.8
    mutation: MutationName = "one_point"
    mutation_probability: float = 0.02
    inversion_probability: float = 0.05
    elite_mode: EliteMode = "count"
    elite_value: float = 2
    elite_count: int = 2
    grain_probability: float = 0.5

    def validate(self) -> None:
        if self.function_key not in BENCHMARKS:
            raise ValueError(f"Nieznana funkcja celu: {self.function_key}.")
        
        definition = BENCHMARKS[self.function_key]
        
        if self.dimensions not in definition.dimensions:
            raise ValueError(
                f"Funkcja {self.function_key} nie obsluguje wymiaru {self.dimensions}."
            )
            
        if not 1 <= self.precision <= 24:
            raise ValueError("Liczba cyfr dokladnosci dziesietnej musi byc w zakresie 1-24.")
        
        if self.population_size < 2 or self.population_size % 2:
            raise ValueError("Populacja musi miec parzysty rozmiar co najmniej 2.")
        
        if self.epochs < 1:
            raise ValueError("Liczba epok musi byc dodatnia.")
        
        if self.objective not in ("minimize", "maximize"):
            raise ValueError(f"Nieznany cel optymalizacji: {self.objective}.")
        
        if self.selection not in ("best", "worst", "roulette", "tournament"):
            raise ValueError(f"Nieznana selekcja: {self.selection}.")
        
        if self.crossover not in ("one_point", "two_point", "uniform", "grain"):
            raise ValueError(f"Nieznane krzyzowanie: {self.crossover}.")
        
        if self.mutation not in ("boundary", "one_point", "two_point"):
            raise ValueError(f"Nieznana mutacja: {self.mutation}.")
        
        if self.elite_mode not in ("count", "percentage"):
            raise ValueError(f"Nieznany tryb elityzmu: {self.elite_mode}.")
        
        if self.selection == "tournament" and (
            self.tournament_size < 2 or self.tournament_size > self.population_size
        ):
            raise ValueError("Rozmiar turnieju musi byc od 2 do rozmiaru populacji.")
        for name, value in (
            ("prawdopodobienstwo krzyzowania", self.crossover_probability),
            ("prawdopodobienstwo mutacji", self.mutation_probability),
            ("prawdopodobienstwo inwersji", self.inversion_probability),
            ("prawdopodobienstwo ziarniste", self.grain_probability),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name.capitalize()} musi byc w zakresie 0-1.")
            
        if self.elite_mode == "count":
            if not 0 <= self.elite_value < self.population_size:
                raise ValueError("Liczba elit musi byc od 0 do rozmiaru populacji - 1.")
        elif not 0 <= self.elite_value < 100:
            raise ValueError("Procent elit musi byc w zakresie 0-100.")

    @property
    def effective_elite_count(self) -> int:
        if self.elite_mode == "percentage":
            return min(self.population_size - 1, round(self.population_size * self.elite_value / 100))
        
        return min(self.population_size - 1, max(0, round(self.elite_value)))


@dataclass
class Individual:
    genes: list[int]
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
        return {
            "best_values": list(self.best_values),
            "best_objective": self.best_objective,
            "elapsed_seconds": self.elapsed_seconds,
            "history": [asdict(item) for item in self.history],
        }


class BinaryChromosome:
    def __init__(self, dimensions: int, minimum: float, maximum: float, precision: int) -> None:
        if dimensions < 1 or minimum >= maximum or not 1 <= precision <= 24:
            raise ValueError("Nieprawidlowa konfiguracja chromosomu.")
        
        self.dimensions = dimensions
        self.minimum = minimum
        self.maximum = maximum
        self.precision = precision
        self.bits_per_gene = math.ceil(
            math.log2((maximum - minimum) * 10**precision + 1)
        )
        self.length = self.dimensions * self.bits_per_gene

    def encode(self, values: list[float] | tuple[float, ...]) -> list[int]:
        if len(values) != self.dimensions:
            raise ValueError("Liczba wartosci nie pasuje do liczby zmiennych.")
        
        genes: list[int] = []
        limit = (1 << self.bits_per_gene) - 1
        
        for value in values:
            if not self.minimum <= value <= self.maximum:
                raise ValueError("Wartosc wykracza poza dziedzine funkcji.")
            integer = round((value - self.minimum) / (self.maximum - self.minimum) * limit)
            genes.extend(int(bit) for bit in f"{integer:0{self.bits_per_gene}b}")
            
        return genes

    def decode(self, genes: list[int]) -> list[float]:
        if len(genes) != self.length or any(bit not in (0, 1) for bit in genes):
            raise ValueError("Nieprawidlowy chromosom binarny.")
        
        limit = (1 << self.bits_per_gene) - 1
        values = []
        
        for index in range(self.dimensions):
            start = index * self.bits_per_gene
            integer = int("".join(map(str, genes[start:start + self.bits_per_gene])), 2)
            values.append(self.minimum + (self.maximum - self.minimum) * integer / limit)
            
        return values

    def random_genes(self, rng: random.Random) -> list[int]:
        return [rng.randint(0, 1) for _ in range(self.length)]


def _rank(population: list[Individual], objective: Objective) -> list[Individual]:
    reverse = objective == "maximize"
    return sorted(population, key=lambda item: item.fitness or 0.0, reverse=reverse)


def select(population: list[Individual], config: GAConfig, rng: random.Random) -> Individual:
    ordered = _rank(population, config.objective)
    
    if config.selection == "best":
        return ordered[0].clone()
    
    if config.selection == "worst":
        return ordered[-1].clone()
    
    if config.selection == "tournament":
        contestants = rng.sample(population, config.tournament_size)
        return _rank(contestants, config.objective)[0].clone()
    
    if config.selection == "roulette":
        scores = [item.fitness or 0.0 for item in population]
        if config.objective == "minimize":
            scores = [max(scores) - score for score in scores]
        else:
            scores = [score - min(scores) for score in scores]
            
        total = sum(scores)
        if total <= 0:
            return rng.choice(population).clone()
        
        target = rng.random() * total
        
        for item, score in zip(population, scores):
            if target < score:
                return item.clone()
            target -= score
        return population[-1].clone()
    
    raise ValueError(f"Nieznana selekcja: {config.selection}.")


def crossover(first: list[int], second: list[int], config: GAConfig, rng: random.Random) -> tuple[list[int], list[int]]:
    if len(first) != len(second):
        raise ValueError("Chromosomy musza miec taka sama dlugosc.")
    
    if config.crossover == "two_point" and len(first) < 3:
        return first.copy(), second.copy()
    
    if rng.random() >= config.crossover_probability or len(first) < 2:
        return first.copy(), second.copy()
    
    if config.crossover == "one_point":
        point = rng.randrange(1, len(first))
        return first[:point] + second[point:], second[:point] + first[point:]
    
    if config.crossover == "two_point":
        left, right = sorted(rng.sample(range(1, len(first)), 2))
        return first[:left] + second[left:right] + first[right:], second[:left] + first[left:right] + second[right:]
    
    if config.crossover == "uniform":
        child_a, child_b = first.copy(), second.copy()
        for index in range(len(first)):
            if rng.random() < 0.5:
                child_a[index], child_b[index] = child_b[index], child_a[index]
        return child_a, child_b
    
    if config.crossover == "grain":
        child_a, child_b = first.copy(), second.copy()
        for index in range(len(first)):
            if rng.random() < config.grain_probability:
                child_a[index], child_b[index] = child_b[index], child_a[index]
        return child_a, child_b
    
    raise ValueError(f"Nieznane krzyzowanie: {config.crossover}.")


def mutate(genes: list[int], config: GAConfig, rng: random.Random) -> list[int]:
    result = genes.copy()
    
    if not result or rng.random() >= config.mutation_probability:
        return result
    
    if config.mutation == "boundary":
        result[0] ^= 1
        result[-1] ^= 1
    elif config.mutation == "one_point":
        result[rng.randrange(len(result))] ^= 1
    elif config.mutation == "two_point":
        for index in rng.sample(range(len(result)), min(2, len(result))):
            result[index] ^= 1
    else:
        raise ValueError(f"Nieznana mutacja: {config.mutation}.")
    
    return result


def invert(genes: list[int], probability: float, rng: random.Random) -> list[int]:
    if len(genes) < 2 or rng.random() >= probability:
        return genes.copy()
    
    left, right = sorted(rng.sample(range(len(genes)), 2))
    return genes[:left] + list(reversed(genes[left:right + 1])) + genes[right + 1:]


class GeneticAlgorithm:
    def __init__(self, config: GAConfig, seed: int | None = None) -> None:
        config.validate()
        self.config = config
        self.seed = random.SystemRandom().randrange(2**63) if seed is None else seed
        self.rng = random.Random(self.seed)
        definition = BENCHMARKS[config.function_key]
        self.benchmark = definition.create(config.dimensions)
        self.codec = BinaryChromosome(
            config.dimensions, definition.minimum, definition.maximum, config.precision
        )

    def _evaluate(self, population: list[Individual]) -> None:
        for individual in population:
            individual.values = self.codec.decode(individual.genes)
            individual.fitness = float(self.benchmark.evaluate(np.asarray(individual.values)))

    def _stats(self, epoch: int, population: list[Individual]) -> GenerationStats:
        scores = [item.fitness for item in population if item.fitness is not None]
        best = max(scores) if self.config.objective == "maximize" else min(scores)
        worst = min(scores) if self.config.objective == "maximize" else max(scores)
        
        return GenerationStats(
            epoch,
            best,
            worst,
            sum(scores) / len(scores),
            float(np.std(scores)),
        )

    def run(self) -> GARunResult:
        import time

        started = time.perf_counter()
        population = [Individual(self.codec.random_genes(self.rng)) for _ in range(self.config.population_size)]
        history: list[GenerationStats] = []
        self._evaluate(population)
        
        for epoch in range(self.config.epochs):
            history.append(self._stats(epoch, population))
            ordered = _rank(population, self.config.objective)
            next_population = [
                item.clone()
                for item in ordered[:self.config.effective_elite_count]
            ]
            
            while len(next_population) < self.config.population_size:
                first = select(population, self.config, self.rng)
                second = select(population, self.config, self.rng)
                child_a, child_b = crossover(first.genes, second.genes, self.config, self.rng)
                next_population.append(Individual(invert(mutate(child_a, self.config, self.rng), self.config.inversion_probability, self.rng)))
                if len(next_population) < self.config.population_size:
                    next_population.append(Individual(invert(mutate(child_b, self.config, self.rng), self.config.inversion_probability, self.rng)))
            population = next_population
            self._evaluate(population)
            
        history.append(self._stats(self.config.epochs, population))
        best = _rank(population, self.config.objective)[0]
        return GARunResult(tuple(best.values or ()), float(best.fitness), time.perf_counter() - started, tuple(history))


def available_benchmarks() -> list[dict[str, object]]:
    return [
        {
            "key": definition.key,
            "name": definition.name,
            "source": definition.source,
            "dimensions": list(definition.dimensions),
            "minimum": definition.minimum,
            "maximum": definition.maximum,
            "optimum": definition.optimum,
            "optimum_arguments": {
                str(dimensions): (
                    list(definition.optimum_arguments) * dimensions
                    if definition.optimum_arguments
                    else [float(value) for value in definition.create(dimensions).x_global]
                )
                for dimensions in definition.dimensions
            },
        }
        for definition in BENCHMARKS.values()
    ]
