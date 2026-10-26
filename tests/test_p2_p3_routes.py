import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.main import app
from backend.models import Base


class P2P3RoutesTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)

        def override_get_db():
            with Session(self.engine) as session:
                yield session

        self.override_get_db = override_get_db
        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    @staticmethod
    def p2_payload():
        return {
            "function_key": "ackley01",
            "dimensions": 2,
            "precision": 1,
            "population_size": 6,
            "epochs": 1,
            "selection": "tournament",
            "tournament_size": 2,
            "crossover": "blend_alpha",
            "crossover_probability": 0.0,
            "mutation": "gaussian",
            "mutation_probability": 0.0,
            "inversion_probability": 0.0,
            "elite_mode": "count",
            "elite_value": 1,
            "grain_probability": 0.5,
            "alpha": 0.5,
            "beta": 0.25,
            "gaussian_sigma": 0.1,
            "seed": 123,
        }

    @staticmethod
    def p3_payload():
        return {
            "function_key": "ackley01",
            "dimensions": 2,
            "num_genes": 20,
            "num_generations": 1,
            "sol_per_pop": 6,
            "num_parents_mating": 3,
            "mutation_num_genes": 2,
            "parent_selection_type": "tournament",
            "crossover_type": "single_point",
            "mutation_type": "random",
            "tournament_size": 2,
            "crossover_probability": 0.0,
            "mutation_probability": 0.0,
            "keep_elitism": 1,
            "seed": 123,
        }

    def assert_history_record(self, run_id, project_key, algorithm_version):
        response = self.client.get(f"/api/runs/{run_id}")
        self.assertEqual(response.status_code, 200, response.text)
        record = response.json()
        self.assertEqual(record["project_key"], project_key)
        self.assertEqual(record["algorithm_version"], algorithm_version)
        self.assertIsNotNone(record["result_data"])

    def test_p2_run_is_persisted_in_history(self):
        response = self.client.post("/api/p2/run", json=self.p2_payload())
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertIsInstance(body["run_id"], str)
        self.assert_history_record(body["run_id"], "p2", "p2-ga-1.1")

    def test_p2_experiment_persists_each_run(self):
        payload = self.p2_payload()
        payload["repetitions"] = 10
        response = self.client.post("/api/p2/experiment", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        runs = response.json()["runs"]
        self.assertEqual(len(runs), 10)
        for run in runs:
            self.assert_history_record(run["run_id"], "p2", "p2-ga-1.1")

    def test_p3_run_is_persisted_in_history(self):
        response = self.client.post("/api/p3/run", json=self.p3_payload())
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertIsInstance(body["run_id"], str)
        self.assert_history_record(body["run_id"], "p3", "p3-pygad-1.0")

    def test_p3_experiment_is_validated_and_persists_each_run(self):
        payload = self.p3_payload()
        payload["repetitions"] = 2
        response = self.client.post("/api/p3/experiment", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        runs = response.json()["runs"]
        self.assertEqual(len(runs), 2)
        for run in runs:
            self.assert_history_record(run["run_id"], "p3", "p3-pygad-1.0")


if __name__ == "__main__":
    unittest.main()
