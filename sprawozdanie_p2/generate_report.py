from __future__ import annotations

import json
import time
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.projects.p1.logic import GAConfig as BinaryConfig, GeneticAlgorithm as BinaryGA
from backend.projects.p2.logic import GAConfig as RealConfig, GeneticAlgorithm as RealGA

OUT = Path(__file__).parent
OUT.mkdir(exist_ok=True)


def run_real(**kwargs):
    return RealGA(RealConfig(**kwargs), seed=kwargs.pop("seed", None)).run()


def run_binary(**kwargs):
    return BinaryGA(BinaryConfig(**kwargs), seed=kwargs.pop("seed", None)).run()


def summarize(results):
    values = np.array([r.best_objective for r in results], dtype=float)
    times = np.array([r.elapsed_seconds for r in results], dtype=float)
    histories = np.array([[s.best for s in r.history] for r in results], dtype=float)
    means = np.array([[s.mean for s in r.history] for r in results], dtype=float)
    deviations = np.array([[s.standard_deviation for s in r.history] for r in results], dtype=float)
    return {
        "average_objective": float(values.mean()),
        "std_objective": float(values.std()),
        "best_objective": float(values.min()),
        "average_time": float(times.mean()),
        "best_history_mean": histories.mean(axis=0).tolist(),
        "best_history_std": histories.std(axis=0).tolist(),
        "population_mean": means.mean(axis=0).tolist(),
        "population_stddev": deviations.mean(axis=0).tolist(),
    }


common = dict(function_key="ackley01", dimensions=5, population_size=40, epochs=100, objective="minimize", selection="tournament", tournament_size=3, crossover_probability=0.8, mutation_probability=0.1, elite_mode="count", elite_value=2, precision=8, inversion_probability=0, grain_probability=0.5)
seeds = range(100, 110)
results = {"benchmark": {"name": "Ackley 01", "dimensions": 5, "population": 40, "epochs": 100, "repetitions": 10}, "configurations": {}, "comparison": {}}

operator_configs = {
    "arytmetyczne": {"crossover": "arithmetic", "mutation": "uniform", "alpha": 0.5, "beta": 0.25, "gaussian_sigma": 0.1},
    "linearne": {"crossover": "linear", "mutation": "uniform", "alpha": 0.5, "beta": 0.25, "gaussian_sigma": 0.1},
    "blx_alfa": {"crossover": "blend_alpha", "mutation": "uniform", "alpha": 0.5, "beta": 0.25, "gaussian_sigma": 0.1},
    "blx_alfa_beta": {"crossover": "blend_alpha_beta", "mutation": "uniform", "alpha": 0.5, "beta": 0.25, "gaussian_sigma": 0.1},
    "usredniajace": {"crossover": "average", "mutation": "uniform", "alpha": 0.5, "beta": 0.25, "gaussian_sigma": 0.1},
    "gauss": {"crossover": "blend_alpha", "mutation": "gaussian", "alpha": 0.5, "beta": 0.25, "gaussian_sigma": 0.1},
}

for name, extra in operator_configs.items():
    run_results = [RealGA(RealConfig(**common, **extra), seed=seed).run() for seed in seeds]
    results["configurations"][name] = summarize(run_results)

binary_results = [BinaryGA(BinaryConfig(**common, crossover="two_point", mutation="one_point"), seed=seed).run() for seed in seeds]
real_results = [RealGA(RealConfig(**common, crossover="blend_alpha", mutation="gaussian", alpha=0.5, beta=0.25, gaussian_sigma=0.1), seed=seed).run() for seed in seeds]
results["comparison"] = {"binarna_p1": summarize(binary_results), "rzeczywista_p2": summarize(real_results)}

with (OUT / "results.json").open("w", encoding="utf-8") as stream:
    json.dump(results, stream, ensure_ascii=False, indent=2)

epochs = np.arange(101)
best = results["configurations"]["blx_alfa"]
plt.figure(figsize=(10, 5))
plt.plot(epochs, best["best_history_mean"], label="Średnia najlepszego osobnika")
plt.fill_between(epochs, np.array(best["best_history_mean"]) - np.array(best["best_history_std"]), np.array(best["best_history_mean"]) + np.array(best["best_history_std"]), alpha=.2)
plt.xlabel("Iteracja"); plt.ylabel("Wartość funkcji celu"); plt.title("P2: zbieżność dla operatora BLX-α"); plt.grid(alpha=.25); plt.legend(); plt.tight_layout(); plt.savefig(OUT / "convergence.png", dpi=160); plt.close()

plt.figure(figsize=(10, 5))
plt.plot(epochs, best["population_mean"], label="Średnia populacji")
plt.plot(epochs, best["population_stddev"], label="Średnie odchylenie standardowe")
plt.xlabel("Iteracja"); plt.ylabel("Wartość"); plt.title("P2: średnia i odchylenie standardowe"); plt.grid(alpha=.25); plt.legend(); plt.tight_layout(); plt.savefig(OUT / "statistics.png", dpi=160); plt.close()

