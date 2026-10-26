"""Konsolowy launcher Projektu 4 — Artificial Bee Colony z MealPy."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from backend.projects.p4.logic import ABCConfig, run


def main() -> None:
    parser = argparse.ArgumentParser(description="Projekt 4 — MealPy ABC")
    parser.add_argument("--function", choices=["quadratic", "ackley01", "hyperellipsoid", "cec2014_f3", "cec2014_f1"], default="ackley01")
    parser.add_argument("--dimensions", type=int, default=5)
    parser.add_argument("--population", type=int, default=40)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--limits", type=int, default=25)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("sprawozdanie_p4/results.json"))
    args = parser.parse_args()
    config = ABCConfig(function_key=args.function, dimensions=args.dimensions, population_size=args.population,
                       epochs=args.epochs, n_limits=args.limits)
    results = [run(config, args.seed + index).as_dict() for index in range(args.repetitions)]
    payload = {"algorithm": "Artificial Bee Colony (MealPy OriginalABC)", "configuration": asdict(config), "runs": results,
               "summary": {"average_objective": sum(x["best_objective"] for x in results) / len(results),
                           "best_objective": min(x["best_objective"] for x in results),
                           "average_elapsed_seconds": sum(x["elapsed_seconds"] for x in results) / len(results)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Zapisano wyniki do {args.output}")
    print(f"Najlepszy wynik: {payload['summary']['best_objective']:.6f}")


if __name__ == "__main__":
    main()
