import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.database import get_db
from backend.main import app
from backend.models import Base


class P4RouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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

    def payload(self, **overrides):
        return {"function_key": "ackley01", "dimensions": 2, "population_size": 6, "epochs": 1, "n_limits": 2, "seed": 123, **overrides}

    def test_benchmarks_are_exposed_in_polish_metadata(self) -> None:
        response = self.client.get("/api/p4/benchmarks")
        self.assertEqual(response.status_code, 200)
        self.assertIn("CEC 2014 F1", {item["name"] for item in response.json()})

    def test_run_is_persisted_and_returns_history(self) -> None:
        response = self.client.post("/api/p4/run", json=self.payload())
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertEqual(body["seed_exact"], "123")
        self.assertEqual(len(body["result"]["history"]), 1)
        stored = self.client.get(f"/api/runs/{body['run_id']}")
        self.assertEqual(stored.status_code, 200, stored.text)
        self.assertEqual(stored.json()["algorithm_version"], "p4-abc-mealpy-1.0")

    def test_invalid_dimension_returns_validation_error_not_server_error(self) -> None:
        response = self.client.post("/api/p4/run", json=self.payload(function_key="cec2014_f1", dimensions=5))
        self.assertEqual(response.status_code, 422, response.text)

    def test_experiment_returns_requested_number_of_runs(self) -> None:
        response = self.client.post("/api/p4/experiment", json=self.payload(repetitions=2))
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(len(response.json()["runs"]), 2)

    def test_all_supported_functions_have_working_run_endpoint(self) -> None:
        for function_key, dimensions in (("quadratic", 2), ("ackley01", 2), ("hyperellipsoid", 2), ("cec2014_f1", 10), ("cec2014_f3", 10)):
            with self.subTest(function_key=function_key):
                response = self.client.post("/api/p4/run", json=self.payload(function_key=function_key, dimensions=dimensions))
                self.assertEqual(response.status_code, 201, response.text)


if __name__ == "__main__":
    unittest.main()
