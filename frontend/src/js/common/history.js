import Chart from 'chart.js/auto';
import { chartToPng, downloadChartPng } from './chart-export.js';
import { deleteJson, downloadFile, getJson, postBlob } from '../api.js';

const $ = (id) => document.querySelector(`#${id}`);
const PROJECT_NAMES = {
    p1: 'Projekt 1',
    p2: 'Projekt 2',
    p3: 'Projekt 3',
    p4: 'Projekt 4',
};
const METRICS = {
    best: 'Najlepsza wartość',
    worst: 'Najgorsza wartość',
    mean: 'Średnia populacji',
    standard_deviation: 'Odchylenie standardowe',
};
const METRIC_OPTIONS = [
    ['best', 'Najlepsza wartość epoki'],
    ['worst', 'Najgorsza wartość epoki'],
    ['mean', 'Średnia populacji'],
    ['standard_deviation', 'Odchylenie standardowe'],
];

let runs = [];
let comparisons = [];
let chart;

function selectedRunIds() {
    return new Set(
        [...document.querySelectorAll('[data-history-run]:checked')]
            .map((checkbox) => checkbox.value),
    );
}

function setStatus(message, isError = false) {
    const status = $('history-status');
    status.textContent = message;
    status.classList.toggle('text-danger', isError);
    status.classList.toggle('text-muted', !isError);
}

function cell(text) {
    const element = document.createElement('td');
    element.textContent = text;
    return element;
}

function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;

    const datePart = date.toLocaleDateString('pl-PL');
    const timePart = date.toLocaleTimeString('pl-PL', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hourCycle: 'h23',
    });
    const milliseconds = String(date.getMilliseconds()).padStart(3, '0');
    return `${datePart} ${timePart}.${milliseconds}`;
}

function formatSeconds(value) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
    if (value < 1) return `${(value * 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })} ms`;
    return `${value.toLocaleString(undefined, { maximumFractionDigits: 3 })} s`;
}

function formatProbability(value) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
    return `${(value * 100).toLocaleString('pl-PL', { maximumFractionDigits: 2 })}%`;
}

function formatConfiguration(parameters) {
    const selectionNames = {
        tournament: 'Turniej',
        best: 'Najlepsi',
        worst: 'Najgorsi',
        roulette: 'Ruletka',
    };
    const crossoverNames = {
        one_point: '1 punkt',
        two_point: '2 punkty',
        single_point: '1 punkt',
        two_points: '2 punkty',
        uniform: 'Jednorodne',
        grain: 'Ziarniste',
        arithmetic: 'Arytmetyczne',
        linear: 'Linearne',
        blend_alpha: 'Mieszające alfa',
        blend_alpha_beta: 'Mieszające alfa i beta',
        average: 'Uśredniające',
    };
    const mutationNames = {
        boundary: 'Brzegowa',
        one_point: '1 bit',
        two_point: '2 bity',
        random: 'Losowa',
        swap: 'Zamiana indeksów',
        gaussian: 'Gaussa',
    };

    const selectionKey = parameters.selection ?? parameters.parent_selection_type;
    const crossoverKey = parameters.crossover ?? parameters.crossover_type;
    const mutationKey = parameters.mutation ?? parameters.mutation_type;
    const selectionName = selectionNames[selectionKey] ?? selectionKey ?? '—';
    const selection = selectionKey === 'tournament'
        ? `${selectionName} (${parameters.tournament_size ?? parameters.K_tournament ?? '—'})`
        : selectionName;
    const crossoverName = crossoverNames[crossoverKey] ?? crossoverKey ?? '—';
    const crossover = parameters.crossover_probability > 0
        ? `${crossoverName} · ${formatProbability(parameters.crossover_probability)}`
        : 'Wył.';
    const mutationName = mutationNames[mutationKey] ?? mutationKey ?? '—';
    const mutation = parameters.mutation_probability > 0
        ? `${mutationName} · ${formatProbability(parameters.mutation_probability)}`
        : 'Wył.';
    const inversion = parameters.inversion_probability > 0
        ? formatProbability(parameters.inversion_probability)
        : 'Wył.';
    let elitism = 'Wył.';
    const eliteValue = parameters.elite_value ?? parameters.keep_elitism ?? 0;
    if (eliteValue > 0 && parameters.elite_mode === 'percentage') {
        elitism = formatProbability(parameters.elite_value / 100);
    } else if (eliteValue > 0) {
        elitism = `${eliteValue} os.`;
    }

    return { selection, crossover, mutation, inversion, elitism };
}

