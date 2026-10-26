import unittest

from backend.projects.p4.logic import ABCConfig, available_benchmarks, objective_function, run


class P4LogicTests(unittest.TestCase):
    def test_all_required_benchmarks_are_available(self) -> None:
        self.assertEqual({item["key"] for item in available_benchmarks()}, {"quadratic", "ackley01", "hyperellipsoid", "cec2014_f1", "cec2014_f3"})

    def test_quadratic_objective_has_expected_bounded_optimum(self) -> None:
        self.assertEqual(objective_function([1, 1], "quadratic"), 20.0)

    def test_abc_returns_reproducible_result(self) -> None:
        config = ABCConfig(function_key="ackley01", dimensions=3, population_size=8, epochs=2)
        first = run(config, seed=17)
        second = run(config, seed=17)
        self.assertEqual(first.best_values, second.best_values)
        self.assertEqual(first.best_objective, second.best_objective)
        self.assertEqual(len(first.history), 2)


if __name__ == "__main__":
    unittest.main()
