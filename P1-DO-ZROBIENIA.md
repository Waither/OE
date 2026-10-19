# Projekt 1 — zadania do dokończenia

Lista oparta na wymaganiach z [pdf/P1.pdf](./pdf/P1.pdf) i aktualnym stanie aplikacji.

## Do zrobienia w kodzie

- [ ] **Uzgodnić znaczenie parametru dokładności.** Formularz opisuje go jako „Dokładność (bity)”, ale obecny parametr określa precyzję dziesiętną, a liczbę bitów chromosomu algorytm wylicza sam. Po ustaleniu oczekiwanego zachowania:
  - zmienić etykietę i opis parametru, jeśli ma pozostać precyzją dziesiętną, albo
  - zmienić kodowanie i walidację, jeśli użytkownik ma bezpośrednio ustawiać liczbę bitów.
- [ ] **Ustalić i wdrożyć regułę dla powtórzeń eksperymentu.** Wymagania sprawozdania mówią o co najmniej 10 uruchomieniach na konfigurację, ale API i formularz obecnie dopuszczają mniej. Zdecydować, czy wymusić minimum 10, czy zostawić krótkie testy jako osobny tryb.
- [ ] **Uzupełnić testy P1** o kodowanie/dekodowanie chromosomu, selekcje, rodzaje krzyżowania i mutacji, inwersję, elityzm oraz minimalizację/maksymalizację. Sprawdzić też powtarzalność wyniku dla tego samego seedu.
- [ ] **Zweryfikować pomiary przed oddaniem:** porównać kilka konfiguracji na tych samych funkcjach i wymiarach, z co najmniej 10 powtórzeniami każdej konfiguracji raportowanej w sprawozdaniu. Zachować wyniki i czasy z historii/eksportu CSV.
- [ ] **Sprawdzić kompletność widoku eksperymentu** względem danych zwracanych przez backend: podsumowanie ma umożliwiać zestawienie średniej, najlepszego i najgorszego wyniku oraz czasu dla serii powtórzeń.
- [ ] **Przejść próbę oddania na czystym uruchomieniu:** instalacja zależności, start backendu i frontendu oraz wykonanie pojedynczego uruchomienia i eksperymentu.

## Do przygotowania poza kodem

- [ ] **Sprawozdanie — technologia i uruchomienie:** użyte technologie oraz wymagania środowiskowe i instrukcja uruchomienia aplikacji.
- [ ] **Sprawozdanie — funkcje testowe:** wybrane funkcje, ich wzory/wykresy, zakresy, rzeczywiste wartości optimum i argumenty, dla których optimum jest osiągane. Podać dane dla każdej testowanej liczby zmiennych.
- [ ] **Sprawozdanie — wyniki pojedynczego przebiegu:** wykres wartości funkcji względem epoki oraz wykres średniej i odchylenia standardowego względem epoki. Wymagania proszą o wykresy z najlepszego uruchomienia.
- [ ] **Sprawozdanie — porównanie konfiguracji:** co najmniej 10 powtórzeń na każdą porównywaną konfigurację; podać średni, najlepszy i najgorszy wynik oraz porównać czas obliczeń.
- [ ] **Sprawozdanie — podsumowanie:** tabela z nazwą funkcji, liczbą zmiennych, rzeczywistym optimum, najlepszym wynikiem algorytmu i błędem względem optimum.
- [ ] **Nagranie demonstracyjne:** krótki film (około 1–2 minut) pokazujący działanie projektu i dołączyć go do sprawozdania.
- [ ] **Archiwum do oddania:** spakować kod źródłowy, sprawozdanie i nagranie do ZIP o nazwie `P1_Nazwisko1Imie1_Nazwisko2Imie2.zip` i wgrać na platformę Delta.

## Poza wymaganiami oddania

- [ ] Rozważyć dodatkowe testy statystyczne lub więcej seedów dla konfiguracji, które mają być szczególnie dokładnie porównane.
