const byId = (id) => document.getElementById(id);
const form = byId('p4-form');

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
        byId('p4-result').innerHTML = `<div class="card"><div class="card-body"><h2 class="h5">Wynik ABC</h2><dl class="row mb-0"><dt class="col-sm-5">Średnia wartość funkcji</dt><dd class="col-sm-7">${result.summary.average_objective.toFixed(6)}</dd><dt class="col-sm-5">Najlepszy wynik</dt><dd class="col-sm-7">${result.summary.best_objective.toFixed(6)}</dd><dt class="col-sm-5">Liczba powtórzeń</dt><dd class="col-sm-7">${result.repetitions}</dd></dl></div></div>`;
        byId('p4-status').textContent = 'Gotowe';
    } catch (error) { byId('p4-status').textContent = `Błąd: ${error.message}`; }
});
