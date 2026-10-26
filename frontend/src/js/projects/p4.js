import Chart from 'chart.js/auto';

const byId = (id) => document.getElementById(id);
const form = byId('p4-form');
let convergenceChart;
let runsChart;

function renderCharts(result) {
    convergenceChart?.destroy();
    runsChart?.destroy();
    const runs = result.runs ?? [];
    const historyLength = Math.max(0, ...runs.map((run) => run.result.history.length));
    const averageHistory = (key) => Array.from({ length: historyLength }, (_, index) => {
        const values = runs.map((run) => run.result.history[index]?.[key]).filter((value) => typeof value === 'number');
        return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
    });
    convergenceChart = new Chart(byId('p4-convergence-chart'), {
        type: 'line',
        data: { labels: Array.from({ length: historyLength }, (_, index) => index + 1), datasets: [
            { label: 'Średnia najlepszego wyniku ABC', data: averageHistory('best'), borderColor: '#0d6efd' },
            { label: 'Średnia populacji', data: averageHistory('mean'), borderColor: '#198754' },
        ] },
        options: { responsive: true, scales: { y: { beginAtZero: false } } },
    });
    runsChart = new Chart(byId('p4-runs-chart'), {
        type: 'bar',
        data: { labels: runs.map((_, index) => `Uruchomienie ${index + 1}`), datasets: [{ label: 'Najlepsza wartość funkcji', data: runs.map((run) => run.result.best_objective), backgroundColor: '#fd7e14' }] },
        options: { responsive: true, scales: { y: { beginAtZero: false } } },
    });
}

byId('p4-function')?.addEventListener('change', () => {
    const dimensions = { quadratic: 2, cec2014_f1: 10, cec2014_f3: 10 };
    if (dimensions[byId('p4-function').value]) byId('p4-dimensions').value = dimensions[byId('p4-function').value];
});

form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    byId('p4-status').textContent = 'Obliczenia…';
    const body = { function_key: byId('p4-function').value, dimensions: Number(byId('p4-dimensions').value), population_size: Number(byId('p4-population').value), epochs: Number(byId('p4-epochs').value), repetitions: Number(byId('p4-repetitions').value) };
    try {
        const response = await fetch('/api/p4/experiment', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
        if (!response.ok) throw new Error(await response.text());
        const result = await response.json();
        byId('p4-result').innerHTML = `<div class="card"><div class="card-body"><h2 class="h5">Wynik ABC</h2><dl class="row mb-0"><dt class="col-sm-5">Średnia wartość funkcji</dt><dd class="col-sm-7">${result.summary.average_objective.toFixed(6)}</dd><dt class="col-sm-5">Najlepszy wynik</dt><dd class="col-sm-7">${result.summary.best_objective.toFixed(6)}</dd><dt class="col-sm-5">Liczba powtórzeń</dt><dd class="col-sm-7">${result.repetitions}</dd></dl></div></div><div class="row g-4 mt-1"><div class="col-lg-7"><div class="card card-body"><h2 class="h5">Zbieżność w kolejnych epokach</h2><canvas id="p4-convergence-chart" aria-label="Wykres zbieżności P4"></canvas></div></div><div class="col-lg-5"><div class="card card-body"><h2 class="h5">Wynik każdego uruchomienia</h2><canvas id="p4-runs-chart" aria-label="Porównanie uruchomień P4"></canvas></div></div></div>`;
        renderCharts(result);
        byId('p4-status').textContent = 'Gotowe';
    } catch (error) { byId('p4-status').textContent = `Błąd: ${error.message}`; }
});