names = list(results["configurations"])
plt.figure(figsize=(10, 5)); plt.bar(names, [results["configurations"][x]["average_objective"] for x in names]); plt.ylabel("Średni najlepszy wynik"); plt.title("Porównanie konfiguracji P2"); plt.xticks(rotation=25, ha="right"); plt.tight_layout(); plt.savefig(OUT / "configurations.png", dpi=160); plt.close()

labels = ["Binarna P1", "Rzeczywista P2"]
comparison = results["comparison"]
plt.figure(figsize=(8, 5)); plt.bar(labels, [comparison["binarna_p1"]["average_objective"], comparison["rzeczywista_p2"]["average_objective"]]); plt.ylabel("Średni najlepszy wynik"); plt.title("P1 kontra P2"); plt.tight_layout(); plt.savefig(OUT / "comparison.png", dpi=160); plt.close()

x = np.linspace(-35, 35, 180); y = np.linspace(-35, 35, 180); xx, yy = np.meshgrid(x, y)
zz = -20 * np.exp(-0.2 * np.sqrt((xx * xx + yy * yy) / 2)) - np.exp((np.cos(2 * np.pi * xx) + np.cos(2 * np.pi * yy)) / 2) + np.e + 20
plt.figure(figsize=(7, 6)); plt.contourf(xx, yy, zz, levels=40, cmap="viridis"); plt.colorbar(label="f(x)"); plt.xlabel("x₁"); plt.ylabel("x₂"); plt.title("Funkcja Ackleya — przekrój 2D"); plt.tight_layout(); plt.savefig(OUT / "ackley_surface.png", dpi=160); plt.close()

def row(name, item):
    return f"| {name} | {item['average_objective']:.4f} | {item['std_objective']:.4f} | {item['average_time']:.6f} s |"

report = fr'''# Projekt 2 — implementacja chromosomu rzeczywistego

## 1. Cel projektu

Celem było zastąpienie binarnej reprezentacji chromosomu reprezentacją rzeczywistą oraz porównanie obu podejść w klasycznym algorytmie genetycznym.

## 2. Technologie

- Python 3.14.3, FastAPI, NumPy, SQLAlchemy i Uvicorn,
- `benchmark_functions` — funkcja Hyperellipsoid,
- `opfunu` — funkcja Ackley 01, CEC2014 F1 (zgodna z P1) oraz dodatkowo CEC2014 F3,
- JavaScript, Vite, Chart.js — interfejs i wykresy,
- Matplotlib — wykresy do sprawozdania.

## 3. Funkcja optymalizowana

W eksperymentach użyto funkcji Ackleya:

$$f(x) = -20e^{{-0.2\sqrt{{\frac{{1}}{{n}}\sum_{{i=1}}^n x_i^2}}}} - e^{{\frac{{1}}{{n}}\sum_{{i=1}}^n\cos(2\pi x_i)}} + 20 + e$$

Dziedzina eksperymentu: $x_i \in [-35, 35]$, optimum globalne: $f(0, ..., 0)=0$.

![Wykres funkcji Ackleya](ackley_surface.png)

## 4. Wymagania środowiska

- Python 3.11+,
- zależności z `requirements.txt`,
- Node.js 20+ do zbudowania frontendu,
- uruchomienie backendu: `python -m uvicorn backend.main:app --reload`,
- zbudowanie frontendu: `npm install` oraz `npm run build` w katalogu `frontend`.

## 5. Zaimplementowane operatory

Chromosom jest wektorem liczb rzeczywistych ograniczanych do dziedziny funkcji. Zaimplementowano krzyżowanie arytmetyczne, linearne, BLX-α, BLX-αβ i uśredniające oraz mutację równomierną i Gaussa.

## 6. Wyniki

Eksperyment: 10 powtórzeń, populacja 40 osobników, 100 iteracji, selekcja turniejowa, elityzm 2 osobników.

### 6.1. Zbieżność i statystyki

![Zbieżność](convergence.png)

![Średnia i odchylenie standardowe](statistics.png)

### 6.2. Porównanie konfiguracji

![Konfiguracje](configurations.png)

| Konfiguracja | Średni najlepszy wynik | Odchylenie wyników | Średni czas |
|---|---:|---:|---:|
{chr(10).join(row(name, results["configurations"][name]) for name in names)}

### 6.3. Reprezentacja binarna a rzeczywista

![Porównanie reprezentacji](comparison.png)

| Reprezentacja | Średni najlepszy wynik | Odchylenie wyników | Średni czas |
|---|---:|---:|---:|
{row("Binarna P1", comparison["binarna_p1"])}
{row("Rzeczywista P2", comparison["rzeczywista_p2"])}

## 7. Wnioski

Reprezentacja rzeczywista eliminuje etap kodowania i dekodowania bitów oraz pozwala bezpośrednio stosować operatory arytmetyczne. Ostateczna ocena jakości zależy od operatora, parametrów mutacji, liczby iteracji i rozmiaru populacji, dlatego porównanie należy interpretować razem z czasem obliczeń i odchyleniem wyników.
'''
(OUT / "SPRAWOZDANIE-P2.md").write_text(report, encoding="utf-8")
print(f"Generated report in {OUT}")
