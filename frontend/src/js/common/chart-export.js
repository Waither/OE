import { postBlob } from '../api.js';

export function chartToPng(chart) {
    return new Promise((resolve, reject) => {
        chart.canvas.toBlob((blob) => {
            if (blob === null) {
                reject(new Error('Nie udało się wyeksportować wykresu jako PNG.'));
                return;
            }
            resolve(blob);
        }, 'image/png');
    });
}

export async function saveChartPng(chart, runId, name) {
    const png = await chartToPng(chart);
    const query = new URLSearchParams({ name });
    return postBlob(`/runs/${encodeURIComponent(runId)}/charts?${query}`, png);
}

export async function downloadChartPng(chart, filename) {
    const png = await chartToPng(chart);
    const objectUrl = URL.createObjectURL(png);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}
