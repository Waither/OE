import Chart from 'chart.js/auto';
import { getJson } from '../api.js';
import { downloadRunCsv, getRun, listRuns } from '../common/run-history.js';

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
    const crossoverEnabled = $('p1-crossover-enabled').checked;
    const mutationEnabled = $('p1-mutation-enabled').checked;
    const inversionEnabled = $('p1-inversion-enabled').checked;
    const elitismEnabled = $('p1-elitism-enabled').checked;
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
        crossover_probability: crossoverEnabled ? number('p1-crossover-probability') : 0,
        mutation: $('p1-mutation').value,
        mutation_probability: mutationEnabled ? number('p1-mutation-probability') : 0,
        inversion_probability: inversionEnabled ? number('p1-inversion-probability') : 0,
        elite_mode: $('p1-elite-mode').value,
        elite_value: elitismEnabled ? number('p1-elite-value') : 0,
        grain_probability: crossoverEnabled && $('p1-crossover').value === 'grain'
            ? number('p1-grain-probability')
            : 0,
        seed: $('p1-seed').value.trim() === '' ? null : number('p1-seed'),
    };
    if (includeRepetitions) value.repetitions = number('p1-repetitions');
    return value;
}

function syncOperatorControls() {
    const crossoverEnabled = $('p1-crossover-enabled').checked;
    const mutationEnabled = $('p1-mutation-enabled').checked;
    const inversionEnabled = $('p1-inversion-enabled').checked;
    const elitismEnabled = $('p1-elitism-enabled').checked;
    const crossoverIsGrain = $('p1-crossover').value === 'grain';
    const usesTournament = $('p1-selection').value === 'tournament';

    $('p1-crossover').disabled = !crossoverEnabled;
    $('p1-crossover-probability').disabled = !crossoverEnabled;
    $('p1-crossover-probability-field').classList.toggle('d-none', !crossoverEnabled);
    $('p1-grain-probability-field').classList.toggle('d-none', !crossoverEnabled || !crossoverIsGrain);
    $('p1-grain-probability').disabled = !crossoverEnabled || !crossoverIsGrain;

    $('p1-mutation').disabled = !mutationEnabled;
    $('p1-mutation-probability').disabled = !mutationEnabled;
    $('p1-mutation-probability-field').classList.toggle('d-none', !mutationEnabled);

    $('p1-inversion-probability').disabled = !inversionEnabled;
    $('p1-elite-mode').disabled = !elitismEnabled;
    $('p1-elite-value').disabled = !elitismEnabled;
    $('p1-elite-value-unit').textContent = $('p1-elite-mode').value === 'percentage' ? '%' : 'os.';

    $('p1-tournament').disabled = !usesTournament;
    $('p1-tournament-field').classList.toggle('d-none', !usesTournament);
}

function syncPopulationConstraints() {
    const populationSize = number('p1-population');
    const maximumTournamentSize = Math.max(2, populationSize);
    const tournament = $('p1-tournament');
    tournament.max = String(maximumTournamentSize);
    if (number('p1-tournament') > maximumTournamentSize) {
        tournament.value = String(maximumTournamentSize);
    }

    const eliteValue = $('p1-elite-value');
    const maximumEliteValue = $('p1-elite-mode').value === 'percentage'
        ? 99
        : Math.max(0, populationSize - 1);
    eliteValue.max = String(maximumEliteValue);
    if (number('p1-elite-value') > maximumEliteValue) {
        eliteValue.value = String(maximumEliteValue);
    }
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

function setHistoryStatus(message, isError = false) {
    const element = $('p1-history-status');
    element.textContent = message;
    element.classList.toggle('text-danger', isError);
    element.classList.toggle('text-muted', !isError);
}

function createHistoryCell(text) {
    const cell = document.createElement('td');
    cell.textContent = text;
    return cell;
}

function formatSeconds(value) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
    if (value < 1) return `${(value * 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })} ms`;
    return `${value.toLocaleString(undefined, { maximumFractionDigits: 3 })} s`;
}

