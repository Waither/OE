# Projekt 4 — plan prezentacji (15–20 minut)

## Slajd 1 — Temat i cel (1 min)

Artificial Bee Colony w MealPy oraz porównanie z algorytmem genetycznym.

## Slajd 2 — Inspiracja biologiczna (2 min)

Kolonia pszczół, źródła pożywienia, podział na pszczoły pracujące, obserwujące i zwiadowcze.

## Slajd 3 — Reprezentacja problemu (1 min)

Wektor rzeczywisty, granice dziedziny i wartość funkcji celu jako jakość źródła.

## Slajd 4 — Pszczoły pracujące (2 min)

Tworzenie sąsiada, lokalna modyfikacja rozwiązania i zasada zachowania lepszego źródła.

## Slajd 5 — Pszczoły obserwujące (2 min)

Losowanie źródeł z prawdopodobieństwem zależnym od jakości.

## Slajd 6 — Pszczoły zwiadowcze (1 min)

Limit prób i ponowne losowanie opuszczonego źródła.

## Slajd 7 — Przykład krok po kroku (3 min)

Dwa źródła w funkcji dwuwymiarowej, obliczenie wartości celu, utworzenie sąsiada i decyzja o zastąpieniu.

## Slajd 8 — Konfiguracja eksperymentu (1 min)

Populacja, epoki, `n_limits`, seedy i pięć powtórzeń.

## Slajd 9 — Funkcje testowe (1 min)

Ackley, Hyperellipsoid, CEC2014 F1 i CEC2014 F3.

## Slajd 10 — Wyniki ABC (2 min)

Średnie wyniki, odchylenia, czasy i wykresy zbieżności.

## Slajd 11 — Porównanie z GA (2 min)

Porównanie jakości rozwiązania, stabilności i czasu z P2.

## Slajd 12 — Wnioski (1 min)

Kiedy ABC jest korzystny, wpływ `n_limits`, ograniczenia i możliwe dalsze eksperymenty.

## Slajd 13 — Dodatkowe porównanie

Uwzględniono CEC2014 F1 oraz wyniki P1 i P2. Wykres: [comparison_p1_p2.png](./comparison_p1_p2.png).

## Slajd 14 — Wpływ konfiguracji

Porównano cztery ustawienia populacji, epok i `n_limits`. Wykres: [configurations_abc.png](./configurations_abc.png).

## Slajd 15 — Podsumowanie

ABC, P1 i P2 oceniono na tych samych seedach tam, gdzie funkcje były wspólne. Wyniki należy interpretować razem z czasem obliczeń i stabilnością.
