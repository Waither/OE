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

## Projekt 4 — MealPy

Projekt 4 wykorzystuje algorytm Artificial Bee Colony z biblioteki MealPy.
W środowisku Python 3.14 MealPy 3.0.3 należy zainstalować bez wymuszania
starego NumPy, ponieważ jego metadane zależności nie uwzględniają jeszcze
NumPy 2.x:

```powershell
python -m pip install --no-deps mealpy==3.0.3
python -m pip install pandas
python p4_console.py --function ackley01 --dimensions 5
```
