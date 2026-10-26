const $ = (id) => document.getElementById(id);
const form = $('p3-form');

const binaryCrossovers = [['single_point', 'Jednopunktowe'], ['two_points', 'Dwupunktowe'], ['uniform', 'Jednorodne']];
const realCrossovers = [
    ['single_point', 'Jednopunktowe'], ['two_points', 'Dwupunktowe'], ['uniform', 'Jednorodne'],
    ['arithmetic', 'Arytmetyczne'], ['blend_alpha', 'Mieszające alfa (BLX-α)'],
    ['blend_alpha_beta', 'Mieszające alfa i beta (BLX-αβ)'], ['average', 'Uśredniające'],
];

function updateRepresentationOptions() {
    const real = $('p3-representation').value === 'real';
    const crossover = $('p3-crossover');
    const selectedCrossover = crossover.value;
    const options = real ? realCrossovers : binaryCrossovers;
    crossover.innerHTML = options.map(([value, label]) => `<option value="${value}">${label}</option>`).join('');
    crossover.value = options.some(([value]) => value === selectedCrossover) ? selectedCrossover : 'single_point';
    $('p3-lower-bound-field').classList.toggle('d-none', !real);
    $('p3-upper-bound-field').classList.toggle('d-none', !real);
    const mutation = $('p3-mutation');
    const mutationOptions = real ? [['random', 'Losowa'], ['gaussian', 'Gaussa']] : [['random', 'Losowa'], ['swap', 'Zamiana indeksów']];
    const selectedMutation = mutation.value;
    mutation.innerHTML = mutationOptions.map(([value, label]) => `<option value="${value}">${label}</option>`).join('');
    mutation.value = mutationOptions.some(([value]) => value === selectedMutation) ? selectedMutation : 'random';
}

function config() {
    const population = Number($('p3-population').value);
    return {
        function_key: $('p3-function').value,
        representation: $('p3-representation').value,
        dimensions: Number($('p3-dimensions').value),
        num_genes: Number($('p3-genes').value),
        num_generations: Number($('p3-generations').value),
        sol_per_pop: population,
        num_parents_mating: Math.max(2, Math.floor(population / 2)),
        lower_bound: Number($('p3-lower-bound').value),
        upper_bound: Number($('p3-upper-bound').value),
        parent_selection_type: $('p3-selection').value,
        crossover_type: $('p3-crossover').value,
        mutation_type: $('p3-mutation').value,
        repetitions: Number($('p3-repetitions').value),
    };
}

function show(result) {
    const summary = result.summary;
    $('p3-result').innerHTML = `<div class="card"><div class="card-body"><h2 class="h5">Wynik eksperymentu</h2><dl class="row mb-0"><dt class="col-sm-5">Średnia wartość funkcji</dt><dd class="col-sm-7">${summary.average_objective.toFixed(6)}</dd><dt class="col-sm-5">Najlepszy wynik</dt><dd class="col-sm-7">${summary.best_objective.toFixed(6)}</dd><dt class="col-sm-5">Liczba uruchomień</dt><dd class="col-sm-7">${result.repetitions}</dd></dl></div></div>`;
}

form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    $('p3-status').textContent = 'Obliczenia…';
    try {
        const response = await fetch('/api/p3/experiment', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config()) });
        if (!response.ok) throw new Error(await response.text());
        show(await response.json());
        $('p3-status').textContent = 'Gotowe';
    } catch (error) {
        $('p3-status').textContent = `Błąd: ${error.message}`;
    }
});

$('p3-representation')?.addEventListener('change', updateRepresentationOptions);
updateRepresentationOptions();
