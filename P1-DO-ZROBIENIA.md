# Projekt 1 — plan dokończenia

Lista porządkuje prace na podstawie wymagań z [pdf/P1.pdf](./pdf/P1.pdf),
aktualnego kodu i dokumentacji. Najpierw są decyzje, które wpływają na
zachowanie aplikacji; później poprawki kodu, weryfikacja i materiały do
oddania.

## 1. Decyzje do zamknięcia przed zmianami

- [ ] **Ustalić, co oznacza „dokładność” chromosomu.** Formularz w
  `frontend/views/P1.html` mówi „Dokładność (bity)”, ale `precision` w
  `backend/projects/p1/logic.py` jest liczbą cyfr po przecinku, a liczbę bitów
  genu algorytm wylicza automatycznie.
  - [ ] Sprawdzić dokładne sformułowanie wymagania w PDF.
  - [ ] Jeśli wymagane są bity — zmienić nazwę parametru, walidację oraz
    `BinaryChromosome`, tak aby użytkownik rzeczywiście ustalał liczbę bitów.
  - [ ] Jeśli wymagana jest precyzja dziesiętna — zostawić obecne kodowanie
    i poprawić etykietę, opis, walidację oraz dokumentację na „liczbę cyfr
    dokładności dziesiętnej”.
  - [ ] Zdecydować, czy obecna granica 1–24 ma pozostać; duża liczba bitów
    może istotnie zwiększyć koszt obliczeń.
- [ ] **Ustalić regułę dla liczby powtórzeń eksperymentu.** Wymaganie
  sprawozdania mówi o co najmniej 10 uruchomieniach na porównywaną
  konfigurację, natomiast endpoint i formularz dopuszczają 1.
  - [ ] Wybrać: wymusić minimum 10 dla endpointu eksperymentu albo zachować
    krótkie serie do testów i wyraźnie oznaczać serie krótsze niż 10 jako
    nieprzeznaczone do raportowania.
  - [ ] Zsynchronizować walidację backendu, ograniczenia formularza i opis
    przycisku/parametru.
- [ ] **Uzgodnić znaczenie „najlepszego” i „najgorszego” przebiegu** dla
  minimalizacji i maksymalizacji. Podsumowanie eksperymentu uwzględnia cel,
  ale statystyki epoki w `logic.py` obecnie zapisują minimum jako `best`
  i maksimum jako `worst` niezależnie od celu. Przy maksymalizacji trzeba
  odwrócić tę interpretację albo nazwać statystyki neutralnie (minimum/
  maksimum).

## 2. Prace w kodzie — kolejność realizacji

### Etap A — spójność parametrów i benchmarków

- [ ] Wdrożyć decyzję dotyczącą precyzji w formularzu, API, modelu
  `GAConfig`, kodowaniu chromosomu, historii zapisanych parametrów i README.
- [ ] Sprawdzić wspólną spójność benchmarków między implementacją,
  endpointem `/api/p1/benchmarks`, formularzem i dokumentacją:
  - [ ] Ackley01: zakres, dozwolone wymiary i optimum.
  - [ ] CEC 2014 F1: dozwolone wymiary, zakres, optimum oraz argumenty
    optimum dla każdego wymiaru.
  - [ ] Usunąć rozbieżność: README podaje Ackley dla 1–30 wymiarów,
    a implementacja aktualnie dopuszcza 2–30.
  - [ ] Potwierdzić, czy dla maksymalizacji optimum referencyjne ma być
    identyczne; jeśli tak, opisać sens maksymalizacji funkcji benchmarkowej.
- [ ] Upewnić się, że etykiety „najlepszy/najgorszy” w danych historii epok,
  wykresach i tabelach mają znaczenie zgodne z wybranym celem.

### Etap B — testy logiki algorytmu

- [ ] Rozbudować `tests/test_p1_logic.py`; testować zachowanie na ustalonych
  danych i seedach, nie tylko to, że algorytm kończy pracę.
