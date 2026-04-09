# Neutralitätsanalyse der Kampfrichter

## Ziel

Das Modul zur Neutralitätsanalyse ermöglicht die objektive Bewertung der Unparteilichkeit jedes Kampfrichters während eines Wettkampfs. Es erkennt automatisch potenzielle Befangenheiten, indem es die vergebenen Noten anhand mehrerer statistischer Kriterien vergleicht.

Dieses Modul ist ein Werkzeug zur **Fortbildung und kontinuierlichen Verbesserung** für Kampfrichter und kein Disziplinarwerkzeug. Es ermöglicht jedem Kampfrichter, sich seiner unbewussten Tendenzen bewusst zu werden, um sich zu verbessern.

---

## Neutralitätspunktzahl (0-100)

Jeder Kampfrichter erhält eine **globale Neutralitätspunktzahl**, die auf 100 Punkte berechnet wird. Je höher die Punktzahl, desto unparteiischer wird der Kampfrichter angesehen.

Die Punktzahl wird berechnet, indem Strafpunkte von der perfekten Punktzahl 100 abgezogen werden, basierend auf 4 gewichteten Kriterien:

| Kriterium | Gewicht | Maximale Strafe |
|-----------|---------|-----------------|
| Vereinsbefangenheit | 30% | -30 Punkte |
| Nationalitätsbefangenheit | 25% | -25 Punkte |
| Positionierungsbefangenheit | 20% | -20 Punkte |
| Übereinstimmung mit den Kollegen | 25% | -25 Punkte |

### Risikostufen

| Punktzahl | Stufe | Bedeutung |
|-----------|-------|-----------|
| **80-100** | Geringes Risiko (grün) | Der Kampfrichter bewertet konsistent und unparteiisch |
| **60-79** | Mäßiges Risiko (orange) | Tendenzen erkannt, zu beobachten |
| **0-59** | Hohes Risiko (rot) | Signifikante Befangenheiten erkannt, Fortbildung empfohlen |

---

## Kriterium 1: Vereinsbefangenheit

### Prinzip
Dieses Kriterium vergleicht den Durchschnitt der Noten, die ein Kampfrichter den Praktizierenden **seines eigenen Vereins** im Vergleich zu den Praktizierenden **anderer Vereine** gibt.

### Berechnung
```
Differenz = Durchschnitt(Noten an Praktizierende desselben Vereins) - Durchschnitt(Noten an andere Praktizierende)
```

### Erkennungsschwellen

| Differenz (Absolutwert) | Schweregrad | Interpretation |
|-------------------------|-------------|----------------|
| < 0,3 Punkte | Neutral | Keine Befangenheit erkannt |
| 0,3 bis 0,5 Punkte | Gering | Leichte Bevorzugung oder Benachteiligung |
| 0,5 bis 0,8 Punkte | Mäßig | Signifikante Tendenz, zu beobachten |
| > 0,8 Punkte | Hoch | Deutliche Befangenheit, Korrekturmaßnahme empfohlen |

### Interpretation
- **Positiver Wert** (+): Der Kampfrichter neigt dazu, Praktizierende seines Vereins günstiger zu bewerten
- **Negativer Wert** (-): Der Kampfrichter neigt dazu, mit Praktizierenden seines Vereins strenger zu sein (Überkompensation)
- Beide Situationen sind zu korrigierende Befangenheiten

### Strafe auf die Gesamtpunktzahl

| Schweregrad | Strafe |
|-------------|--------|
| Neutral | 0 Punkte |
| Gering | -10 Punkte |
| Mäßig | -20 Punkte |
| Hoch | -30 Punkte |

---

## Kriterium 2: Nationalitätsbefangenheit

### Prinzip
Dieses Kriterium vergleicht den Durchschnitt der Noten, die Praktizierenden **derselben Nationalität** wie der Kampfrichter vergeben werden, mit den Praktizierenden **anderer Nationalitäten**.

### Berechnung
```
Differenz = Durchschnitt(Noten gleiche Nationalität) - Durchschnitt(Noten andere Nationalitäten)
```

