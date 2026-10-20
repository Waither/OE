import random
import math
import unittest

import numpy as np
from pydantic import ValidationError

from backend.projects.p1.logic import (
    BENCHMARKS,
    BinaryChromosome,
    GAConfig,
    GeneticAlgorithm,
    Individual,
    crossover,
    invert,
    mutate,
    select,
)
from backend.projects.p1.routes import GARunRequest


class ZeroRandom(random.Random):
    def random(self) -> float:
        return 0.0


class FixedSampleRandom(ZeroRandom):
    def sample(self, population, k):
        return [population[0], population[-1]][:k]


class DisabledOperatorTests(unittest.TestCase):
    def test_population_of_two_runs_with_valid_operator_limits(self) -> None:
        request = GARunRequest(
            population_size=2,
            tournament_size=2,
            elite_value=1,
            epochs=1,
            seed=42,
        )
        config = GAConfig(**request.model_dump(exclude={"seed"}))

        result = GeneticAlgorithm(config, seed=request.seed).run()

        self.assertEqual(len(result.history), 2)
        self.assertEqual(len(result.best_values), config.dimensions)

    def test_population_of_two_rejects_out_of_range_operator_defaults(self) -> None:
        with self.assertRaises(ValidationError):
            GARunRequest(population_size=2)

    def test_tournament_size_is_ignored_for_other_selection_methods(self) -> None:
        config = GAConfig(
            population_size=2,
            selection="best",
            tournament_size=3,
            elite_value=0,
        )

        config.validate()

    def test_zero_probability_disables_crossover_even_for_zero_random_value(self) -> None:
        first = [0, 0, 0, 0]
        second = [1, 1, 1, 1]
        config = GAConfig(crossover_probability=0)

        children = crossover(first, second, config, ZeroRandom())

        self.assertEqual(children, (first, second))

    def test_zero_probability_disables_mutation_even_for_zero_random_value(self) -> None:
        genes = [0, 1, 0, 1]
        config = GAConfig(mutation_probability=0)

        self.assertEqual(mutate(genes, config, ZeroRandom()), genes)

    def test_zero_probability_disables_inversion_even_for_zero_random_value(self) -> None:
        genes = [0, 0, 1, 1]

        self.assertEqual(invert(genes, 0, ZeroRandom()), genes)

    def test_inversion_leaves_single_gene_chromosomes_unchanged(self) -> None:
        genes = [1]

        inverted = invert(genes, 1, ZeroRandom())

        self.assertEqual(inverted, genes)
        self.assertIsNot(inverted, genes)


class ChromosomeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.codec = BinaryChromosome(dimensions=2, minimum=-1.0, maximum=1.0, precision=2)

    def test_encoding_uses_automatic_bit_length_and_decodes_boundaries(self) -> None:
        expected_bits_per_gene = math.ceil(math.log2(2 * 10**2 + 1))
        self.assertEqual(self.codec.bits_per_gene, expected_bits_per_gene)
        self.assertEqual(self.codec.length, expected_bits_per_gene * 2)

        encoded = self.codec.encode((-1.0, 1.0))

        self.assertEqual(self.codec.decode(encoded), [-1.0, 1.0])

    def test_encoding_and_decoding_approximate_intermediate_values(self) -> None:
        values = (-0.25, 0.375)

        decoded = self.codec.decode(self.codec.encode(values))

        self.assertLessEqual(abs(decoded[0] - values[0]), 2 / ((1 << self.codec.bits_per_gene) - 1))
        self.assertLessEqual(abs(decoded[1] - values[1]), 2 / ((1 << self.codec.bits_per_gene) - 1))

    def test_encoding_rejects_wrong_dimension_and_out_of_domain_values(self) -> None:
        with self.assertRaises(ValueError):
            self.codec.encode((0.0,))
        with self.assertRaises(ValueError):
            self.codec.encode((-1.01, 0.0))

    def test_decoding_rejects_wrong_length_and_nonbinary_values(self) -> None:
        with self.assertRaises(ValueError):
            self.codec.decode([0] * (self.codec.length - 1))
        with self.assertRaises(ValueError):
            self.codec.decode([0] * (self.codec.length - 1) + [2])

    def test_ackley_rejects_unsupported_one_dimension_and_exposes_known_optimum(self) -> None:
        definition = BENCHMARKS["ackley01"]
        self.assertNotIn(1, definition.dimensions)
        with self.assertRaises(ValueError):
            definition.create(1)

        benchmark = definition.create(2)
        self.assertAlmostEqual(float(benchmark.evaluate(np.zeros(2))), definition.optimum)
        self.assertEqual(definition.optimum_arguments * 2, (0.0, 0.0))

    def test_cec2014_metadata_arguments_reach_the_known_optimum(self) -> None:
        definition = BENCHMARKS["cec2014_f1"]
        for dimensions in definition.dimensions:
            with self.subTest(dimensions=dimensions):
                benchmark = definition.create(dimensions)
                self.assertAlmostEqual(
                    float(benchmark.evaluate(np.asarray(benchmark.x_global))),
                    definition.optimum,
                )


class OperatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.population = [
            Individual([0, 0, 0], fitness=1.0),
            Individual([0, 1, 0], fitness=2.0),
            Individual([1, 1, 1], fitness=3.0),
        ]

    def test_best_and_worst_selection_respect_both_objectives(self) -> None:
        for objective, best_fitness, worst_fitness in (
            ("minimize", 1.0, 3.0),
            ("maximize", 3.0, 1.0),
        ):
            best = select(
                self.population,
                GAConfig(selection="best", objective=objective),
                random.Random(42),
            )
            worst = select(
                self.population,
                GAConfig(selection="worst", objective=objective),
                random.Random(42),
            )
            self.assertEqual(best.fitness, best_fitness)
            self.assertEqual(worst.fitness, worst_fitness)

    def test_tournament_and_roulette_select_members_of_the_population(self) -> None:
        for selection in ("tournament", "roulette"):
            selected = select(
                self.population,
                GAConfig(selection=selection, tournament_size=2),
                random.Random(42),
            )
            self.assertIn(selected.fitness, (1.0, 2.0, 3.0))
            self.assertIsNot(selected, next(item for item in self.population if item.fitness == selected.fitness))

    def test_tournament_and_roulette_select_correctly_for_both_objectives(self) -> None:
        for objective, best_fitness, zero_target_roulette_fitness in (
            ("minimize", 1.0, 1.0),
            ("maximize", 3.0, 2.0),
        ):
            tournament = select(
                self.population,
                GAConfig(
                    selection="tournament",
                    objective=objective,
                    tournament_size=len(self.population),
                ),
                random.Random(42),
            )
            roulette = select(
                self.population,
                GAConfig(selection="roulette", objective=objective),
                ZeroRandom(),
            )

            self.assertEqual(tournament.fitness, best_fitness)
            self.assertEqual(roulette.fitness, zero_target_roulette_fitness)

    def test_roulette_handles_equal_fitness_values(self) -> None:
        population = [Individual([0], fitness=2.0), Individual([1], fitness=2.0)]

        selected = select(
            population,
            GAConfig(selection="roulette"),
            random.Random(42),
        )

        self.assertIn(selected.genes, ([0], [1]))

    def test_all_crossover_methods_preserve_chromosome_length(self) -> None:
        first = [0, 0, 0, 0, 0]
        second = [1, 1, 1, 1, 1]
        for method in ("one_point", "two_point", "uniform", "grain"):
            config = GAConfig(
                crossover=method,
                crossover_probability=1,
                grain_probability=1,
            )
            children = crossover(first, second, config, random.Random(42))
            self.assertEqual(tuple(map(len, children)), (len(first), len(second)))
            self.assertEqual(sorted(children[0] + children[1]), sorted(first + second))

    def test_two_point_crossover_is_a_noop_when_no_two_cut_points_exist(self) -> None:
        first, second = [0, 1], [1, 0]

        children = crossover(
            first,
            second,
            GAConfig(crossover="two_point", crossover_probability=1),
            random.Random(42),
        )

        self.assertEqual(children, (first, second))
        self.assertIsNot(children[0], first)
        self.assertIsNot(children[1], second)

    def test_all_mutation_methods_preserve_length_and_expected_flip_count(self) -> None:
        genes = [0, 0, 0, 0]
        expected_flips = {"boundary": 2, "one_point": 1, "two_point": 2}
        for method, flip_count in expected_flips.items():
            mutated = mutate(
                genes,
                GAConfig(mutation=method, mutation_probability=1),
                random.Random(42),
            )
            self.assertEqual(len(mutated), len(genes))
            self.assertEqual(sum(left != right for left, right in zip(genes, mutated)), flip_count)

    def test_two_point_mutation_handles_one_bit_chromosomes(self) -> None:
        mutated = mutate(
            [0],
            GAConfig(mutation="two_point", mutation_probability=1),
            random.Random(42),
        )
        self.assertEqual(mutated, [1])

    def test_inversion_reverses_a_segment_without_changing_length(self) -> None:
        genes = [0, 0, 0, 1, 1]

        inverted = invert(genes, 1, FixedSampleRandom())

        self.assertEqual(len(inverted), len(genes))
        self.assertCountEqual(inverted, genes)
        self.assertNotEqual(inverted, genes)