function configurationCell(value, description) {
    const element = cell(value);
    element.title = description;
    return element;
}

function supportsEpochMetrics() {
    return ['p1', 'p2', 'p3', 'p4'].includes($('history-project').value);
}

function renderProjectControls() {
    const hasMetrics = supportsEpochMetrics();
    const metricSelect = $('history-metric');
    const selectedMetric = metricSelect.value;
    metricSelect.replaceChildren();
    if (hasMetrics) {
        for (const [value, label] of METRIC_OPTIONS) {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            metricSelect.append(option);
        }
        metricSelect.value = METRIC_OPTIONS.some(([value]) => value === selectedMetric)
            ? selectedMetric
            : METRIC_OPTIONS[0][0];
        metricSelect.disabled = false;
    } else {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Brak metryk dla tego projektu';
        metricSelect.append(option);
        metricSelect.disabled = true;
    }

    $('history-chart-section').classList.toggle('d-none', !hasMetrics);
    $('history-comparisons-section').classList.toggle('d-none', !hasMetrics);
    $('history-selection-actions').classList.toggle('d-none', !hasMetrics);
    renderRunHeadings(hasMetrics);
}

function renderRunHeadings(hasMetrics) {
    const headings = hasMetrics
        ? ['', 'Data', 'Funkcja', 'Wymiary', 'Seed', 'Wynik', 'Czas', 'Selekcja', 'Krzyżowanie', 'Mutacja', 'Inwersja', 'Elityzm']
        : ['Data', 'Seed', 'Wersja algorytmu', 'Parametry zapisane', 'Wynik zapisany'];
    const row = $('history-runs-heading-row');
    row.replaceChildren();
    for (const heading of headings) {
        const cellElement = document.createElement('th');
        cellElement.scope = 'col';
        cellElement.textContent = heading;
        row.append(cellElement);
    }
}

function jsonDetails(value, label) {
    const element = document.createElement('td');
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    const content = document.createElement('pre');
    const serialized = JSON.stringify(value, null, 2);

    summary.textContent = label;
    content.className = 'small mt-2 mb-0';
    content.style.whiteSpace = 'pre-wrap';
    content.style.overflowWrap = 'anywhere';
    content.textContent = serialized ?? String(value);
    details.append(summary, content);
    element.append(details);
    return element;
}

function renderRuns() {
    const body = $('history-runs');
    body.replaceChildren();
    const hasMetrics = supportsEpochMetrics();

    for (const run of runs) {
        const parameters = run.parameters ?? {};
        const result = run.result_data ?? {};
        const row = document.createElement('tr');

        if (!hasMetrics) {
            const parameterCount = Object.keys(parameters).length;
            const resultCount = result && typeof result === 'object' ? Object.keys(result).length : 0;
            row.append(
                cell(formatDate(run.created_at)),
                cell(String(run.seed)),
                cell(String(run.algorithm_version ?? '—')),
                jsonDetails(parameters, `${parameterCount} parametrów`),
                jsonDetails(result, `${resultCount} pól wyniku`),
            );
            body.append(row);
            continue;
        }

        const configuration = formatConfiguration(parameters);
        const selectionCell = document.createElement('td');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input';
        checkbox.value = run.id;
        checkbox.dataset.historyRun = '';
        checkbox.setAttribute('aria-label', `Porównaj uruchomienie z ${formatDate(run.created_at)}`);
        checkbox.addEventListener('change', renderChart);
        selectionCell.append(checkbox);

            row.append(
            selectionCell,
            cell(formatDate(run.created_at)),
            cell(String(parameters.function_key ?? '—')),
            cell(String(parameters.dimensions ?? '—')),
            cell(String(run.seed)),
            cell(typeof result.best_objective === 'number' ? result.best_objective.toLocaleString() : '—'),
            cell(formatSeconds(result.elapsed_seconds)),
            configurationCell(configuration.selection, `Selekcja: ${configuration.selection}`),
            configurationCell(configuration.crossover, (parameters.crossover ?? parameters.crossover_type) === 'grain'
                ? `Krzyżowanie ziarniste; prawdopodobieństwo krzyżowania ${formatProbability(parameters.crossover_probability)}, zamiana bitu ${formatProbability(parameters.grain_probability)}`
                : `Krzyżowanie: ${configuration.crossover}`),
            configurationCell(configuration.mutation, `Mutacja: ${configuration.mutation}`),
            configurationCell(configuration.inversion, `Inwersja: ${configuration.inversion}`),
            configurationCell(configuration.elitism, `Elityzm: ${configuration.elitism}`),
        );
        body.append(row);
    }
}