function renderHistory(runs) {
    const list = $('p1-history-list');
    list.replaceChildren();

    for (const run of runs) {
        const row = document.createElement('tr');
        const parameters = run.parameters ?? {};
        const result = run.result_data ?? {};
        const benchmark = benchmarks.find((item) => item.key === parameters.function_key);
        const bestObjective = result.best_objective;
        const optimumError = typeof bestObjective === 'number' && benchmark
            ? Math.abs(bestObjective - benchmark.optimum)
            : null;
        const createdAt = new Date(run.created_at);
        const dateText = Number.isNaN(createdAt.getTime())
            ? run.created_at
            : createdAt.toLocaleString();

        row.append(
            createHistoryCell(dateText),
            createHistoryCell(String(parameters.function_key ?? '—')),
            createHistoryCell(String(parameters.dimensions ?? '—')),
            createHistoryCell(String(run.seed)),
            createHistoryCell(typeof bestObjective === 'number' ? bestObjective.toLocaleString() : '—'),
            createHistoryCell(formatSeconds(result.elapsed_seconds)),
            createHistoryCell(optimumError === null ? '—' : optimumError.toLocaleString(undefined, { maximumFractionDigits: 5 })),
        );

        const actions = document.createElement('td');
        actions.className = 'text-nowrap';

        const loadButton = document.createElement('button');
        loadButton.type = 'button';
        loadButton.className = 'btn btn-sm btn-outline-primary me-2';
        loadButton.textContent = 'Wczytaj wynik';
        loadButton.addEventListener('click', () => void loadHistoricalRun(run.id));

        const parametersButton = document.createElement('button');
        parametersButton.type = 'button';
        parametersButton.className = 'btn btn-sm btn-outline-success me-2';
        parametersButton.textContent = 'Wgraj parametry';
        parametersButton.addEventListener('click', () => loadHistoricalParameters(run));

        const exportButton = document.createElement('button');
        exportButton.type = 'button';
        exportButton.className = 'btn btn-sm btn-outline-secondary';
        exportButton.textContent = 'CSV';
        exportButton.addEventListener('click', () => {
            downloadRunCsv(run.id).catch((error) => setHistoryStatus(error.message, true));
        });

        actions.append(loadButton, parametersButton, exportButton);
        row.append(actions);
        list.append(row);
    }

    setHistoryStatus(runs.length ? `Wyświetlono ${runs.length} zapisanych uruchomień.` : 'Brak zapisanych uruchomień P1.');
}

