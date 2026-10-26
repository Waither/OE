"""Uruchamia eksperymenty ABC, porównuje je z P2 i tworzy raport."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.projects.p4.logic import ABCConfig, run as run_abc
from backend.projects.p2.logic import GAConfig, GeneticAlgorithm

ROOT = Path(__file__).resolve().parent
CASES = [("ackley01", 5), ("hyperellipsoid", 5), ("cec2014_f3", 10)]


def main() -> None:
    rows = []
    histories = {}
    for function_key, dimensions in CASES:
        for algorithm in ("ABC", "GA"):
            for index in range(5):
                if algorithm == "ABC":
                    result = run_abc(ABCConfig(function_key=function_key, dimensions=dimensions, population_size=20, epochs=50, n_limits=15), 500 + index)
                    data = result.as_dict()
                else:
                    result = GeneticAlgorithm(GAConfig(function_key=function_key, dimensions=dimensions, population_size=20, epochs=50, crossover="blend_alpha", mutation="gaussian"), 500 + index).run()
                    data = result.as_dict()
                rows.append({"function": function_key, "dimensions": dimensions, "algorithm": algorithm,
                             "best_objective": data["best_objective"], "elapsed_seconds": data["elapsed_seconds"]})
                histories.setdefault((function_key, algorithm), []).append(data["history"])

    (ROOT / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with (ROOT / "results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    for function_key, _dimensions in CASES:
        plt.figure(figsize=(9, 5))
        for algorithm, color in (("ABC", "#198754"), ("GA", "#0d6efd")):
            histories_for_algorithm = histories[(function_key, algorithm)]
            best = [min(item[i]["best"] for item in histories_for_algorithm) for i in range(len(histories_for_algorithm[0]))]
            plt.plot(range(1, len(best) + 1), best, label=algorithm, color=color)
        plt.title(f"Zbieżność: {function_key}"); plt.xlabel("Epoka"); plt.ylabel("Najlepsza wartość funkcji")
        plt.legend(); plt.grid(alpha=.25); plt.tight_layout(); plt.savefig(ROOT / f"convergence_{function_key}.png", dpi=160); plt.close()

    with (ROOT / "SPRAWOZDANIE-P4.md").open("a", encoding="utf-8") as report:
        report.write("\n## Wyniki eksperymentalne\n\n")
        report.write("Eksperyment wykonano dla 5 powtórzeń, populacji 20 osobników i 50 epok. W ABC użyto `n_limits=15`, a w GA krzyżowania BLX-α i mutacji Gaussa.\n\n")
        report.write("| Funkcja | ABC — średni wynik | GA — średni wynik | ABC — czas [s] | GA — czas [s] |\n|---|---:|---:|---:|---:|\n")
        for function_key, _ in CASES:
            abc = [row for row in rows if row["function"] == function_key and row["algorithm"] == "ABC"]
            ga = [row for row in rows if row["function"] == function_key and row["algorithm"] == "GA"]
            avg = lambda values, key: sum(float(row[key]) for row in values) / len(values)
            report.write(f"| {function_key} | {avg(abc, 'best_objective'):.6f} | {avg(ga, 'best_objective'):.6f} | {avg(abc, 'elapsed_seconds'):.4f} | {avg(ga, 'elapsed_seconds'):.4f} |\n")
            report.write(f"\n![Zbieżność {function_key}](./convergence_{function_key}.png)\n\n")
        report.write("Dane źródłowe znajdują się w plikach [results.csv](./results.csv) i [results.json](./results.json).\n\n")
        report.write("## Wnioski\n\nABC wykorzystuje fazę pszczół pracujących, obserwujących i zwiadowczych. W porównaniu z GA nie używa krzyżowania ani mutacji chromosomów; nowe rozwiązania powstają przez lokalne przeszukiwanie sąsiedztwa źródeł pokarmu. Wybór algorytmu powinien uwzględniać nie tylko średnią wartość celu, ale także stabilność i czas obliczeń.\n")


if __name__ == "__main__":
    main()
