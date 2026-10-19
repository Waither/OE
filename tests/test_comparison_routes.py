import unittest

from backend.main import app


class ComparisonRouteTests(unittest.TestCase):
    def test_comparison_endpoints_are_registered(self) -> None:
        paths = app.openapi()["paths"]

        self.assertIn("/api/runs/comparisons", paths)
        self.assertIn("get", paths["/api/runs/comparisons"])
        self.assertIn("post", paths["/api/runs/comparisons"])
        self.assertIn("/api/runs/comparisons/{comparison_id}/image", paths)
        self.assertIn("get", paths["/api/runs/comparisons/{comparison_id}/image"])


if __name__ == "__main__":
    unittest.main()