- [ ] Kodowanie chromosomu:
  - [ ] poprawna długość chromosomu i liczba bitów na zmienną;
  - [ ] dekodowanie wartości skrajnych dziedziny i wartości pośredniej;
  - [ ] odtworzenie wartości z tolerancją wynikającą z dokładności;
  - [ ] odrzucanie złej liczby zmiennych, bitów spoza 0/1 i wartości poza
    dziedziną.
- [ ] Selekcja: sprawdzić wszystkie metody (`best`, `worst`, `roulette`,
  `tournament`), oba cele, przypadek jednakowych fitnessów oraz graniczne
  rozmiary turnieju.
- [ ] Krzyżowanie: sprawdzić każdy wariant, długość i poprawność potomków,
  prawdopodobieństwo 0 i 1 oraz chromosomy krótsze niż wymagane punkty
  cięcia.
- [ ] Mutacja i inwersja: sprawdzić każdy wariant, zachowanie długości,
  prawdopodobieństwo 0 i 1 oraz krótkie chromosomy.
- [ ] Elityzm: sprawdzić tryb liczbowy i procentowy, zaokrąglanie,
  wyłączenie elityzmu, oba cele i zachowanie najlepszego osobnika między
  epokami.
- [ ] Statystyki: sprawdzić średnią, odchylenie standardowe oraz interpretację
  najlepszego/najgorszego wyniku dla minimalizacji i maksymalizacji.
- [ ] Powtarzalność: ten sam seed i konfiguracja powinny dawać te same
  wartości, wynik i historię epok. Czas wykonania nie musi być identyczny.
- [ ] Walidacja konfiguracji: błędny benchmark/wymiar, nieparzysta lub za
  mała populacja, niedozwolone parametry operatorów i wartości poza zakresem
  powinny zwracać czytelny błąd.

### Etap C — API i eksperymenty powtórzeniowe

- [ ] Dodać testy endpointów P1 dla listy benchmarków, pojedynczego
  uruchomienia, eksperymentu i walidacji błędnych danych.
- [ ] Sprawdzić, czy pojedyncze uruchomienie zapisuje w historii parametry,
  seed i kompletny wynik wraz z historią epok.
- [ ] Sprawdzić, czy seria eksperymentu generuje i zapisuje odrębny seed dla
  każdego uruchomienia, a seed bazowy pozwala odtworzyć całą serię.
- [ ] Dodać testy statystyk eksperymentu: średni, najlepszy i najgorszy
  wynik, średni błąd od optimum i czasy. Dopilnować właściwej kolejności
  najlepszego/najgorszego wyniku dla obu celów.
- [ ] Rozstrzygnąć, czy w podsumowaniu potrzebne są także minimum i maksimum
  czasu albo odchylenie standardowe wyników/czasów; obecnie API zwraca
  wyłącznie średni czas i średni błąd.
- [ ] Zdecydować, czy seria eksperymentu ma być zapisywana jako osobny,
  identyfikowalny eksperyment. Obecnie zapisywane są pojedyncze uruchomienia,
  ale nie ma nadrzędnego rekordu grupującego ich konfigurację i seed bazowy.
- [ ] Sprawdzić limity requestów i obsługę konfiguracji skrajnych, by
  eksperymenty o dużej populacji, liczbie epok i powtórzeń nie blokowały
  aplikacji przez nieakceptowalny czas.

### Etap D — formularz, wyniki i historia

- [ ] Dostosować formularz do uzgodnionej nazwy i zakresu parametru precyzji.
- [ ] Dopasować pole powtórzeń i jego walidację do reguły ustalonej w etapie 1.
- [ ] Sprawdzić w GUI każdy operator, włączniki operatorów, zależne pola
  (turniej, krzyżowanie ziarniste, elityzm) i zakresy wartości.
- [ ] Uzupełnić widok eksperymentu o wszystkie zatwierdzone statystyki
  i jasne podanie liczby powtórzeń, seedów oraz konfiguracji.
- [ ] Upewnić się, że wykresy eksperymentu pochodzą z najlepszego przebiegu
  według wybranego celu, a wykresy pojedynczego przebiegu prezentują właściwe
  statystyki dla każdej epoki.
- [ ] Zweryfikować wyświetlanie wyniku dla maksymalizacji, w tym opisy serii
  wykresów oraz wartości „najlepsza” i „najgorsza”.
