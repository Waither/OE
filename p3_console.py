"""Konsolowy launcher Projektu 3.

Przykłady:
    python p3_console.py --representation binary --function quadratic
    python p3_console.py --experiment --output sprawozdanie_p3/results.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from backend.projects.p3.logic import GAConfig, run


def main() -> None:
    parser = argparse.ArgumentParser(description="Eksperymenty PyGAD — Projekt 3")
    parser.add_argument("--function", dest="function_key", choices=["quadratic", "hyperellipsoid", "ackley01", "cec2014_f3"], default="quadratic")
    parser.add_argument("--representation", choices=["binary", "real"], default="binary")
    parser.add_argument("--dimensions", type=int, default=2)
    parser.add_argument("--genes", type=int, default=60)
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--population", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--experiment", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("sprawozdanie_p3/results.json"))
    args = parser.parse_args()

    configurations = []
    selections = ["tournament", "rws", "random"] if args.experiment else ["tournament"]
    crossovers = ["single_point", "two_points", "uniform"] if args.experiment else ["single_point"]
    mutations = (["random", "swap", "gaussian"] if args.representation == "real" else ["random", "swap"]) if args.experiment else ["random"]
    for selection in selections:
        for crossover in crossovers:
            for mutation in mutations:
                config = GAConfig(function_key=args.function_key, representation=args.representation,
                                  dimensions=args.dimensions, num_genes=args.genes,
                                  num_generations=args.generations, sol_per_pop=args.population,
                                  num_parents_mating=max(2, args.population // 2),
                                  parent_selection_type=selection, crossover_type=crossover,
                                  mutation_type=mutation)
                result = run(config, seed=args.seed + len(configurations))
                configurations.append({"configuration": asdict(config), "result": result.as_dict()})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(configurations, indent=2), encoding="utf-8")
    best = min(configurations, key=lambda item: item["result"]["best_objective"])
    print(f"Zapisano {len(configurations)} wyników do {args.output}")
    print(f"Najlepsza wartość funkcji: {best['result']['best_objective']:.6f}")


if __name__ == "__main__":
    main()
