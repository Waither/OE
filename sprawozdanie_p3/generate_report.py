"""Generuje powtarzalne wyniki, CSV, wykresy i sekcję wynikową raportu P3."""
from __future__ import annotations

import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.projects.p3.logic import GAConfig, run

ROOT = Path(__file__).resolve().parent
SELECTIONS = ["tournament", "rws", "random"]
BINARY_CROSSOVERS = ["single_point", "two_points", "uniform"]
REAL_CROSSOVERS = ["single_point", "two_points", "uniform", "arithmetic", "blend_alpha", "blend_alpha_beta", "average"]


def execute(function_key: str, representation: str, dimensions: int, *, seed_offset: int = 0) -> list[dict[str, object]]:
    crossovers = BINARY_CROSSOVERS if representation == "binary" else REAL_CROSSOVERS
    mutations = ["random", "swap"] if representation == "binary" else ["random", "swap", "gaussian"]
    rows = []
    index = 0
    for selection in SELECTIONS:
        for crossover in crossovers:
            for mutation in mutations:
                config = GAConfig(function_key=function_key, representation=representation, dimensions=dimensions,
                                  num_genes=60 if representation == "binary" else dimensions,
                                  num_generations=25, sol_per_pop=20, num_parents_mating=10,
                                  parent_selection_type=selection, crossover_type=crossover, mutation_type=mutation)
                result = run(config, seed=1000 + seed_offset + index)
                rows.append({"function": function_key, "representation": representation,
                             "selection": selection, "crossover": crossover, "mutation": mutation,
                             "best_objective": result.best_objective, "elapsed_seconds": result.elapsed_seconds,
                             "history": [asdict(item) for item in result.history]})
                index += 1
    return rows


def main() -> None:
    rows = execute("quadratic", "binary", 2) + execute("quadratic", "real", 2, seed_offset=1000)
    smoke = [("hyperellipsoid", 5), ("ackley01", 5), ("cec2014_f3", 10)]
    for offset, (function_key, dimensions) in enumerate(smoke, 2000):
        for representation in ("binary", "real"):
            config = GAConfig(function_key=function_key, representation=representation, dimensions=dimensions,
                              num_genes=60 if representation == "binary" else dimensions,
                              num_generations=25, sol_per_pop=20, num_parents_mating=10,
                              parent_selection_type="tournament", crossover_type="single_point", mutation_type="random")
            result = run(config, seed=offset)
            rows.append({"function": function_key, "representation": representation, "selection": "tournament",
                         "crossover": "single_point", "mutation": "random", "best_objective": result.best_objective,
                         "elapsed_seconds": result.elapsed_seconds, "history": [asdict(item) for item in result.history]})

    (ROOT / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with (ROOT / "results.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["function", "representation", "selection", "crossover", "mutation", "best_objective", "elapsed_seconds"])
        writer.writeheader()
        writer.writerows([{key: row[key] for key in writer.fieldnames} for row in rows])

    comparison = [row for row in rows if row["function"] == "quadratic"]
    for representation in ("binary", "real"):
        plt.figure(figsize=(11, 6))
        selected = [row for row in comparison if row["representation"] == representation]
        for row in selected:
            history = row["history"]
            plt.plot([item["epoch"] for item in history], [item["best"] for item in history], alpha=.25)
        plt.title(f"Zbieżność — reprezentacja {representation}")
        plt.xlabel("Pokolenie")
        plt.ylabel("Najlepsza wartość funkcji")
        plt.grid(alpha=.25)
        plt.tight_layout()
        plt.savefig(ROOT / f"convergence_{representation}.png", dpi=160)
        plt.close()

    labels = [f"{row['representation']}:{row['selection']}" for row in comparison]
    values = [row["best_objective"] for row in comparison]
    plt.figure(figsize=(14, 6))
    plt.bar(range(len(values)), values)
    plt.xticks(range(len(values)), labels, rotation=75, fontsize=7)
    plt.ylabel("Najlepsza wartość funkcji")
    plt.title("Porównanie konfiguracji dla funkcji kwadratowej")
    plt.tight_layout()
    plt.savefig(ROOT / "comparison.png", dpi=160)
    plt.close()

    report = ROOT / "SPRAWOZDANIE-P3.md"
    with report.open("a", encoding="utf-8") as file:
        file.write("\n## Wyniki eksperymentów\n\n")
        file.write("Eksperyment główny wykonano dla 25 pokoleń, populacji 20 osobników i 10 rodziców. "
                   "Dla funkcji kwadratowej przetestowano wszystkie kombinacje operatorów wymagane w zadaniu.\n\n")
        file.write("| Reprezentacja | Liczba konfiguracji | Najlepszy wynik | Średni czas [s] |\n|---|---:|---:|---:|\n")
        for representation in ("binary", "real"):
            selected = [row for row in comparison if row["representation"] == representation]
            file.write(f"| {representation} | {len(selected)} | {min(row['best_objective'] for row in selected):.6f} | {sum(row['elapsed_seconds'] for row in selected) / len(selected):.4f} |\n")
        file.write("\nWykresy: [zbieżność binarna](./convergence_binary.png), [zbieżność rzeczywista](./convergence_real.png), [porównanie konfiguracji](./comparison.png).\n")
        file.write("\nPliki danych: [results.csv](./results.csv) i [results.json](./results.json).\n")
        file.write("\n## Wnioski\n\nWyniki są zależne od funkcji, operatorów i losowego seeda. Reprezentacja rzeczywista pozwala wykonywać operacje BLX oraz Gaussa bez dekodowania bitów, natomiast binarna daje kontrolę nad precyzją przez liczbę bitów przypadających na zmienną.\n")


if __name__ == "__main__":
    main()