- [ ] Potwierdzić, że historia i eksport CSV zachowują komplet danych
  potrzebnych do raportu: benchmark, wymiar, konfigurację, seed, wynik,
  błąd od optimum, czas oraz dane epok.
- [ ] Obsłużyć czytelnie błędy API i błędne odpowiedzi bez pozorowania
  poprawnego wyniku; sprawdzić także odświeżanie historii po serii
  eksperymentu.

### Etap E — integracja i kryteria zakończenia kodu

- [ ] Uruchomić testy backendu obejmujące P1 i wspólną obsługę zapisów.
- [ ] Uruchomić `npm test` oraz `npm run build` w katalogu `frontend`.
- [ ] Ręcznie sprawdzić aplikację: oba benchmarki, poprawne i błędne
  konfiguracje, minimalizację, maksymalizację, zapis historii, ponowne
  wczytanie parametrów, odtworzenie wyniku i pobranie CSV.
- [ ] Sprawdzić serie eksperymentów na krótkiej konfiguracji testowej oraz
  serii spełniającej wymagania raportu.
- [ ] Wykonać próbę na czystym środowisku według instrukcji README:
  instalacja zależności, start backendu i frontendu, uruchomienie P1.
- [ ] Zaktualizować README oraz tę checklistę po zakończeniu prac; nie
  zostawiać niezgodnych zakresów, nazw parametrów ani przykładowych requestów.

## 3. Pomiary i sprawozdanie

- [ ] Wybrać benchmarki, wymiary i konfiguracje, które rzeczywiście będą
  porównywane; utrzymać te same funkcje i wymiary w porównywanych
  konfiguracjach.
- [ ] Ustalić wartości parametrów i seedów przed pomiarami. Dla każdej
  raportowanej konfiguracji wykonać co najmniej 10 powtórzeń (lub inną
  zatwierdzoną liczbę wynikającą z wymagań).
- [ ] Zachować dane wejściowe eksperymentu, seedy, wszystkie wyniki i czasy
  z historii aplikacji lub eksportów CSV; opisać metodę liczenia
  statystyk.
- [ ] Przygotować opis technologii, wymagań środowiskowych i instrukcję
  uruchomienia.
- [ ] Dla każdej funkcji testowej przygotować wzór, zakres, wykres, rzeczywistą
  wartość optimum i argumenty osiągające optimum. Podać właściwe dane dla
  każdego raportowanego wymiaru.
- [ ] Dla najlepszego pojedynczego przebiegu każdej omawianej konfiguracji
  przygotować wykres wartości funkcji względem epoki oraz wykres średniej
  i odchylenia standardowego względem epoki.
- [ ] Przygotować porównanie konfiguracji obejmujące co najmniej średni,
  najlepszy i najgorszy wynik oraz czas obliczeń; jasno oznaczyć, czy wynik
  jest minimalizowany, czy maksymalizowany.
- [ ] Przygotować tabelę końcową: funkcja, liczba zmiennych, rzeczywiste
  optimum, najlepszy wynik algorytmu i błąd względem optimum.
- [ ] Sprawdzić, czy wnioski wynikają z zapisanych danych i czy nie zestawiają
  wyników uzyskanych dla różnych funkcji lub wymiarów.

## 4. Materiały do oddania

- [ ] Nagrać krótką demonstrację (około 1–2 minut) pokazującą działanie
  aplikacji i dołączyć ją do sprawozdania.
- [ ] Spakować kod źródłowy, sprawozdanie i nagranie do ZIP o nazwie
  `P1_Nazwisko1Imie1_Nazwisko2Imie2.zip`.
- [ ] Otworzyć archiwum kontrolnie i potwierdzić, że zawiera wymagane pliki,
  ale nie zawiera lokalnej bazy, środowiska wirtualnego ani `node_modules`.
- [ ] Wgrać archiwum na platformę Delta i sprawdzić potwierdzenie przesłania.

## 5. Opcjonalnie — poza minimum oddania

- [ ] Dla szczególnie istotnych porównań zwiększyć liczbę seedów i rozważyć
  dodatkowe testy statystyczne; opisać je osobno od podstawowych wyników.