function renderChart() {
    if (!supportsEpochMetrics()) {
        chart?.destroy();
        chart = undefined;
        return;
    }

    const selected = selectedRunIds();
    const selectedRuns = runs.filter((run) => selected.has(run.id));
    const metric = $('history-metric').value;
    const maxEpochs = Math.max(0, ...selectedRuns.map((run) => run.result_data?.history?.length ?? 0));
    const labels = Array.from({ length: maxEpochs }, (_, index) => index);

    chart?.destroy();
    chart = undefined;
    $('history-selected-count').textContent = `${selectedRuns.length} wybranych`;
    $('history-download-chart').disabled = selectedRuns.length === 0;
    $('history-save-comparison').disabled = selectedRuns.length < 2;
    $('history-chart-empty').classList.toggle('d-none', selectedRuns.length > 0);
    if (!selectedRuns.length) return;

    chart = new Chart($('history-chart'), {
        type: 'line',
        data: {
            labels,
            datasets: selectedRuns.map((run, index) => {
                const history = run.result_data?.history ?? [];
                const hue = (index * 137.508) % 360;
                return {
                    label: formatDate(run.created_at),
                    data: history.map((epoch) => epoch[metric]),
                    borderColor: `hsl(${hue} 65% 42%)`,
                    backgroundColor: `hsl(${hue} 65% 42%)`,
                    pointRadius: history.length > 150 ? 0 : 2,
                    borderWidth: 2,
                    tension: 0.15,
                    spanGaps: false,
                };
            }),
        },
        options: {
            maintainAspectRatio: false,
            interaction: { mode: 'nearest', intersect: false },
            plugins: {
                legend: { position: 'bottom' },
                title: { display: true, text: METRICS[metric] },
                tooltip: { mode: 'index', intersect: false },
            },
            scales: {
                x: { title: { display: true, text: 'Epoka' } },
                y: { title: { display: true, text: METRICS[metric] } },
            },
        },
    });
}

function renderComparisons() {
    const body = $('history-comparisons');
    body.replaceChildren();
    for (const comparison of comparisons) {
        const row = document.createElement('tr');
        const runDates = comparison.run_ids
            .map((runId) => runs.find((run) => run.id === runId))
            .filter(Boolean)
            .map((run) => formatDate(run.created_at))
            .join(', ');
        const actions = document.createElement('td');

        const loadButton = document.createElement('button');
        loadButton.type = 'button';
        loadButton.className = 'btn btn-sm btn-outline-primary me-2';
        loadButton.textContent = 'Wczytaj';
        loadButton.addEventListener('click', () => void loadComparison(comparison));

        const downloadButton = document.createElement('button');
        downloadButton.type = 'button';
        downloadButton.className = 'btn btn-sm btn-outline-secondary';
        downloadButton.textContent = 'Pobierz PNG';
        downloadButton.addEventListener('click', () => {
            downloadFile(`/runs/comparisons/${encodeURIComponent(comparison.id)}/image`)
                .catch((error) => setComparisonStatus(error.message, true));
        });

        actions.append(loadButton, downloadButton);
        row.append(
            cell(formatDate(comparison.created_at)),
            cell(METRICS[comparison.metric] ?? comparison.metric),
            cell(runDates || `${comparison.run_ids.length} uruchomień`),
            actions,
        );
        body.append(row);
    }
    setComparisonStatus(comparisons.length
        ? `Zapisano porównań: ${comparisons.length}.`
        : 'Brak zapisanych porównań.');
}

function setComparisonStatus(message, isError = false) {
    const status = $('history-comparisons-status');
    status.textContent = message;
    status.classList.toggle('text-danger', isError);
    status.classList.toggle('text-muted', !isError);
}

async function refreshComparisons() {
    if (!supportsEpochMetrics()) {
        comparisons = [];
        renderComparisons();
        return;
    }

    setComparisonStatus('Wczytywanie zapisanych porównań…');
    try {
        const projectKey = $('history-project').value;
        comparisons = await getJson(`/runs/comparisons?project_key=${encodeURIComponent(projectKey)}&limit=50`);
        renderComparisons();
    } catch (error) {
        comparisons = [];
        renderComparisons();
        setComparisonStatus(`Nie udało się wczytać zapisanych porównań: ${error.message}`, true);
    }
}

