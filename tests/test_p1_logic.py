import random
import unittest

from pydantic import ValidationError

from backend.projects.p1.logic import GAConfig, GeneticAlgorithm, crossover, invert, mutate
from backend.projects.p1.routes import GARunRequest


class ZeroRandom(random.Random):
    def random(self) -> float:
        return 0.0


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


if __name__ == "__main__":
    unittest.main()