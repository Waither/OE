# Krótkie sprawozdanie — Projekt 1

Sprawozdanie ma krótko wyjaśniać **co robi aplikacja, jak przepływają dane
i jakie są wyniki badań**. Wystarczy kilka konkretnych rozdziałów — bez
opisywania każdej linijki kodu i każdego operatora osobno. Uzupełnij
rzeczywistymi wynikami z aplikacji; nie wpisuj przykładowych lub
wymyślonych liczb.

## 1. Cel i działanie aplikacji

W 1–2 akapitach napisz, że aplikacja uruchamia binarny algorytm genetyczny
do minimalizacji lub maksymalizacji wybranej funkcji wielu zmiennych.
Wymień badane benchmarki, wymiary oraz porównywane ustawienia.

Krótko opisz algorytm: program tworzy populację, ocenia osobniki, wybiera
rodziców i stosuje krzyżowanie, mutację, opcjonalną inwersję oraz elityzm.
Proces powtarza się przez zadaną liczbę epok, po czym aplikacja pokazuje
najlepsze rozwiązanie i wykresy.

## 2. Przepływ danych

Pokaż ten przepływ w kilku zdaniach lub jako prosty schemat:

**Formularz w przeglądarce** → konfiguracja JSON → **FastAPI** → algorytm
i benchmark z `opfunu` → wynik, statystyki epok i seedy → zapis w **SQLite**
→ odpowiedź do interfejsu → wykresy, podsumowanie i historia.

Przy eksperymencie backend uruchamia algorytm wielokrotnie z osobnymi
seedami. Zapisuje każdy przebieg z parametrami i wspólnym identyfikatorem
eksperymentu. Interfejs zestawia wyniki i pokazuje wykres najlepszego
przebiegu. Eksport CSV pozwala pobrać dane do dalszej analizy.

**Rysunek 1.** *Formularz P1 oraz wynik eksperymentu z tabelą powtórzeń.*
Wstaw jeden czytelny zrzut ekranu aplikacji.

## 3. Badania i wyniki

Opisz krótko plan testów: funkcja, wymiar, kierunek optymalizacji,
konfiguracja, liczba epok i powtórzeń. Dla porównania zmieniaj najlepiej
jeden parametr naraz, a pozostałe pozostaw takie same. Wykonaj co najmniej
10 powtórzeń każdej porównywanej konfiguracji; zapisz seed bazowy.

Wstaw jedną krótką tabelę:

| Funkcja / wymiar | Konfiguracja | Powtórzenia | Średni wynik | Najlepszy | Najgorszy | Średni czas | Błąd od minimum |
|---|---|---:|---:|---:|---:|---:|---:|
| [uzupełnij] | [uzupełnij] | [min. 10] | [ ] | [ ] | [ ] | [ ] | [ ] |

Podaj, że dla minimalizacji najlepszy wynik jest najmniejszy, a dla
maksymalizacji — największy. Błąd licz tylko względem znanego minimum;
przy maksymalizacji wpisz „nie dotyczy — brak znanego maksimum”.

Wstaw wykresy z jednego uruchomienia, podpisując funkcję, wymiar i seed:

- **Rysunek 2.** *Najlepsza i najgorsza wartość funkcji w kolejnych epokach.*
- **Rysunek 3.** *Średnia i odchylenie standardowe populacji w kolejnych epokach.*

Dodaj krótki komentarz do wyników: która konfiguracja wypadła lepiej,
jak zmienił się czas i czy wyniki powtórzeń były podobne. Wnioski oprzyj
na tabeli, nie na pojedynczym wykresie.

## 4. Podsumowanie

W kilku zdaniach odpowiedz, czy cel został osiągnięty, co pokazały badania
i jakie ustawienia sprawdziły się najlepiej. Zaznacz ograniczenia, np.
liczbę testowanych konfiguracji lub epok. Nie twierdź, że algorytm zawsze
znajduje optimum, jeśli wyniki tego nie potwierdzają.

Na końcu podaj źródła benchmarków i użytych bibliotek. Eksporty CSV,
dodatkowe tabele i nagranie demonstracyjne można dołączyć jako załączniki.
