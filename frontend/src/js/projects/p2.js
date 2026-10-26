import Chart from 'chart.js/auto';
import { getJson } from '../api.js';
import { downloadRunCsv, getRun, listRuns } from '../common/run-history.js';

let benchmarks = [];
let objectiveChart;
let statsChart;

const $ = (id) => document.querySelector(`#${id}`);
const number = (id) => Number($(id).value);

function showStatus(message, type = 'info') {
    const element = $('p2-status');
    element.textContent = message;
    element.className = `alert alert-${type} mt-3`;
}

function selectedBenchmark() {
    return benchmarks.find((item) => item.key === $('p2-function').value);
}

function refreshDimensions() {
    const benchmark = selectedBenchmark();
    $('p2-dimensions').innerHTML = benchmark.dimensions
        .map((dimension) => `<option value="${dimension}">${dimension}</option>`)
        .join('');
}

function payload(includeRepetitions = false) {
    const crossoverEnabled = $('p2-crossover-enabled').checked;
    const mutationEnabled = $('p2-mutation-enabled').checked;
    const elitismEnabled = $('p2-elitism-enabled').checked;
    const value = {
        function_key: $('p2-function').value,
        dimensions: number('p2-dimensions'),
        precision: number('p2-precision'),
        population_size: number('p2-population'),
        epochs: number('p2-epochs'),
        objective: $('p2-objective').value,
        selection: $('p2-selection').value,
        tournament_size: number('p2-tournament'),
        crossover: $('p2-crossover').value,
        crossover_probability: crossoverEnabled ? number('p2-crossover-probability') : 0,
        mutation: $('p2-mutation').value,
        mutation_probability: mutationEnabled ? number('p2-mutation-probability') : 0,
        inversion_probability: 0,
        elite_mode: $('p2-elite-mode').value,
        elite_value: elitismEnabled ? number('p2-elite-value') : 0,
        grain_probability: 0,
        alpha: number('p2-grain-probability'),
        beta: number('p2-inversion-probability'),
        gaussian_sigma: number('p2-gaussian-sigma'),
        seed: $('p2-seed').value.trim() === '' ? null : $('p2-seed').value.trim(),
    };
    if (includeRepetitions) value.repetitions = number('p2-repetitions');
    return value;
}

function formatExperimentConfiguration(configuration) {
    const benchmark = benchmarks.find((item) => item.key === configuration.function_key);
    const formatPercentage = (value) => `${Number((value * 100).toFixed(2))}%`;
    const values = [
        ['Funkcja', benchmark?.name ?? configuration.function_key],
        ['Wymiary', configuration.dimensions],
        ['Dokładność (cyfry dziesiętne)', configuration.precision],
        ['Rozmiar populacji', configuration.population_size],
        ['Liczba epok', configuration.epochs],
        ['Cel', configuration.objective === 'minimize' ? 'Minimalizacja' : 'Maksymalizacja'],
        ['Selekcja', {
            best: 'Najlepszych',
            worst: 'Najgorszych',
            roulette: 'Ruletkowa',
            tournament: 'Turniejowa',
        }[configuration.selection]],
        ['Rozmiar turnieju', configuration.tournament_size],
        ['Krzyżowanie', {
            arithmetic: 'Arytmetyczne',
            linear: 'Linearne',
            blend_alpha: 'Mieszające alfa',
            blend_alpha_beta: 'Mieszające alfa i beta',
            average: 'Uśredniające',
        }[configuration.crossover]],
        ['Prawdopodobieństwo krzyżowania', formatPercentage(configuration.crossover_probability)],
        ['Mutacja', {
            uniform: 'Równomierna',
            gaussian: 'Gaussa',
        }[configuration.mutation]],
        ['Prawdopodobieństwo mutacji', formatPercentage(configuration.mutation_probability)],
        ['Parametr alfa', configuration.alpha],
        ['Parametr beta', configuration.beta],
        ['Sigma mutacji Gaussa', configuration.gaussian_sigma],
        ['Elityzm', configuration.elite_mode === 'count' ? 'Liczba osobników' : 'Procent populacji'],
        ['Wartość elityzmu', configuration.elite_mode === 'count'
            ? `${configuration.elite_value} os.`
            : `${configuration.elite_value}%`],
    ];
    return `<table class="table table-sm mb-0"><tbody>${values
        .map(([label, value]) => `<tr><th scope="row">${label}</th><td>${value}</td></tr>`)
        .join('')}</tbody></table>`;
}