### Erkennungsschwellen

| Differenz (Absolutwert) | Schweregrad | Interpretation |
|-------------------------|-------------|----------------|
| < 0,2 Punkte | Neutral | Keine Befangenheit erkannt |
| 0,2 bis 0,4 Punkte | Gering | Leichte Bevorzugung oder Benachteiligung |
| 0,4 bis 0,6 Punkte | Mäßig | Signifikante Tendenz |
| > 0,6 Punkte | Hoch | Deutliche Befangenheit |

### Interpretation
- **Strengere Schwellen** als bei der Vereinsbefangenheit, da die Nationalität keinen Einfluss auf die technische Bewertung haben sollte
- **Positiver Wert**: Bevorzugung der eigenen Nationalität
- **Negativer Wert**: Übermäßige Strenge gegenüber der eigenen Nationalität

### Strafe auf die Gesamtpunktzahl

| Schweregrad | Strafe |
|-------------|--------|
| Neutral | 0 Punkte |
| Gering | -8 Punkte |
| Mäßig | -16 Punkte |
| Hoch | -25 Punkte |

---

## Kriterium 3: Positionierungsbefangenheit

### Prinzip
Dieses Kriterium vergleicht den **allgemeinen Notendurchschnitt** eines Kampfrichters mit dem **Durchschnitt aller Kampfrichter** des Wettkampfs. Es erkennt systematisch zu großzügige oder zu strenge Kampfrichter.

### Berechnung
```
Differenz = Durchschnitt(alle Noten des Kampfrichters) - Durchschnitt(alle Noten aller Kampfrichter)
```

### Erkennungsschwellen

| Differenz (Absolutwert) | Schweregrad | Interpretation |
|-------------------------|-------------|----------------|
| < 0,2 Punkte | Neutral | Im Durchschnitt, kalibrierte Bewertung |
| 0,2 bis 0,4 Punkte | Gering | Leicht großzügig oder streng |
| 0,4 bis 0,6 Punkte | Mäßig | Auffallend großzügig oder streng |
| > 0,6 Punkte | Hoch | Sehr großzügig oder sehr streng |

### Interpretation
- **Positiver Wert** (+): Der Kampfrichter bewertet systematisch über dem Durchschnitt (großzügig)
- **Negativer Wert** (-): Der Kampfrichter bewertet systematisch unter dem Durchschnitt (streng)
- Ein guter Kampfrichter liegt im neutralen Bereich (< 0,2 Punkte Abweichung)

### Strafe auf die Gesamtpunktzahl

| Schweregrad | Strafe |
|-------------|--------|
| Neutral | 0 Punkte |
| Gering | -5 Punkte |
| Mäßig | -12 Punkte |
| Hoch | -20 Punkte |

---

## Kriterium 4: Übereinstimmung mit den Kollegen

### Prinzip
Dieses Kriterium misst, inwieweit die Noten eines Kampfrichters **mit denen der anderen Kampfrichter** für dieselben Darbietungen **übereinstimmen**. Ein Kampfrichter, dessen Noten ständig von denen seiner Kollegen abweichen, kann ein Kalibrierungs- oder Befangenheitsproblem aufweisen.

### Berechnung
Für jede vom Kampfrichter bewertete Darbietung:
```
Durchschnitt der anderen = Durchschnitt(Noten der anderen Kampfrichter für diese Darbietung)
Abweichung = |Note des Kampfrichters - Durchschnitt der anderen|
Individuelle Übereinstimmung = max(0, 100 - (Abweichung × 20))
```

Die **globale Übereinstimmungspunktzahl** ist der Durchschnitt aller individuellen Übereinstimmungen.

### Interpretation

| Übereinstimmung | Bedeutung |
|-----------------|-----------|
| **90-100%** | Ausgezeichnete Übereinstimmung, sehr abgestimmte Bewertung |
| **75-89%** | Gute Übereinstimmung |
| **60-74%** | Akzeptable, aber verbesserungsfähige Übereinstimmung |
| **< 60%** | Geringe Übereinstimmung, **Warnung generiert** |

