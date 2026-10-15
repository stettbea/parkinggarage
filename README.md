# parkinggarage
data analytics project

Ich würde nicht zuerst mit Modeling oder K-Means anfangen. Der erste Schritt ist jetzt: Projekt sauber abgrenzen und sofort mit der Datensammlung starten, weil der offizielle Zürcher Feed nur den aktuellen Zustand liefert und keine eigene Historie enthält.

Für euch wäre dieser Start am sinnvollsten:

Forschungsfrage final festlegen. Ich würde aktuell mit dieser arbeiten:
“How do parking garage utilization patterns in Zurich differ by location, time of day, weekday/weekend and weather conditions, and how reliably can periods of high utilization be identified?”
Damit ist von Anfang an klar, dass euer Projekt nicht nur eine simple Prediction ist, sondern auch Vergleiche und Muster untersucht.
Primärdatenquelle testen. Der offizielle Feed der Stadt Zürich liefert laufend die freien Plätze, Status, Parkhausname, Zeitstempel und eine eindeutige ID als XML/RSS. Der aktuelle Endpoint ist http://www.pls-zh.ch/plsFeed/rss. Die Stadt beschreibt die Datenqualität als „sehr gut“, weist aber darauf hin, dass nicht alle Zürcher Parkhäuser im PLS-Verbund enthalten sind.
Sofort eigene Daten speichern. Das ist momentan der wichtigste Punkt. Der Feed enthält nur die aktuelle Belegung. Wenn ihr heute nicht sammelt, könnt ihr diesen Zeitpunkt später nicht aus dem offiziellen Feed rekonstruieren. Ich würde alle 15 Minuten speichern. Das reicht völlig und hält die Datenmenge übersichtlich.

Eure erste Rohdatentabelle sollte zunächst wirklich nur so aussehen:

timestamp	parking_id	parking_name	free_spaces	status
2026-10-08 18:00	…	Urania	125	open
2026-10-08 18:15	…	Urania	111	open
2026-10-08 18:30	…	Urania	97	open

Die Stadt liefert dafür genau die relevanten Felder title, description, pubDate und guid; in description stecken Status und Zahl der aktuell freien Plätze. Mögliche Statuswerte sind open, closed und unbestimmt.

Danach würde ich in dieser Reihenfolge arbeiten
Phase 1 – diese Woche: Datenquelle verstehen

Bevor ihr irgendetwas automatisiert, ruft ihr den Feed einmal in Python ab und schaut euch an:

import requests

url = "http://www.pls-zh.ch/plsFeed/rss"

response = requests.get(url)

print(response.status_code)
print(response.text[:2000])

Ziel ist noch nicht, perfekten Code zu schreiben. Ihr wollt zuerst wissen:

Wie viele Parkhäuser werden geliefert?
Wie sieht description genau aus?
Ist guid stabil?
Wie werden geschlossene Parkhäuser dargestellt?
Ist immer eine Zahl für freie Plätze vorhanden?

Danach bauen wir daraus einen Pandas-DataFrame.

Phase 2 – Parkhaus-Stammdaten erstellen

Ihr braucht zusätzlich pro Parkhaus:

parking_id
name
capacity
address
latitude
longitude

Das ist notwendig, weil free_spaces = 40 alleine nichts sagt.

Bei einem Parkhaus mit 50 Plätzen bedeutet es:

nur 20 % belegt.

Bei einem Parkhaus mit 500 Plätzen:

92 % belegt.

Erst daraus entsteht eure zentrale Kennzahl:

$$ occupancy\_rate = \frac{capacity-free\_spaces}{capacity} $$

Der Feed enthält für jedes Objekt auch einen Link zu Detailinformationen wie Adresse, Parkplatzangebot, Tarife und Betreiber.

Zusätzlich gibt es einen offiziellen Geodatensatz mit sämtlichen öffentlich zugänglichen Parkhäusern in Zürich, unter anderem als CSV und GeoJSON.

Das wird dann eure zweite Datenquelle bzw. einer der Integrationsschritte.

Phase 3 – automatisches Sammeln

Erst wenn der einmalige Abruf funktioniert, automatisieren wir:

alle 15 Minuten

Feed abrufen
      ↓
XML parsen
      ↓
Parkhäuser extrahieren
      ↓
timestamp hinzufügen
      ↓
PostgreSQL speichern

Warum ich hier PostgreSQL direkt von Anfang an nehmen würde: Ihr bekommt dafür einen Zusatzpunkt und müsst später nicht von SQLite migrieren.

Bei beispielsweise 25 Parkhäusern:

$$ 25 \times 4 \times 24 = 2400 $$

Records pro Tag.

Nach 6 Wochen wären das rund:

$$ 100'800 $$

Records.

Das ist für euer Projekt sehr angenehm: groß genug für eine ordentliche Analyse, aber überhaupt nicht problematisch.

Phase 4 – Wetter erst später hinzufügen