function syncOperatorControls() {
    const crossoverEnabled = $('p2-crossover-enabled').checked;
    const mutationEnabled = $('p2-mutation-enabled').checked;
    const elitismEnabled = $('p2-elitism-enabled').checked;
    const usesTournament = $('p2-selection').value === 'tournament';

    $('p2-crossover').disabled = !crossoverEnabled;
    $('p2-crossover-probability').disabled = !crossoverEnabled;
    $('p2-crossover-probability-field').classList.toggle('d-none', !crossoverEnabled);
    $('p2-grain-probability-field').classList.toggle('d-none', !crossoverEnabled);
    $('p2-grain-probability').disabled = !crossoverEnabled;

    $('p2-mutation').disabled = !mutationEnabled;
    $('p2-mutation-probability').disabled = !mutationEnabled;
    $('p2-mutation-probability-field').classList.toggle('d-none', !mutationEnabled);

    $('p2-inversion-probability').disabled = false;
    $('p2-gaussian-sigma').disabled = false;
    $('p2-elite-mode').disabled = !elitismEnabled;
    $('p2-elite-value').disabled = !elitismEnabled;
    $('p2-elite-value-unit').textContent = $('p2-elite-mode').value === 'percentage' ? '%' : 'os.';

    $('p2-tournament').disabled = !usesTournament;
    $('p2-tournament-field').classList.toggle('d-none', !usesTournament);
    syncPopulationConstraints();
}

function syncPopulationConstraints() {
    const populationSize = number('p2-population');
    const maximumTournamentSize = Math.max(2, populationSize);
    const tournament = $('p2-tournament');
    tournament.max = String(maximumTournamentSize);
    if (number('p2-tournament') > maximumTournamentSize) {
        tournament.value = String(maximumTournamentSize);
    }

    const eliteValue = $('p2-elite-value');
    const maximumEliteValue = $('p2-elite-mode').value === 'percentage'
        ? 99
        : Math.max(0, populationSize - 1);
    eliteValue.max = String(maximumEliteValue);
    if (number('p2-elite-value') > maximumEliteValue) {
        eliteValue.value = String(maximumEliteValue);
    }
}

function drawCharts(history) {
    const labels = history.map((item) => item.epoch);
    objectiveChart?.destroy();
    statsChart?.destroy();
    objectiveChart = new Chart($('p2-objective-chart'), {
        type: 'line',
        data: { labels, datasets: [
            { label: 'Najlepsza wartość', data: history.map((item) => item.best), borderColor: '#0d6efd' },
            { label: 'Najgorsza wartość', data: history.map((item) => item.worst), borderColor: '#dc3545' },
        ] },
        options: { responsive: true, plugins: { title: { display: true, text: 'Wartość funkcji względem epoki' } } },
    });
    statsChart = new Chart($('p2-stats-chart'), {
        type: 'line',
        data: { labels, datasets: [
            { label: 'Średnia', data: history.map((item) => item.mean), borderColor: '#198754' },
            { label: 'Odchylenie standardowe', data: history.map((item) => item.standard_deviation), borderColor: '#fd7e14' },
        ] },
        options: { responsive: true, plugins: { title: { display: true, text: 'Średnia i odchylenie standardowe' } } },
    });
}

function showResult(result, label = 'Wynik') {
    $('p2-result').innerHTML = `<div class="card"><div class="card-body"><h2 class="h5">${label}</h2><dl class="row mb-0"><dt class="col-sm-5">Wartość funkcji</dt><dd class="col-sm-7">${result.best_objective}</dd><dt class="col-sm-5">Czas obliczeń</dt><dd class="col-sm-7">${result.elapsed_seconds.toFixed(4)} s</dd><dt class="col-sm-5">Najlepszy wektor</dt><dd class="col-sm-7 text-break">${result.best_values.join(', ')}</dd></dl></div></div>`;
    drawCharts(result.history);
}

