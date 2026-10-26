# Projekt 3 — PyGAD

## Cel projektu

Celem jest optymalizacja funkcji celu z wykorzystaniem biblioteki PyGAD dla
reprezentacji binarnej i rzeczywistej.

## Reprezentacja i dekodowanie

W reprezentacji binarnej chromosom jest dzielony na równe bloki. Dla 60 genów
i 3 zmiennych pierwsze 20 bitów opisuje pierwszą zmienną, kolejne 20 drugą,
a ostatnie 20 trzecią. Wartość binarna jest skalowana do przedziału `[0, 1]`.

## Badane operatory

Przetestowano selekcję turniejową, ruletkę (`rws`) i losową. Dla chromosomu
binarnego używane są krzyżowania `single_point`, `two_points` i `uniform` oraz
mutacje `random` i `swap`. Dla chromosomu rzeczywistego dodano własne callbacki
PyGAD: krzyżowanie jednopunktowe, dwupunktowe, jednorodne, arytmetyczne,
BLX-α, BLX-αβ i uśredniające oraz mutację Gaussa.

## Uruchomienie

```bash
python p3_console.py --experiment --function hyperellipsoid --dimensions 10
```

Wyniki są zapisywane do `sprawozdanie_p3/results.json`. Każdy wynik zawiera
konfigurację, seed, najlepszy chromosom, wartość funkcji i historię pokoleń.

## Funkcje benchmarkowe

Program obsługuje funkcję z treści zadania oraz `Hyperellipsoid`, `Ackley01` i
CEC2014 F3. Dla funkcji benchmarkowych należy dobrać odpowiedni wymiar zgodnie
z ich ograniczeniami.

## Uwaga o funkcji z treści zadania

Funkcja kwadratowa ma minimum globalne w `(1, 3)`. Jeżeli obie zmienne są
ograniczone do `[0, 1]`, minimum globalne leży poza dziedziną i eksperyment
raportuje najlepsze rozwiązanie w ograniczonym obszarze.

## Wyniki eksperymentów

Eksperyment główny wykonano dla 25 pokoleń, populacji 20 osobników i 10 rodziców. Dla funkcji kwadratowej przetestowano wszystkie kombinacje operatorów wymagane w zadaniu.

| Reprezentacja | Liczba konfiguracji | Najlepszy wynik | Średni czas [s] |
|---|---:|---:|---:|
| binary | 18 | 20.000100 | 0.0429 |
| real | 63 | 20.000000 | 0.0114 |

Wykresy: [zbieżność binarna](./convergence_binary.png), [zbieżność rzeczywista](./convergence_real.png), [porównanie konfiguracji](./comparison.png).

Pliki danych: [results.csv](./results.csv) i [results.json](./results.json).

## Wnioski

Wyniki są zależne od funkcji, operatorów i losowego seeda. Reprezentacja rzeczywista pozwala wykonywać operacje BLX oraz Gaussa bez dekodowania bitów, natomiast binarna daje kontrolę nad precyzją przez liczbę bitów przypadających na zmienną.
