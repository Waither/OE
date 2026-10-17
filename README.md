# OE

## Wymagania

- Python 3.10 lub nowszy
- Node.js 18 lub nowszy i npm

## Uruchomienie w trybie developerskim

W pierwszym terminalu, w katalogu głównym repozytorium:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

W drugim terminalu:

```powershell
cd frontend
npm install
npm run dev
```

Otwórz adres podany przez Vite (domyślnie `http://localhost:5173`). Jedna
strona `index.html` zawiera wspólną nawigację i `<main>`. Router frontendu
zmienia zawartość `<main>` dla adresów `/`, `/1`, `/2`, `/3` i `/4`, bez
przeładowania całej strony. Zapytania `/api` Vite przekazuje do FastAPI
działającego na porcie 8000.

## Budowanie frontendu

W katalogu `frontend` uruchom:

```powershell
npm run build
```

Po zbudowaniu frontend jest dostępny z FastAPI pod `/`, `/1`, `/2`, `/3` i
`/4`; każde z tych adresów zwraca ten sam szkielet, a router w przeglądarce
wstawia właściwą zawartość do `<main>`. Dokumentacja API znajduje się pod
`/docs`.

Plik bazy SQLite zostanie utworzony pod `backend/data/app.db` przy pierwszym
starcie backendu. Przy starcie aplikacji SQLAlchemy
utworzy tabele bazowych modeli: historię uruchomień i metadane zapisanych
wykresów. Szczegółowy format wyników poszczególnych projektów pozostaje JSON-em,
aż wymagania P1–P4 określą dokładniejszy model danych.

Wspólne endpointy historii:

- `GET /api/runs?project_key=p1&limit=50` — lista zapisanych uruchomień;
- `GET /api/runs/{id}` — parametry, seed i wynik;
- `GET /api/runs/{id}/export.csv` — CSV z metadanymi i wynikiem;
- `POST /api/runs/{id}/charts?name=...` — zapis wykresu PNG wysłanego z frontendu;
- `GET /api/runs/{id}/charts` — lista wykresów zapisanych dla uruchomienia;
- `GET /api/runs/{id}/charts/{chart_id}` — pobranie zapisanego PNG.

Logika każdego projektu powinna korzystać ze wspólnego
`create_random_generator()` i `create_run()`, by zapisać seed, parametry oraz
wynik. `create_csv()` koduje rekordy CSV, a `saveChartPng()` wysyła obraz
Chart.js do backendu. Każdy projekt nadal sam określa swoje parametry,
obliczenia i dane wynikowe.

Tworzenie tabel przez `create_all()` jest wystarczające dla obecnego prototypu.
Gdy schemat zacznie ewoluować, przed pracą na wspólnej bazie należy dodać
migracje Alembic.

Każdy developer ma własny lokalny plik bazy, ignorowany przez Git. Kod,
zależności i struktura tabel są wspólne w repozytorium; historię uruchomień
można wymieniać przez eksport CSV, a artefakty PNG pozostają lokalnymi plikami.
