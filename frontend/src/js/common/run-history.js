import { downloadFile, getJson } from '../api.js';

export function listRuns(projectKey, limit = 50) {
    const query = new URLSearchParams({ limit: String(limit) });
    if (projectKey) {
        query.set('project_key', projectKey);
    }
    return getJson(`/runs?${query}`);
}

export function getRun(runId) {
    return getJson(`/runs/${encodeURIComponent(runId)}`);
}

export function listSavedCharts(runId) {
    return getJson(`/runs/${encodeURIComponent(runId)}/charts`);
}

export function downloadRunCsv(runId) {
    return downloadFile(`/runs/${encodeURIComponent(runId)}/export.csv`);
}

export function downloadSavedChart(runId, chartId) {
    return downloadFile(
        `/runs/${encodeURIComponent(runId)}/charts/${encodeURIComponent(chartId)}`,
    );
}
