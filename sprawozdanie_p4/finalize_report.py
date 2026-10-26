"""Uzupełnia raport P4 o CEC2014 F1, konfiguracje ABC oraz porównanie z P1/P2."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.projects.p1.logic import GAConfig as P1Config, GeneticAlgorithm as P1GA
from backend.projects.p2.logic import GAConfig as P2Config, GeneticAlgorithm as P2GA
from backend.projects.p4.logic import ABCConfig, run as run_abc

ROOT = Path(__file__).resolve().parent


def one_run(algorithm: str, function: str, dimensions: int, seed: int) -> dict[str, float | str]:
    if algorithm == "ABC":
        result = run_abc(ABCConfig(function_key=function, dimensions=dimensions, population_size=20, epochs=50, n_limits=15), seed)
    elif algorithm == "P1":
        result = P1GA(P1Config(function_key=function, dimensions=dimensions, population_size=20, epochs=50, precision=8), seed).run()
    else:
        result = P2GA(P2Config(function_key=function, dimensions=dimensions, population_size=20, epochs=50, crossover="blend_alpha", mutation="gaussian"), seed).run()
    return {"algorithm": algorithm, "function": function, "best_objective": result.best_objective, "elapsed_seconds": result.elapsed_seconds}


def main() -> None:
    rows = []
    for function, dimensions, algorithms in (("ackley01", 5, ["ABC", "P1", "P2"]), ("cec2014_f1", 10, ["ABC", "P1"])):
        for algorithm in algorithms:
            for seed in range(700, 705):
                rows.append(one_run(algorithm, function, dimensions, seed))

    configurations = []
    for population, epochs, n_limits in ((20, 50, 10), (20, 50, 25), (40, 50, 15), (20, 100, 15)):
        values = []
        for seed in range(800, 803):
            result = run_abc(ABCConfig(function_key="ackley01", dimensions=5, population_size=population, epochs=epochs, n_limits=n_limits), seed)
            values.append(result.best_objective)
        configurations.append({"population": population, "epochs": epochs, "n_limits": n_limits,
                               "average_objective": sum(values) / len(values), "best_objective": min(values)})

    (ROOT / "supplement_results.json").write_text(json.dumps({"comparisons": rows, "configurations": configurations}, indent=2), encoding="utf-8")
    with (ROOT / "supplement_results.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

    labels = [f"{item['function']}\n{item['algorithm']}" for item in rows]
    values = [item["best_objective"] for item in rows]
    plt.figure(figsize=(12, 5)); plt.bar(range(len(values)), values); plt.xticks(range(len(values)), labels, rotation=75, fontsize=7)
    plt.ylabel("Najlepsza wartość funkcji"); plt.title("ABC kontra algorytmy genetyczne P1/P2"); plt.tight_layout()
    plt.savefig(ROOT / "comparison_p1_p2.png", dpi=160); plt.close()

    config_labels = [f"pop={x['population']}\nep={x['epochs']}\nlim={x['n_limits']}" for x in configurations]
    plt.figure(figsize=(8, 5)); plt.bar(range(len(configurations)), [x["average_objective"] for x in configurations]); plt.xticks(range(len(configurations)), config_labels)
    plt.ylabel("Średnia wartość funkcji"); plt.title("Wpływ konfiguracji ABC — Ackley"); plt.tight_layout()
    plt.savefig(ROOT / "configurations_abc.png", dpi=160); plt.close()

    with (ROOT / "SPRAWOZDANIE-P4.md").open("a", encoding="utf-8") as report:
        report.write("\n## Uzupełnienie eksperymentów\n\n")
        report.write("Dodano CEC2014 F1 oraz porównanie z algorytmami genetycznymi P1 i P2. Każdy wariant wykonano pięć razy.\n\n")
        report.write("![Porównanie ABC z P1 i P2](./comparison_p1_p2.png)\n\n")
        report.write("Przetestowano również cztery konfiguracje ABC dla funkcji Ackley: zmieniano populację, liczbę epok i `n_limits`.\n\n")
        report.write("| Populacja | Epoki | n_limits | Średni wynik | Najlepszy wynik |\n|---:|---:|---:|---:|---:|\n")
        for item in configurations:
            report.write(f"| {item['population']} | {item['epochs']} | {item['n_limits']} | {item['average_objective']:.6f} | {item['best_objective']:.6f} |\n")
        report.write("\n![Konfiguracje ABC](./configurations_abc.png)\n\n")
        report.write("CEC2014 F1 oraz pełne dane porównawcze znajdują się w [supplement_results.csv](./supplement_results.csv) i [supplement_results.json](./supplement_results.json).\n")

    with (ROOT / "P4_PREZENTACJA.md").open("a", encoding="utf-8") as presentation:
        presentation.write("\n## Slajd 13 — Dodatkowe porównanie\n\nUwzględniono CEC2014 F1 oraz wyniki P1 i P2. Wykres: [comparison_p1_p2.png](./comparison_p1_p2.png).\n")
        presentation.write("\n## Slajd 14 — Wpływ konfiguracji\n\nPorównano cztery ustawienia populacji, epok i `n_limits`. Wykres: [configurations_abc.png](./configurations_abc.png).\n")
        presentation.write("\n## Slajd 15 — Podsumowanie\n\nABC, P1 i P2 oceniono na tych samych seedach tam, gdzie funkcje były wspólne. Wyniki należy interpretować razem z czasem obliczeń i stabilnością.\n")


if __name__ == "__main__":
    main()
