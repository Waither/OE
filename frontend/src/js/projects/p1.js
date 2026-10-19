import Chart from 'chart.js/auto';
import { getJson } from '../api.js';

let benchmarks = [];
let objectiveChart;
let statsChart;

const $ = (id) => document.querySelector(`#${id}`);
const number = (id) => Number($(id).value);

function showStatus(message, type = 'info') {
    const element = $('p1-status');
    element.textContent = message;
    element.className = `alert alert-${type} mt-3`;
}

function selectedBenchmark() {
    return benchmarks.find((item) => item.key === $('p1-function').value);
}

function refreshDimensions() {
    const benchmark = selectedBenchmark();
    $('p1-dimensions').innerHTML = benchmark.dimensions
        .map((dimension) => `<option value="${dimension}">${dimension}</option>`)
        .join('');
}

function payload(includeRepetitions = false) {
    const value = {
        function_key: $('p1-function').value,
        dimensions: number('p1-dimensions'),
        precision: number('p1-precision'),
        population_size: number('p1-population'),
        epochs: number('p1-epochs'),
        objective: $('p1-objective').value,
        selection: $('p1-selection').value,
        tournament_size: number('p1-tournament'),
        crossover: $('p1-crossover').value,
        crossover_probability: number('p1-crossover-probability'),
        mutation: $('p1-mutation').value,
        mutation_probability: number('p1-mutation-probability'),
        inversion_probability: number('p1-inversion-probability'),
        elite_mode: $('p1-elite-mode').value,
        elite_value: number('p1-elite-value'),
        grain_probability: 0.5,
    };
    if (includeRepetitions) value.repetitions = number('p1-repetitions');
    return value;
}

function drawCharts(history) {
    const labels = history.map((item) => item.epoch);
    objectiveChart?.destroy();
    statsChart?.destroy();
    objectiveChart = new Chart($('p1-objective-chart'), {
        type: 'line',
        data: { labels, datasets: [
            { label: 'Najlepsza wartość', data: history.map((item) => item.best), borderColor: '#0d6efd' },
            { label: 'Najgorsza wartość', data: history.map((item) => item.worst), borderColor: '#dc3545' },
        ] },
        options: { responsive: true, plugins: { title: { display: true, text: 'Wartość funkcji względem epoki' } } },
    });
    statsChart = new Chart($('p1-stats-chart'), {
        type: 'line',
        data: { labels, datasets: [
            { label: 'Średnia', data: history.map((item) => item.mean), borderColor: '#198754' },
            { label: 'Odchylenie standardowe', data: history.map((item) => item.standard_deviation), borderColor: '#fd7e14' },
        ] },
        options: { responsive: true, plugins: { title: { display: true, text: 'Średnia i odchylenie standardowe' } } },
    });
}

function showResult(result, label = 'Wynik') {
    $('p1-result').innerHTML = `<div class="card"><div class="card-body"><h2 class="h5">${label}</h2><dl class="row mb-0"><dt class="col-sm-5">Wartość funkcji</dt><dd class="col-sm-7">${result.best_objective}</dd><dt class="col-sm-5">Czas obliczeń</dt><dd class="col-sm-7">${result.elapsed_seconds.toFixed(4)} s</dd><dt class="col-sm-5">Najlepszy wektor</dt><dd class="col-sm-7 text-break">${result.best_values.join(', ')}</dd></dl></div></div>`;
    drawCharts(result.history);
}

async function runSingle(event) {
    event.preventDefault();
    showStatus('Trwa obliczanie…');
    try {
        const response = await fetch('/api/p1/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload()) });
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        showResult(data.result, `Pojedyncze uruchomienie (seed ${data.seed})`);
        showStatus('Obliczenia zakończone.', 'success');
    } catch (error) {
        showStatus(error.message, 'danger');
    }
}

async function runExperiment() {
    showStatus('Trwa seria powtórzeń…');
    try {
        const response = await fetch('/api/p1/experiment', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload(true)) });
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        const summary = data.summary;
        $('p1-result').innerHTML = `<div class="card"><div class="card-body"><h2 class="h5">Eksperyment — ${data.repetitions} powtórzeń</h2><p>Średni wynik: ${summary.average_objective}</p><p>Najlepszy wynik: ${summary.best_objective}</p><p>Najgorszy wynik: ${summary.worst_objective}</p><p>Średni błąd: ${summary.average_error}</p><p>Średni czas: ${summary.average_elapsed_seconds.toFixed(4)} s</p></div></div>`;
        const bestRun = data.runs.reduce((best, run) => $('p1-objective').value === 'minimize' ? (run.result.best_objective < best.result.best_objective ? run : best) : (run.result.best_objective > best.result.best_objective ? run : best));
        drawCharts(bestRun.result.history);
        showStatus('Eksperyment zakończony.', 'success');
    } catch (error) {
        showStatus(error.message, 'danger');
    }
}

export async function mount() {
    benchmarks = await getJson('/p1/benchmarks');
    $('p1-function').innerHTML = benchmarks.map((item) => `<option value="${item.key}">${item.name}</option>`).join('');
    $('p1-function').addEventListener('change', refreshDimensions);
    refreshDimensions();
    $('p1-form').addEventListener('submit', runSingle);
    $('p1-experiment').addEventListener('click', runExperiment);
}