class AlgorithmBehaviorTests(unittest.TestCase):
    def test_generation_statistics_define_best_and_worst_for_objective(self) -> None:
        population = [
            Individual([0], fitness=1.0),
            Individual([1], fitness=3.0),
        ]
        for objective, best, worst in (
            ("minimize", 1.0, 3.0),
            ("maximize", 3.0, 1.0),
        ):
            algorithm = GeneticAlgorithm(
                GAConfig(objective=objective, elite_value=0),
                seed=1,
            )

            stats = algorithm._stats(0, population)

            self.assertEqual((stats.best, stats.worst), (best, worst))
            self.assertEqual(stats.mean, 2.0)
            self.assertEqual(stats.standard_deviation, 1.0)

    def test_elitism_keeps_best_value_from_regressing(self) -> None:
        for objective in ("minimize", "maximize"):
            result = GeneticAlgorithm(
                GAConfig(
                    dimensions=2,
                    precision=2,
                    population_size=10,
                    epochs=8,
                    objective=objective,
                    selection="tournament",
                    tournament_size=3,
                    elite_mode="count",
                    elite_value=1,
                ),
                seed=52,
            ).run()
            best_values = [epoch.best for epoch in result.history]
            if objective == "minimize":
                self.assertTrue(
                    all(current <= previous for previous, current in zip(best_values, best_values[1:]))
                )
            else:
                self.assertTrue(
                    all(current >= previous for previous, current in zip(best_values, best_values[1:]))
                )

    def test_elite_percentage_is_rounded_to_an_integer_count(self) -> None:
        config = GAConfig(
            population_size=10,
            elite_mode="percentage",
            elite_value=20,
        )

        self.assertEqual(config.effective_elite_count, 2)
        self.assertEqual(
            GAConfig(
                population_size=10,
                elite_mode="percentage",
                elite_value=0,
            ).effective_elite_count,
            0,
        )
        self.assertEqual(
            GAConfig(
                population_size=10,
                elite_mode="count",
                elite_value=0,
            ).effective_elite_count,
            0,
        )
        self.assertEqual(
            GAConfig(
                population_size=10,
                elite_mode="percentage",
                elite_value=26,
            ).effective_elite_count,
            3,
        )

    def test_same_seed_reproduces_solution_and_generation_history(self) -> None:
        config = GAConfig(dimensions=2, precision=2, population_size=10, epochs=5)

        first = GeneticAlgorithm(config, seed=123).run()
        second = GeneticAlgorithm(config, seed=123).run()

        self.assertEqual(first.best_values, second.best_values)
        self.assertEqual(first.best_objective, second.best_objective)
        self.assertEqual(first.history, second.history)

    def test_invalid_configuration_values_are_rejected(self) -> None:
        invalid_configs = (
            GAConfig(function_key="unknown"),
            GAConfig(dimensions=1),
            GAConfig(population_size=3),
            GAConfig(epochs=0),
            GAConfig(selection="invalid"),
            GAConfig(crossover="invalid"),
            GAConfig(mutation="invalid"),
            GAConfig(elite_mode="invalid"),
            GAConfig(crossover_probability=1.1),
            GAConfig(mutation_probability=-0.1),
        )
        for config in invalid_configs:
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    config.validate()

    def test_experiment_request_requires_at_least_ten_repetitions(self) -> None:
        from backend.projects.p1.routes import GAExperimentRequest

        with self.assertRaises(ValidationError):
            GAExperimentRequest(repetitions=9)
        self.assertEqual(GAExperimentRequest().repetitions, 10)

if __name__ == "__main__":
    unittest.main()