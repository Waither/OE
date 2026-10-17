import csv
import io
import unittest

from backend.common.csv_export import create_csv
from backend.common.randomness import create_random_generator


class CommonHelpersTests(unittest.TestCase):
    def test_seeded_random_generators_reproduce_the_same_values(self) -> None:
        seed_a, random_a = create_random_generator(1234)
        seed_b, random_b = create_random_generator(1234)

        self.assertEqual(seed_a, seed_b)
        self.assertEqual(
            [random_a.random() for _ in range(5)],
            [random_b.random() for _ in range(5)],
        )

    def test_random_generator_returns_a_reusable_generated_seed(self) -> None:
        seed, generator = create_random_generator()

        self.assertGreaterEqual(seed, 0)
        self.assertLess(seed, 2**63)
        self.assertEqual(generator.random(), create_random_generator(seed)[1].random())

    def test_random_generator_rejects_out_of_range_seed(self) -> None:
        with self.assertRaises(ValueError):
            create_random_generator(2**63)

    def test_csv_infers_columns_and_encodes_nested_values(self) -> None:
        content = create_csv(
            [
                {"epoch": 1, "best": 2.5, "details": {"population": 10}},
                {"epoch": 2, "best": 3.0},
            ]
        )
        text = content.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))

        self.assertEqual(list(rows[0]), ["epoch", "best", "details"])
        self.assertEqual(rows[0]["details"], '{"population":10}')
        self.assertEqual(rows[1]["details"], "")

    def test_csv_can_create_header_for_empty_data(self) -> None:
        content = create_csv([], fieldnames=["epoch", "best"])

        self.assertEqual(content.decode("utf-8-sig"), "epoch,best\r\n")


if __name__ == "__main__":
    unittest.main()
