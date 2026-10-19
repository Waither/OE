import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.common.csv_export import create_run_csv_response
from backend.common.run_service import (
    create_run,
    delete_project_runs,
    get_chart_artifacts,
    get_chart_comparison_file,
    get_chart_file,
    get_run,
    list_chart_comparisons,
    save_chart_comparison,
    save_chart_png,
)
from backend.models import Base


class RunServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.temp_directory = tempfile.TemporaryDirectory()
        self.artifact_root = Path(self.temp_directory.name)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()
        self.temp_directory.cleanup()

    def test_run_is_persisted_and_exported_to_csv(self) -> None:
        run = create_run(
            self.session,
            project_key="p1",
            seed=42,
            algorithm_version="test",
            parameters={"population_size": 10},
            result_data=[{"epoch": 1, "best": 3.5}, {"epoch": 2, "best": 4.0}],
        )

        loaded_run = get_run(self.session, run.id)
        response = create_run_csv_response(loaded_run)

        self.assertEqual(loaded_run.parameters, {"population_size": 10})
        self.assertEqual(loaded_run.seed, 42)
        csv_rows = list(csv.DictReader(io.StringIO(bytes(response.body).decode("utf-8-sig"))))
        self.assertEqual(list(csv_rows[0])[:2], ["epoch", "best"])
        self.assertEqual(json.loads(csv_rows[0]["parameters"]), {"population_size": 10})
        self.assertIn("p1_", response.headers["content-disposition"])

    def test_png_is_persisted_and_listed_for_its_run(self) -> None:
        run = create_run(
            self.session,
            project_key="p2",
            seed=7,
            algorithm_version="test",
            parameters={},
            result_data={},
        )
        png_data = b"\x89PNG\r\n\x1a\nchart data"

        artifact = save_chart_png(
            self.session,
            run=run,
            name="Populacja",
            content=png_data,
            artifact_root=self.artifact_root,
        )
        stored_artifacts = get_chart_artifacts(self.session, run.id)
        stored_file = get_chart_file(artifact, self.artifact_root)

        self.assertEqual(len(stored_artifacts), 1)
        self.assertEqual(stored_artifacts[0].name, "Populacja")
        self.assertEqual(stored_file.read_bytes(), png_data)

    def test_png_rejects_non_png_content(self) -> None:
        run = create_run(
            self.session,
            project_key="p3",
            seed=7,
            algorithm_version="test",
            parameters={},
            result_data={},
        )

        with self.assertRaises(HTTPException):
            save_chart_png(
                self.session,
                run=run,
                name="Niepoprawny",
                content=b"not an image",
                artifact_root=self.artifact_root,
            )

    def test_delete_project_runs_removes_project_data_and_chart_files_only(self) -> None:
        p1_run = create_run(
            self.session,
            project_key="p1",
            seed=1,
            algorithm_version="test",
            parameters={},
            result_data={},
        )
        p2_run = create_run(
            self.session,
            project_key="p2",
            seed=2,
            algorithm_version="test",
            parameters={},
            result_data={},
        )
        png_data = b"\x89PNG\r\n\x1a\nchart data"
        p1_chart = save_chart_png(
            self.session,
            run=p1_run,
            name="P1",
            content=png_data,
            artifact_root=self.artifact_root,
        )
        p2_chart = save_chart_png(
            self.session,
            run=p2_run,
            name="P2",
            content=png_data,
            artifact_root=self.artifact_root,
        )
        p1_chart_path = get_chart_file(p1_chart, self.artifact_root)
        p2_chart_path = get_chart_file(p2_chart, self.artifact_root)
        p1_comparison = save_chart_comparison(
            self.session,
            project_key="p1",
            run_ids=[p1_run.id, create_run(
                self.session,
                project_key="p1",
                seed=3,
                algorithm_version="test",
                parameters={},
                result_data={},
            ).id],
            metric="best",
            content=png_data,
            artifact_root=self.artifact_root,
        )
        p1_comparison_path = get_chart_comparison_file(p1_comparison, self.artifact_root)

        deleted_count = delete_project_runs(
            self.session,
            project_key="p1",
            artifact_root=self.artifact_root,
        )

        self.assertEqual(deleted_count, 2)
        with self.assertRaises(HTTPException):
            get_run(self.session, p1_run.id)
        self.assertEqual(get_run(self.session, p2_run.id).id, p2_run.id)
        self.assertFalse(p1_chart_path.exists())
        self.assertTrue(p2_chart_path.exists())
        self.assertEqual(len(get_chart_artifacts(self.session, p2_run.id)), 1)
        self.assertFalse(p1_comparison_path.exists())
        self.assertEqual(list_chart_comparisons(self.session, project_key="p1"), [])
        self.assertEqual(len(list_chart_comparisons(self.session, project_key="p2")), 0)

    def test_chart_comparison_stores_run_ids_metric_and_png(self) -> None:
        first_run = create_run(
            self.session,
            project_key="p1",
            seed=1,
            algorithm_version="test",
            parameters={},
            result_data={},
        )
        second_run = create_run(
            self.session,
            project_key="p1",
            seed=2,
            algorithm_version="test",
            parameters={},
            result_data={},
        )
        png_data = b"\x89PNG\r\n\x1a\ncomparison"

        comparison = save_chart_comparison(
            self.session,
            project_key="p1",
            run_ids=[first_run.id, second_run.id],
            metric="mean",
            content=png_data,
            artifact_root=self.artifact_root,
        )
        stored = list_chart_comparisons(self.session, project_key="p1")

        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].run_ids, [first_run.id, second_run.id])
        self.assertEqual(stored[0].metric, "mean")
        self.assertEqual(get_chart_comparison_file(comparison, self.artifact_root).read_bytes(), png_data)

    def test_chart_comparison_rejects_runs_from_another_project(self) -> None:
        p1_run = create_run(
            self.session,
            project_key="p1",
            seed=1,
            algorithm_version="test",
            parameters={},
            result_data={},
        )
        p2_run = create_run(
            self.session,
            project_key="p2",
            seed=2,
            algorithm_version="test",
            parameters={},
            result_data={},
        )

        with self.assertRaises(HTTPException):
            save_chart_comparison(
                self.session,
                project_key="p1",
                run_ids=[p1_run.id, p2_run.id],
                metric="best",
                content=b"\x89PNG\r\n\x1a\ncomparison",
                artifact_root=self.artifact_root,
            )

    def test_delete_project_runs_rejects_unknown_project(self) -> None:
        with self.assertRaises(HTTPException):
            delete_project_runs(
                self.session,
                project_key="unknown",
                artifact_root=self.artifact_root,
            )


if __name__ == "__main__":
    unittest.main()
