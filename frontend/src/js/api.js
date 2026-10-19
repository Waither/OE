const API_BASE_URL = '/api';

async function ensureSuccess(response) {
    if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Żądanie API nie powiodło się (${response.status}).`);
    }
    return response;
}

export async function getJson(path) {
    const response = await ensureSuccess(await fetch(`${API_BASE_URL}${path}`, {
        headers: { Accept: 'application/json' },
    }));

    return response.json();
}

export async function postBlob(path, blob) {
    const response = await ensureSuccess(await fetch(`${API_BASE_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': blob.type },
        body: blob,
    }));

    return response.json();
}

export async function deleteJson(path) {
    const response = await ensureSuccess(await fetch(`${API_BASE_URL}${path}`, {
        method: 'DELETE',
        headers: { Accept: 'application/json' },
    }));

    return response.json();
}

export async function downloadFile(path) {
    const response = await ensureSuccess(await fetch(`${API_BASE_URL}${path}`));
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') ?? '';
    const filename = disposition.match(/filename="([^"]+)"/)?.[1] ?? 'download';
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}