async function saveComparison() {
    if (!supportsEpochMetrics()) return;
    const selectedRuns = runs.filter((run) => selectedRunIds().has(run.id));
    if (selectedRuns.length < 2 || !chart) return;

    const button = $('history-save-comparison');
    button.disabled = true;
    setStatus('Zapisywanie porównania…');
    try {
        const image = await chartToPng(chart);
        const query = new URLSearchParams({
            project_key: $('history-project').value,
            metric: $('history-metric').value,
        });
        for (const run of selectedRuns) query.append('run_ids', run.id);
        await postBlob(`/runs/comparisons?${query}`, image);
        await refreshComparisons();
        setStatus('Porównanie wraz z wykresem PNG zostało zapisane.');
    } catch (error) {
        setStatus(`Nie udało się zapisać porównania: ${error.message}`, true);
    } finally {
        renderChart();
    }
}

async function loadComparison(comparison) {
    setComparisonStatus('Wczytywanie zapisanego porównania…');
    try {
        const existingIds = new Set(runs.map((run) => run.id));
        const missingRuns = await Promise.all(
            comparison.run_ids
                .filter((runId) => !existingIds.has(runId))
                .map((runId) => getJson(`/runs/${encodeURIComponent(runId)}`)),
        );
        runs = [...runs, ...missingRuns];
        renderRuns();
        $('history-metric').value = comparison.metric;
        document.querySelectorAll('[data-history-run]').forEach((checkbox) => {
            checkbox.checked = comparison.run_ids.includes(checkbox.value);
        });
        renderChart();
        setComparisonStatus('Wczytano zapisane porównanie.');
        $('history-chart-heading').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        setComparisonStatus(`Nie udało się wczytać porównania: ${error.message}`, true);
    }
}

async function refreshRuns() {
    renderProjectControls();
    setStatus('Wczytywanie zapisanych uruchomień…');
    try {
        const projectKey = $('history-project').value;
        runs = await getJson(`/runs?project_key=${encodeURIComponent(projectKey)}&limit=200`);
        renderRuns();
        renderChart();
        await refreshComparisons();
        setStatus(runs.length
            ? `Wczytano ${runs.length} uruchomień projektu ${PROJECT_NAMES[projectKey]}.`
            : `Brak zapisanych uruchomień dla ${PROJECT_NAMES[projectKey]}.`);
    } catch (error) {
        runs = [];
        renderRuns();
        renderChart();
        comparisons = [];
        renderComparisons();
        setStatus(`Nie udało się wczytać historii: ${error.message}`, true);
    }
}

async function clearProjectHistory() {
    const projectKey = $('history-project').value;
    const projectName = PROJECT_NAMES[projectKey];
    const confirmed = window.confirm(
        `Czy na pewno usunąć wszystkie zapisane uruchomienia projektu ${projectName} oraz powiązane z nimi wykresy? Tej operacji nie można cofnąć.`,
    );
    if (!confirmed) return;

    const button = $('history-clear-project');
    button.disabled = true;
    setStatus(`Usuwanie historii ${projectName}…`);
    try {
        const result = await deleteJson(`/runs/project/${encodeURIComponent(projectKey)}`);
        runs = [];
        comparisons = [];
        renderRuns();
        renderChart();
        renderComparisons();
        setStatus(`Usunięto ${result.deleted_runs} uruchomień projektu ${projectName}.`);
    } catch (error) {
        setStatus(`Nie udało się wyczyścić historii: ${error.message}`, true);
    } finally {
        button.disabled = false;
    }
}

export async function mount() {
    $('history-project').addEventListener('change', () => {
        runs = [];
        comparisons = [];
        renderRuns();
        renderChart();
        renderComparisons();
        void refreshRuns();
    });
    $('history-metric').addEventListener('change', renderChart);
    $('history-refresh').addEventListener('click', refreshRuns);
    $('history-clear-project').addEventListener('click', clearProjectHistory);
    $('history-download-chart').addEventListener('click', async () => {
        if (!chart) return;
        try {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            await downloadChartPng(chart, `porownanie-${timestamp}.png`);
        } catch (error) {
            setStatus(`Nie udało się pobrać wykresu: ${error.message}`, true);
        }
    });
    $('history-save-comparison').addEventListener('click', saveComparison);
    $('history-refresh-comparisons').addEventListener('click', refreshComparisons);
    $('history-select-all').addEventListener('click', () => {
        document.querySelectorAll('[data-history-run]').forEach((checkbox) => {
            checkbox.checked = true;
        });
        renderChart();
    });
    $('history-clear').addEventListener('click', () => {
        document.querySelectorAll('[data-history-run]').forEach((checkbox) => {
            checkbox.checked = false;
        });
        renderChart();
    });
    await refreshRuns();
}
