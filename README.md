# Uruchomienie aplikacji

## Wymagania

- Windows 10/11
- Python 3.10 lub nowszy
- Node.js 18 lub nowszy z npm

## Tryb developerski

Otwórz dwa terminale w katalogu głównym repozytorium.

W pierwszym utwórz środowisko Pythona, zainstaluj zależności i uruchom backend:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

W drugim zainstaluj zależności frontendu i uruchom serwer developerski:

```powershell
cd frontend
npm install
npm run dev
```

Otwórz adres wyświetlony przez Vite, zwykle <http://localhost:5173>.
Pozostaw oba terminale uruchomione, gdy korzystasz z aplikacji.

## Uruchomienie zbudowanej aplikacji

Zbuduj frontend z katalogu `frontend`:

```powershell
npm install
npm run build
```

Następnie, z katalogu głównego repozytorium, uruchom backend:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app
```

Otwórz <http://localhost:8000>. Backend utworzy lokalną bazę SQLite przy
pierwszym uruchomieniu.