Wetter würde ich nicht direkt in den Collector einbauen.

Sammelt zuerst sauber:

Parkhaus + Zeit + freie Plätze.

Das Wetter können wir danach anhand des Zeitstempels dazujoinen.

Das verhindert, dass euer Collector unnötig kompliziert wird.

Euer finaler Datensatz könnte später so aussehen:

timestamp	parking	capacity	free	occupancy	hour	weekday	rain	temp
18:00	Urania	500	125	0.75	18	Thu	1	12.1
18:15	Urania	500	111	0.778	18	Thu	1	12.1
Phase 5 – erst dann EDA

Wenn ihr ungefähr 1–2 Wochen Daten habt, könnt ihr schon eine erste Exploratory Data Analysis durchführen.

Ich würde zunächst genau diese Fragen beantworten:

Wie hoch ist die durchschnittliche Auslastung pro Parkhaus?
Wann sind die Parkhäuser am vollsten?
Wie unterscheiden sich Montag–Freitag und Wochenende?
Welche Parkhäuser haben besonders starke Schwankungen?
Wie häufig erreichen einzelne Parkhäuser beispielsweise >80 %, >90 % oder >95 %?
Gibt es offensichtliche Tagesmuster?

Erste Visualisierungen:

1. Line Plot
Auslastung über einen Tag

2. Heatmap
Wochentag × Stunde

3. Boxplot
Auslastung pro Parkhaus

4. Barplot
Anteil Beobachtungen mit hoher Auslastung

5. Karte
durchschnittliche Auslastung pro Parkhaus

Noch kein Machine Learning.

Erst die EDA entscheidet beispielsweise, ob 90 % überhaupt eine sinnvolle Definition von „high utilization“ ist.

Phase 6 – danach Forschungsfrage konkretisieren

Das ist wichtig: Einige Entscheidungen sollten wir nicht jetzt erraten.

Beispielsweise wissen wir momentan noch nicht, ob:

occupancy >= 90 %

ein sinnvolles Target ist.

Angenommen, nur 0.2 % aller Beobachtungen liegen über 90 %. Dann wäre Classification schwierig.

Vielleicht ergeben die Daten:

>= 85 %

als besseren Grenzwert.

Oder vielleicht funktioniert eine Regression auf occupancy_rate besser.

Deshalb:

Daten zuerst kennenlernen → dann Modeling finalisieren.

Phase 7 – K-Means und Statistik

Wenn genügend Daten vorhanden sind, aggregiert ihr jedes Parkhaus beispielsweise zu:

avg_morning_occupancy
avg_afternoon_occupancy
avg_evening_occupancy
avg_weekend_occupancy
peak_occupancy
high_occupancy_frequency

Darauf könnt ihr K-Means anwenden.

Dann könnten sich etwa Nutzungsprofile herausbilden wie:

Cluster 1
tagsüber stark ausgelastet

Cluster 2
abends stark ausgelastet

Cluster 3
am Wochenende stark

Cluster 4
generell geringe Nutzung

Wichtig: Diese Clusterbezeichnungen bestimmen wir erst anhand der tatsächlichen Ergebnisse.

Beim statistischen Test würde ich wahrscheinlich einen einfachen Chi-Quadrat-Test verwenden:

Besteht ein Zusammenhang zwischen weekday/weekend und high utilization?

Das ist leicht verständlich und sinnvoll.

Phase 8 – Modeling

Erst ganz zum Schluss.

Interessantes Target:

Wird das Parkhaus in 30 Minuten eine hohe Auslastung erreichen?

Dann verwendet ihr beispielsweise:

current_occupancy
occupancy_change_last_30min
hour
weekday
weekend
temperature
rain
parking_garage
capacity

und vergleicht:

Logistic Regression
vs.
Random Forest

mit:

Precision
Recall
F1
Confusion Matrix
Konkret: Was ich an eurer Stelle jetzt heute machen würde

Nicht zehn Dinge gleichzeitig.

Heute würde ich nur drei Aufgaben erledigen:

A. Projektordner/GitHub anlegen.

parking-analytics-zurich/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│
├── src/
│   └── collect_parking_data.py
│
├── sql/
│
└── README.md

B. Den RSS-Feed einmal in Python abrufen und in einen sauberen DataFrame umwandeln.

C. Prüfen, welche Parkhäuser tatsächlich geliefert werden und welche Variablen wir genau erhalten.

Danach würde ich erst PostgreSQL und die automatische Datensammlung aufsetzen.

Das Wichtigste ist also gerade nicht, die komplette Analyse fertigzuplanen, sondern:

Wir müssen jetzt zuerst sicherstellen, dass wir die Parkhausdaten zuverlässig auslesen und abspeichern können.

Wenn wir das machen, können wir anschließend wirklich Schritt für Schritt mit eurem ersten Python-Notebook starten – vom API-Abruf bis zu eurem ersten DataFrame, sodass ihr genau versteht, was jede Zeile macht.