function setHistoryStatus(message, isError = false) {
    const element = $('p2-history-status');
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

async function responseError(response) {
    let body;
    try {
        body = await response.json();
    } catch {
        return `Błąd ${response.status}: ${response.statusText}`;
    }
    const detail = body.detail;
    if (Array.isArray(detail)) {
        return detail.map((item) => {
            const field = Array.isArray(item.loc) ? item.loc.slice(1).join('.') : '';
            return field ? `${field}: ${item.msg}` : item.msg;
        }).join('; ');
    }
    return typeof detail === 'string'
        ? detail
        : `Błąd ${response.status}: ${response.statusText}`;
}

function renderHistory(runs) {
    const list = $('p2-history-list');
    list.replaceChildren();

    for (const run of runs) {
        const row = document.createElement('tr');
        const parameters = run.parameters ?? {};
        const result = run.result_data ?? {};
        const benchmark = benchmarks.find((item) => item.key === parameters.function_key);
        const bestObjective = result.best_objective;
        const experimentId = parameters.experiment?.id;
        const optimumError = typeof bestObjective === 'number'
            && benchmark
            && parameters.objective !== 'maximize'
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
            createHistoryCell(experimentId ?? '—'),
            createHistoryCell(run.seed_exact ?? String(run.seed)),
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

    setHistoryStatus(runs.length ? `Wyświetlono ${runs.length} zapisanych uruchomień.` : 'Brak zapisanych uruchomień p2.');
}

function loadHistoricalParameters(run) {
    const parameters = run.parameters ?? {};
    const fields = {
        function_key: 'p2-function',
        dimensions: 'p2-dimensions',
        precision: 'p2-precision',
        population_size: 'p2-population',
        epochs: 'p2-epochs',
        objective: 'p2-objective',
        selection: 'p2-selection',
        tournament_size: 'p2-tournament',
        crossover: 'p2-crossover',
        crossover_probability: 'p2-crossover-probability',
        mutation: 'p2-mutation',
        mutation_probability: 'p2-mutation-probability',
        inversion_probability: 'p2-inversion-probability',
        elite_mode: 'p2-elite-mode',
        elite_value: 'p2-elite-value',
        grain_probability: 'p2-grain-probability',
        alpha: 'p2-grain-probability',
        beta: 'p2-inversion-probability',
        gaussian_sigma: 'p2-gaussian-sigma',
    };

    if (!benchmarks.some((item) => item.key === parameters.function_key)) {
        setHistoryStatus('Nie można wgrać parametrów: zapis wskazuje nieznaną funkcję.', true);
        return;
    }

    $('p2-function').value = parameters.function_key;
    refreshDimensions();
    for (const [parameter, id] of Object.entries(fields)) {
        const element = $(id);
        const value = parameters[parameter];
        if (element && value !== undefined && value !== null) {
            element.value = String(value);
        }
    }
    $('p2-crossover-enabled').checked = (parameters.crossover_probability ?? 0) > 0;
    $('p2-mutation-enabled').checked = (parameters.mutation_probability ?? 0) > 0;
    $('p2-elitism-enabled').checked = (parameters.elite_value ?? 0) > 0;
    syncOperatorControls();
    syncPopulationConstraints();
    $('p2-seed').value = run.seed_exact ?? String(run.seed);
    $('p2-repetitions').value = '10';
    $('p2-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
    setHistoryStatus('Wgrano parametry zapisanego uruchomienia. Możesz od razu uruchomić je ponownie.');
}

async function refreshHistory() {
    setHistoryStatus('Wczytywanie historii…');
    try {
        const runs = await listRuns('p2', 50);
        renderHistory(runs);
    } catch (error) {
        setHistoryStatus(`Nie udało się wczytać historii: ${error.message}`, true);
    }
}

async function loadHistoricalRun(runId) {
    setHistoryStatus('Wczytywanie zapisanego uruchomienia…');
    try {
        const run = await getRun(runId);
        if (run.project_key !== 'p2') {
            throw new Error('To uruchomienie nie należy do Projektu 2.');
        }
        const createdAt = new Date(run.created_at).toLocaleString();
        showResult(run.result_data, `Zapisane uruchomienie — ${createdAt} (seed ${run.seed_exact ?? run.seed})`);
        setHistoryStatus('Wczytano zapisany wynik i historię epok.');
    } catch (error) {
        setHistoryStatus(`Nie udało się wczytać uruchomienia: ${error.message}`, true);
    }
}

async function runSingle(event) {
    event.preventDefault();
    if (!$('p2-form').reportValidity()) return;
    showStatus('Trwa obliczanie…');
    try {
        const response = await fetch('/api/p2/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload()) });
        if (!response.ok) throw new Error(await responseError(response));
        const data = await response.json();
        $('p2-seed').value = data.seed_exact;
        showResult(data.result, `Pojedyncze uruchomienie (seed ${data.seed_exact})`);
        showStatus('Obliczenia zakończone.', 'success');
        void refreshHistory();
    } catch (error) {
        showStatus(error.message, 'danger');
    }
}

async function runExperiment() {
    if (!$('p2-form').reportValidity()) return;
    showStatus('Trwa seria powtórzeń…');
    try {
        const response = await fetch('/api/p2/experiment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload(true)),
        });
        if (!response.ok) throw new Error(await responseError(response));
        const data = await response.json();
        $('p2-seed').value = data.seed_exact;
        const summary = data.summary;
        const averageError = summary.average_error === null
            ? 'Nie dotyczy — brak znanego optimum maksymalnego dla tego benchmarku.'
            : summary.average_error;
        const objectiveDirection = data.configuration.objective;
        const bestRun = data.runs.reduce((best, run) => objectiveDirection === 'minimize'
            ? (run.result.best_objective < best.result.best_objective ? run : best)
            : (run.result.best_objective > best.result.best_objective ? run : best));
        const runRows = data.runs.map((run, index) => `<tr><th scope="row">${index + 1}</th><td>${run.seed_exact}</td><td>${run.result.best_objective}</td><td>${formatSeconds(run.result.elapsed_seconds)}</td><td><code>${run.run_id}</code></td></tr>`).join('');
        $('p2-result').innerHTML = `<div class="card"><div class="card-body"><h2 class="h5">Eksperyment — ${data.repetitions} powtórzeń</h2><dl class="row"><dt class="col-sm-3">Identyfikator</dt><dd class="col-sm-9"><code>${data.experiment_id}</code></dd><dt class="col-sm-3">Seed bazowy</dt><dd class="col-sm-9">${data.seed_exact}</dd><dt class="col-sm-3">Średni wynik</dt><dd class="col-sm-9">${summary.average_objective}</dd><dt class="col-sm-3">Najlepszy wynik</dt><dd class="col-sm-9">${summary.best_objective}</dd><dt class="col-sm-3">Najgorszy wynik</dt><dd class="col-sm-9">${summary.worst_objective}</dd><dt class="col-sm-3">Średni błąd względem znanego optimum minimalizacyjnego</dt><dd class="col-sm-9">${averageError}</dd><dt class="col-sm-3">Średni czas obliczeń</dt><dd class="col-sm-9">${formatSeconds(summary.average_elapsed_seconds)}</dd></dl><h3 class="h6 mt-3">Użyta konfiguracja</h3>${formatExperimentConfiguration(data.configuration)}<h3 class="h6 mt-4">Wyniki powtórzeń</h3><div class="table-responsive"><table class="table table-sm table-striped"><thead><tr><th scope="col">#</th><th scope="col">Seed</th><th scope="col">Najlepszy wynik</th><th scope="col">Czas obliczeń</th><th scope="col">ID uruchomienia</th></tr></thead><tbody>${runRows}</tbody></table></div><p class="small text-muted mb-0">Wykresy poniżej pokazują najlepszy przebieg dla celu: ${objectiveDirection === 'minimize' ? 'minimalizacji' : 'maksymalizacji'}, seed ${bestRun.seed_exact} (uruchomienie ${bestRun.run_id}).</p></div></div>`;
        drawCharts(bestRun.result.history);
        showStatus('Eksperyment zakończony.', 'success');
        void refreshHistory();
    } catch (error) {
        showStatus(error.message, 'danger');
    }
}

async function compareRepresentations() {
    if (!$('p2-form').reportValidity()) return;
    showStatus('Porównywanie reprezentacji…');
    try {
        const response = await fetch('/api/p2/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload(true)),
        });
        if (!response.ok) throw new Error(await responseError(response));
        const data = await response.json();
        $('p2-result').innerHTML = `<div class="card"><div class="card-body"><h2 class="h5">Porównanie P1 i P2</h2><div class="table-responsive"><table class="table table-sm"><thead><tr><th>Reprezentacja</th><th>Średni wynik</th><th>Najlepszy wynik</th><th>Średni czas</th></tr></thead><tbody><tr><th>Binarna (P1)</th><td>${data.binary.average_objective}</td><td>${data.binary.best_objective}</td><td>${formatSeconds(data.binary.average_elapsed_seconds)}</td></tr><tr><th>Rzeczywista (P2)</th><td>${data.real.average_objective}</td><td>${data.real.best_objective}</td><td>${formatSeconds(data.real.average_elapsed_seconds)}</td></tr></tbody></table></div></div></div>`;
        showStatus('Porównanie zakończone.', 'success');
    } catch (error) {
        showStatus(error.message, 'danger');
    }
}

export async function mount() {
    benchmarks = await getJson('/p2/benchmarks');
    $('p2-function').innerHTML = benchmarks.map((item) => `<option value="${item.key}">${item.name}</option>`).join('');
    $('p2-function').addEventListener('change', refreshDimensions);
    $('p2-population').addEventListener('input', syncPopulationConstraints);
    $('p2-elite-mode').addEventListener('change', syncPopulationConstraints);
    for (const id of [
        'p2-crossover-enabled',
        'p2-mutation-enabled',
        'p2-elitism-enabled',
        'p2-crossover',
        'p2-selection',
        'p2-elite-mode',
    ]) {
        $(id).addEventListener('change', syncOperatorControls);
    }
    refreshDimensions();
    syncOperatorControls();
    syncPopulationConstraints();
    $('p2-form').addEventListener('submit', runSingle);
    $('p2-experiment').addEventListener('click', runExperiment);
    $('p2-compare').addEventListener('click', compareRepresentations);
    $('p2-history-refresh').addEventListener('click', refreshHistory);
    await refreshHistory();
}

