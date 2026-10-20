import csv
import io
import json
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.database import get_db
from backend.main import app
from backend.models import Base


class P1RouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.previous_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = self.override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        if self.previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = self.previous_override
        self.engine.dispose()

    def override_get_db(self):
        with Session(self.engine) as session:
            yield session

    @staticmethod
    def small_run_payload(**overrides):
        return {
            "function_key": "ackley01",
            "dimensions": 2,
            "precision": 1,
            "population_size": 2,
            "tournament_size": 2,
            "elite_value": 1,
            "epochs": 1,
            "crossover_probability": 0,
            "mutation_probability": 0,
            "inversion_probability": 0,
            "seed": 123,
            **overrides,
        }

    def test_benchmark_endpoint_exposes_supported_dimensions_and_optimum_metadata(self) -> None:
        response = self.client.get("/api/p1/benchmarks")

        self.assertEqual(response.status_code, 200)
        benchmarks = {item["key"]: item for item in response.json()}
        self.assertEqual(benchmarks["ackley01"]["dimensions"], list(range(2, 31)))
        self.assertEqual(benchmarks["ackley01"]["optimum"], 0)
        self.assertEqual(benchmarks["ackley01"]["optimum_arguments"]["2"], [0, 0])
        self.assertEqual(benchmarks["cec2014_f1"]["dimensions"], [10, 20, 30, 50, 100])
        self.assertEqual(
            len(benchmarks["cec2014_f1"]["optimum_arguments"]["10"]),
            10,
        )

    def test_single_run_is_persisted_with_seed_parameters_and_epoch_history(self) -> None:
        response = self.client.post("/api/p1/run", json=self.small_run_payload())

        self.assertEqual(response.status_code, 201, response.text)
        result = response.json()
        self.assertEqual(result["seed"], 123)
        self.assertEqual(result["seed_exact"], "123")
        self.assertEqual(len(result["result"]["history"]), 2)
        self.assertEqual(len(result["result"]["best_values"]), 2)

        stored = self.client.get(f"/api/runs/{result['run_id']}")
        self.assertEqual(stored.status_code, 200, stored.text)
        self.assertEqual(stored.json()["seed"], 123)
        self.assertEqual(stored.json()["algorithm_version"], "p1-ga-1.1")
        self.assertEqual(stored.json()["parameters"]["precision"], 1)
        self.assertEqual(stored.json()["result_data"], result["result"])

    def test_seed_exact_preserves_values_above_javascript_safe_integer_range(self) -> None:
        seed = 9_007_199_254_740_993
        response = self.client.post(
            "/api/p1/run",
            json=self.small_run_payload(seed=str(seed)),
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["seed_exact"], str(seed))

    def test_runs_for_both_benchmarks_are_saved_in_history_and_export_all_analysis_fields(self) -> None:
        for function_key, dimensions in (("ackley01", 2), ("cec2014_f1", 10)):
            with self.subTest(function_key=function_key):
                payload = self.small_run_payload(
                    function_key=function_key,
                    dimensions=dimensions,
                    seed=987654321,
                )
                single = self.client.post("/api/p1/run", json=payload)
                self.assertEqual(single.status_code, 201, single.text)
                single_data = single.json()

                experiment = self.client.post(
                    "/api/p1/experiment",
                    json={**payload, "repetitions": 10},
                )
                self.assertEqual(experiment.status_code, 201, experiment.text)
                experiment_data = experiment.json()
                self.assertEqual(len(experiment_data["runs"]), 10)

                history = self.client.get(
                    "/api/runs",
                    params={"project_key": "p1", "limit": 50},
                ).json()
                grouped_runs = [
                    item for item in history
                    if item["parameters"].get("experiment", {}).get("id")
                    == experiment_data["experiment_id"]
                ]
                self.assertEqual(len(grouped_runs), 10)
                self.assertTrue(all(item["seed_exact"] == str(item["seed"]) for item in grouped_runs))
                self.assertTrue(
                    all(
                        item["parameters"]["experiment"]["id"] == experiment_data["experiment_id"]
                        for item in grouped_runs
                    )
                )
                self.assertTrue(any(item["id"] == single_data["run_id"] for item in history))

                csv_response = self.client.get(
                    f"/api/runs/{single_data['run_id']}/export.csv"
                )
                self.assertEqual(csv_response.status_code, 200)
                rows = list(csv.DictReader(io.StringIO(csv_response.content.decode("utf-8-sig"))))
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertEqual(row["seed"], "987654321")
                self.assertEqual(row["best_objective"], str(single_data["result"]["best_objective"]))
                self.assertEqual(row["elapsed_seconds"], str(single_data["result"]["elapsed_seconds"]))
                self.assertEqual(len(json.loads(row["history"])), payload["epochs"] + 1)
                parameters = json.loads(row["parameters"])
                self.assertEqual(parameters["function_key"], function_key)
                self.assertEqual(parameters["dimensions"], dimensions)

                details = self.client.get(f"/api/runs/{single_data['run_id']}").json()
                self.assertEqual(details["seed_exact"], "987654321")
                self.assertEqual(details["result_data"], single_data["result"])

    def test_api_validation_error_is_explicit_and_rejects_invalid_configuration(self) -> None:
        response = self.client.post(
            "/api/p1/run",
            json=self.small_run_payload(precision=25),
        )

        self.assertEqual(response.status_code, 422)
        self.assertTrue(response.json()["detail"])

    def test_experiment_requires_ten_runs_and_persists_each_seeded_result(self) -> None:
        too_short = self.client.post(
            "/api/p1/experiment",
            json=self.small_run_payload(repetitions=9),
        )
        self.assertEqual(too_short.status_code, 422)

        response = self.client.post(
            "/api/p1/experiment",
            json=self.small_run_payload(repetitions=10),
        )

        self.assertEqual(response.status_code, 201, response.text)
        experiment = response.json()
        self.assertEqual(experiment["repetitions"], 10)
        self.assertTrue(experiment["experiment_id"])
        self.assertEqual(experiment["seed"], 123)
        self.assertEqual(experiment["seed_exact"], "123")
        self.assertEqual(experiment["configuration"]["function_key"], "ackley01")
        self.assertEqual(experiment["configuration"]["dimensions"], 2)
        self.assertEqual(experiment["configuration"]["precision"], 1)
        seeds = [run["seed"] for run in experiment["runs"]]
        self.assertEqual(len(set(seeds)), 10)
        self.assertEqual(len({run["run_id"] for run in experiment["runs"]}), 10)

        objectives = [run["result"]["best_objective"] for run in experiment["runs"]]
        durations = [run["result"]["elapsed_seconds"] for run in experiment["runs"]]
        summary = experiment["summary"]
        self.assertAlmostEqual(summary["average_objective"], sum(objectives) / 10)
        self.assertEqual(summary["best_objective"], min(objectives))
        self.assertEqual(summary["worst_objective"], max(objectives))
        self.assertAlmostEqual(summary["average_elapsed_seconds"], sum(durations) / 10)
        self.assertAlmostEqual(
            summary["average_error"],
            sum(abs(value) for value in objectives) / 10,
        )

        stored_runs = self.client.get("/api/runs", params={"project_key": "p1"}).json()
        self.assertEqual(len(stored_runs), 10)
        self.assertEqual({run["seed"] for run in stored_runs}, set(seeds))
        for run in stored_runs:
            metadata = run["parameters"]["experiment"]
            self.assertEqual(metadata["id"], experiment["experiment_id"])
            self.assertEqual(metadata["seed"], experiment["seed"])
            self.assertEqual(metadata["repetitions"], 10)
            self.assertIn(metadata["index"], range(10))

        replay = self.client.post(
            "/api/p1/experiment",
            json=self.small_run_payload(repetitions=10),
        ).json()
        self.assertNotEqual(replay["experiment_id"], experiment["experiment_id"])
        self.assertEqual(
            [run["seed"] for run in replay["runs"]],
            seeds,
        )
        self.assertEqual(
            [run["result"]["best_objective"] for run in replay["runs"]],
            objectives,
        )

    def test_maximization_experiment_uses_objective_aware_summary_order(self) -> None:
        response = self.client.post(
            "/api/p1/experiment",
            json=self.small_run_payload(repetitions=10, objective="maximize"),
        )

        self.assertEqual(response.status_code, 201, response.text)
        experiment = response.json()
        objectives = [run["result"]["best_objective"] for run in experiment["runs"]]
        self.assertEqual(experiment["summary"]["best_objective"], max(objectives))
        self.assertEqual(experiment["summary"]["worst_objective"], min(objectives))
        self.assertIsNone(experiment["summary"]["average_error"])

    def test_invalid_dimension_and_extra_request_fields_are_rejected(self) -> None:
        invalid_dimension = self.client.post(
            "/api/p1/run",
            json=self.small_run_payload(dimensions=1),
        )
        extra_field = self.client.post(
            "/api/p1/run",
            json=self.small_run_payload(unexpected=True),
        )

        self.assertEqual(invalid_dimension.status_code, 422)
        self.assertEqual(extra_field.status_code, 422)

if __name__ == "__main__":
    unittest.main()