function loadHistoricalParameters(run) {
    const parameters = run.parameters ?? {};
    const fields = {
        function_key: 'p1-function',
        dimensions: 'p1-dimensions',
        precision: 'p1-precision',
        population_size: 'p1-population',
        epochs: 'p1-epochs',
        objective: 'p1-objective',
        selection: 'p1-selection',
        tournament_size: 'p1-tournament',
        crossover: 'p1-crossover',
        crossover_probability: 'p1-crossover-probability',
        mutation: 'p1-mutation',
        mutation_probability: 'p1-mutation-probability',
        inversion_probability: 'p1-inversion-probability',
        elite_mode: 'p1-elite-mode',
        elite_value: 'p1-elite-value',
        grain_probability: 'p1-grain-probability',
    };

    if (!benchmarks.some((item) => item.key === parameters.function_key)) {
        setHistoryStatus('Nie można wgrać parametrów: zapis wskazuje nieznaną funkcję.', true);
        return;
    }

    $('p1-function').value = parameters.function_key;
    refreshDimensions();
    for (const [parameter, id] of Object.entries(fields)) {
        const element = $(id);
        const value = parameters[parameter];
        if (element && value !== undefined && value !== null) {
            element.value = String(value);
        }
    }
    $('p1-crossover-enabled').checked = (parameters.crossover_probability ?? 0) > 0;
    $('p1-mutation-enabled').checked = (parameters.mutation_probability ?? 0) > 0;
    $('p1-inversion-enabled').checked = (parameters.inversion_probability ?? 0) > 0;
    $('p1-elitism-enabled').checked = (parameters.elite_value ?? 0) > 0;
    syncOperatorControls();
    syncPopulationConstraints();
    $('p1-seed').value = String(run.seed);
    $('p1-repetitions').value = '1';
    $('p1-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
    setHistoryStatus('Wgrano parametry zapisanego uruchomienia. Możesz od razu uruchomić je ponownie.');
}

async function refreshHistory() {
    setHistoryStatus('Wczytywanie historii…');
    try {
        const runs = await listRuns('p1', 50);
        renderHistory(runs);
    } catch (error) {
        setHistoryStatus(`Nie udało się wczytać historii: ${error.message}`, true);
    }
}

async function loadHistoricalRun(runId) {
    setHistoryStatus('Wczytywanie zapisanego uruchomienia…');
    try {
        const run = await getRun(runId);
        if (run.project_key !== 'p1') {
            throw new Error('To uruchomienie nie należy do Projektu 1.');
        }
        const createdAt = new Date(run.created_at).toLocaleString();
        showResult(run.result_data, `Zapisane uruchomienie — ${createdAt} (seed ${run.seed})`);
        setHistoryStatus('Wczytano zapisany wynik i historię epok.');
    } catch (error) {
        setHistoryStatus(`Nie udało się wczytać uruchomienia: ${error.message}`, true);
    }
}

async function runSingle(event) {
    event.preventDefault();
    showStatus('Trwa obliczanie…');
    try {
        const response = await fetch('/api/p1/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload()) });
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        $('p1-seed').value = String(data.seed);
        showResult(data.result, `Pojedyncze uruchomienie (seed ${data.seed})`);
        showStatus('Obliczenia zakończone.', 'success');
        void refreshHistory();
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
        $('p1-seed').value = String(data.seed);
        const summary = data.summary;
        $('p1-result').innerHTML = `<div class="card"><div class="card-body"><h2 class="h5">Eksperyment — ${data.repetitions} powtórzeń</h2><p>Średni wynik: ${summary.average_objective}</p><p>Najlepszy wynik: ${summary.best_objective}</p><p>Najgorszy wynik: ${summary.worst_objective}</p><p>Średni błąd: ${summary.average_error}</p><p>Średni czas: ${summary.average_elapsed_seconds.toFixed(4)} s</p></div></div>`;
        const bestRun = data.runs.reduce((best, run) => $('p1-objective').value === 'minimize' ? (run.result.best_objective < best.result.best_objective ? run : best) : (run.result.best_objective > best.result.best_objective ? run : best));
        drawCharts(bestRun.result.history);
        showStatus('Eksperyment zakończony.', 'success');
        void refreshHistory();
    } catch (error) {
        showStatus(error.message, 'danger');
    }
}

export async function mount() {
    benchmarks = await getJson('/p1/benchmarks');
    $('p1-function').innerHTML = benchmarks.map((item) => `<option value="${item.key}">${item.name}</option>`).join('');
    $('p1-function').addEventListener('change', refreshDimensions);
    $('p1-population').addEventListener('input', syncPopulationConstraints);
    $('p1-elite-mode').addEventListener('change', syncPopulationConstraints);
    for (const id of [
        'p1-crossover-enabled',
        'p1-mutation-enabled',
        'p1-inversion-enabled',
        'p1-elitism-enabled',
        'p1-crossover',
        'p1-selection',
    ]) {
        $(id).addEventListener('change', syncOperatorControls);
    }
    refreshDimensions();
    syncOperatorControls();
    syncPopulationConstraints();
    $('p1-form').addEventListener('submit', runSingle);
    $('p1-experiment').addEventListener('click', runExperiment);
    $('p1-history-refresh').addEventListener('click', refreshHistory);
    await refreshHistory();
}