### Auswirkung auf die Gesamtpunktzahl
Die Übereinstimmung beeinflusst die Neutralitätspunktzahl über einen Bonus/Malus:
```
Anpassung = (Übereinstimmung - 50) / 2
```
- Übereinstimmung von 100%: Bonus von +25 Punkten
- Übereinstimmung von 50%: weder Bonus noch Malus
- Übereinstimmung von 0%: Malus von -25 Punkten

### Bedingungen
- Mindestens **3 bewertete Darbietungen** sind erforderlich, damit die Berechnung aussagekräftig ist
- Nur aktive Noten (keine Übungsnoten) werden berücksichtigt

---

## Warnsystem

Warnungen werden in folgenden Fällen automatisch generiert:

| Bedingung | Warnung |
|-----------|---------|
| Mäßige oder hohe Vereinsbefangenheit | "Vereinsbefangenheit erkannt" mit dem Abweichungswert |
| Mäßige oder hohe Nationalitätsbefangenheit | "Nationalitätsbefangenheit erkannt" mit dem Abweichungswert |
| Nur hohe Positionierung | "Extreme Position" mit der Abweichung vom Durchschnitt |
| Übereinstimmung < 60% | "Geringe Übereinstimmung mit den anderen Kampfrichtern" |

Die Warnungen sind auf der Detailkarte jedes Kampfrichters in der Analyseoberfläche sichtbar.

---

## Podium der unparteiischsten Kampfrichter

Am Ende der Analyse hebt ein **Podium** die 3 Kampfrichter mit den besten Neutralitätspunktzahlen hervor:

- **1. Platz (Gold)**: Höchste Neutralitätspunktzahl
- **2. Platz (Silber)**: Zweithöchste Punktzahl
- **3. Platz (Bronze)**: Dritthöchste Punktzahl

Diese Rangliste belohnt die Unparteilichkeit und ermutigt alle Kampfrichter, sich zu verbessern.

---

## Empfehlungen für Kampfrichter

### Zur Verbesserung Ihrer Neutralitätspunktzahl

1. **Vereinsbefangenheit**: Achten Sie besonders darauf, wenn Sie einen Praktizierenden Ihres eigenen Vereins bewerten. Wenden Sie die gleichen technischen Kriterien wie für andere an.

2. **Nationalitätsbefangenheit**: Konzentrieren Sie sich ausschließlich auf Technik und Ausführung. Die Nationalität des Praktizierenden sollte Ihre Bewertung nicht beeinflussen.

3. **Positionierung**: Kalibrieren Sie Ihre Noten an den definierten Kriterien. Weder zu großzügig noch zu streng. Im Zweifel beziehen Sie sich auf die offizielle Bewertungsskala.

4. **Übereinstimmung**: Wenn Ihre Noten häufig von denen Ihrer Kollegen abweichen, kann dies auf ein Problem beim Verständnis der Kriterien hindeuten. Nehmen Sie an Kalibrierungssitzungen teil.

### Bewährte Praktiken

- Bewerten Sie jede Darbietung unabhängig, ohne die Noten der anderen Kampfrichter anzusehen
- Nutzen Sie die gesamte Bewertungsskala
- Ändern Sie Ihre Noten nicht, nachdem Sie die der anderen gesehen haben
- Nehmen Sie sich Zeit, jedes Kriterium einzeln zu bewerten
- Machen Sie bei Müdigkeit eine Pause, um Ihre Konzentration aufrechtzuerhalten

---

## Zugang und Vertraulichkeit

- Die Neutralitätsanalyse ist für **Wettkampforganisatoren** und **Verbandsadministratoren** zugänglich
- Jeder Kampfrichter kann **seine eigenen Ergebnisse** einsehen
- Die Daten werden in **Echtzeit** aus den vorhandenen Noten berechnet (keine Neutralitätsdaten werden dauerhaft gespeichert)
- Die Analyse erfordert eine ausreichende Anzahl von Noten, um zuverlässig zu sein (mindestens 3 Darbietungen für die Übereinstimmung)
