# Nøytralitetsanalyse av Dommere

## Formål

Nøytralitetsanalysemodulen gjør det mulig å objektivt evaluere upartiskheten til hver dommer under en konkurranse. Den oppdager automatisk potensielle skjevheter ved å sammenligne tildelte poeng basert på flere statistiske kriterier.

Denne modulen er et verktøy for **opplæring og kontinuerlig forbedring** for dommere, og ikke et disiplinærverktøy. Den gjør det mulig for hver dommer å bli bevisst sine ubevisste tendenser for å kunne utvikle seg.

---

## Nøytralitetsscore (0-100)

Hver dommer mottar en **samlet nøytralitetsscore** beregnet ut av 100 poeng. Jo høyere scoren er, desto mer anses dommeren som upartisk.

Scoren beregnes ved å trekke fra straffer fra den perfekte scoren på 100, basert på 4 vektede kriterier:

| Kriterium | Vekt | Maksimal straff |
|-----------|------|-----------------|
| Klubbskjevhet | 30% | -30 poeng |
| Nasjonalitetsskjevhet | 25% | -25 poeng |
| Posisjoneringsskjevhet | 20% | -20 poeng |
| Samsvar med kollegaer | 25% | -25 poeng |

### Risikonivåer

| Score | Nivå | Betydning |
|-------|------|-----------|
| **80-100** | Lav risiko (grønn) | Dommeren bedømmer konsistent og upartisk |
| **60-79** | Moderat risiko (oransje) | Tendenser oppdaget, bør overvåkes |
| **0-59** | Høy risiko (rød) | Betydelige skjevheter oppdaget, opplæring anbefalt |

---

## Kriterium 1: Klubbskjevhet

### Prinsipp
Dette kriteriet sammenligner gjennomsnittet av poeng en dommer tildeler utøvere fra **sin egen klubb** med utøvere **fra andre klubber**.

### Beregning
```
Forskjell = Gjennomsnitt(poeng til utøvere fra egen klubb) - Gjennomsnitt(poeng til andre utøvere)
```

### Deteksjonsgrenser

| Forskjell (absolutt verdi) | Alvorlighet | Tolkning |
|---------------------------|-------------|----------|
| < 0,3 poeng | Nøytral | Ingen skjevhet oppdaget |
| 0,3 til 0,5 poeng | Lav | Lett favorisering eller disfavorisering |
| 0,5 til 0,8 poeng | Moderat | Betydelig tendens som bør overvåkes |
| > 0,8 poeng | Høy | Markant skjevhet, korrigerende tiltak anbefalt |

### Hvordan tolke
- **Positiv verdi** (+): dommeren har en tendens til å bedømme mer positivt utøvere fra sin klubb
- **Negativ verdi** (-): dommeren har en tendens til å være strengere med utøvere fra sin klubb (overkompensering)
- Begge situasjoner er skjevheter som bør korrigeres

### Straff på samlet score

| Alvorlighet | Straff |
|-------------|--------|
| Nøytral | 0 poeng |
| Lav | -10 poeng |
| Moderat | -20 poeng |
| Høy | -30 poeng |

---

## Kriterium 2: Nasjonalitetsskjevhet

### Prinsipp
Dette kriteriet sammenligner gjennomsnittet av poeng tildelt utøvere av **samme nasjonalitet** som dommeren med utøvere **av andre nasjonaliteter**.

### Beregning
```
Forskjell = Gjennomsnitt(poeng til samme nasjonalitet) - Gjennomsnitt(poeng til andre nasjonaliteter)
```

### Deteksjonsgrenser

| Forskjell (absolutt verdi) | Alvorlighet | Tolkning |
|---------------------------|-------------|----------|
| < 0,2 poeng | Nøytral | Ingen skjevhet oppdaget |
| 0,2 til 0,4 poeng | Lav | Lett favorisering eller disfavorisering |
| 0,4 til 0,6 poeng | Moderat | Betydelig tendens |
| > 0,6 poeng | Høy | Markant skjevhet |

### Hvordan tolke
- **Strengere grenser** enn klubbskjevhet, da nasjonalitet ikke burde ha noen innflytelse på teknisk bedømming
- **Positiv verdi**: favorisering av egen nasjonalitet
- **Negativ verdi**: overdreven strenghet overfor egen nasjonalitet

### Straff på samlet score

| Alvorlighet | Straff |
|-------------|--------|
| Nøytral | 0 poeng |
| Lav | -8 poeng |
| Moderat | -16 poeng |
| Høy | -25 poeng |

---

## Kriterium 3: Posisjoneringsskjevhet

### Prinsipp
Dette kriteriet sammenligner **det generelle gjennomsnittet av poeng** til en dommer med **gjennomsnittet av alle dommere** i konkurransen. Det oppdager dommere som systematisk er for sjenerøse eller for strenge.

### Beregning
```
Forskjell = Gjennomsnitt(alle dommerens poeng) - Gjennomsnitt(alle poeng fra alle dommere)
```

### Deteksjonsgrenser

| Forskjell (absolutt verdi) | Alvorlighet | Tolkning |
|---------------------------|-------------|----------|
| < 0,2 poeng | Nøytral | Innenfor gjennomsnittet, kalibrert bedømming |
| 0,2 til 0,4 poeng | Lav | Litt sjenerøs eller streng |
| 0,4 til 0,6 poeng | Moderat | Merkbart sjenerøs eller streng |
| > 0,6 poeng | Høy | Svært sjenerøs eller svært streng |

### Hvordan tolke
- **Positiv verdi** (+): dommeren bedømmer systematisk over gjennomsnittet (sjenerøs)
- **Negativ verdi** (-): dommeren bedømmer systematisk under gjennomsnittet (streng)
- En god dommer ligger innenfor det nøytrale området (< 0,2 poeng avvik)

### Straff på samlet score

| Alvorlighet | Straff |
|-------------|--------|
| Nøytral | 0 poeng |
| Lav | -5 poeng |
| Moderat | -12 poeng |
| Høy | -20 poeng |

---

## Kriterium 4: Samsvar med Kollegaer

### Prinsipp
Dette kriteriet måler i hvilken grad en dommers poeng er **i samsvar med de andre dommernes** for de samme prestasjonene. En dommer hvis poeng konsekvent avviker fra kollegaene kan ha et kalibrerings- eller skjevhetsproblem.

### Beregning
For hver prestasjon bedømt av dommeren:
```
Gjennomsnitt av andre = Gjennomsnitt(poeng fra andre dommere for denne prestasjonen)
Avvik = |Dommerens poeng - Gjennomsnitt av andre|
Individuelt samsvar = maks(0, 100 - (Avvik × 20))
```

Den **samlede samsvarsscoren** er gjennomsnittet av alle individuelle samsvar.

### Tolkning

| Samsvar | Betydning |
|---------|-----------|
| **90-100%** | Utmerket samsvar, svært samstemt bedømming |
| **75-89%** | Godt samsvar |
| **60-74%** | Akseptabelt samsvar, men bør forbedres |
| **< 60%** | Lavt samsvar, **varsling generert** |

### Innvirkning på samlet score
Samsvaret påvirker nøytralitetsscoren via en bonus/malus:
```
Justering = (Samsvar - 50) / 2
```
- Samsvar på 100%: bonus på +25 poeng
- Samsvar på 50%: verken bonus eller malus
- Samsvar på 0%: malus på -25 poeng

### Betingelser
- Et minimum av **3 prestasjoner** bedømt kreves for at beregningen skal være signifikant
- Bare aktive poeng (ikke treningspoeng) tas med i beregningen

---

## Varslingssystem

Varsler genereres automatisk i følgende tilfeller:

| Betingelse | Varsling |
|-----------|----------|
| Moderat eller høy klubbskjevhet | "Klubbskjevhet oppdaget" med avviksverdien |
| Moderat eller høy nasjonalitetsskjevhet | "Nasjonalitetsskjevhet oppdaget" med avviksverdien |
| Kun høy posisjonering | "Ekstrem posisjonering" med avvik fra gjennomsnittet |
| Samsvar < 60% | "Lavt samsvar med andre dommere" |

Varslene er synlige på det detaljerte kortet til hver dommer i analysegrensesnittet.

---

## Podium for de Mest Upartiske Dommerne

Ved slutten av analysen fremhever et **podium** de 3 dommerne med de beste nøytralitetsscorene:

- **1. plass (Gull)**: Høyeste nøytralitetsscore
- **2. plass (Sølv)**: Nest beste score
- **3. plass (Bronse)**: Tredje beste score

Denne rangeringen belønner upartiskhet og oppmuntrer alle dommere til å forbedre seg.

---

## Anbefalinger for Dommere

### For å forbedre sin nøytralitetsscore

1. **Klubbskjevhet**: Vær spesielt oppmerksom når du bedømmer en utøver fra din egen klubb. Bruk de samme tekniske kriteriene som for andre.

2. **Nasjonalitetsskjevhet**: Konsentrer deg utelukkende om teknikk og utførelse. Utøverens nasjonalitet skal ikke påvirke din evaluering.

3. **Posisjonering**: Kalibrer poengene dine ved å følge de definerte kriteriene. Verken for sjenerøs eller for streng. Ved tvil, se den offisielle poengtabellen.

4. **Samsvar**: Hvis poengene dine ofte avviker fra kollegaenes, kan dette indikere et problem med forståelsen av kriteriene. Delta på kalibreringssesjoner.

### God praksis

- Bedøm hver prestasjon uavhengig, uten å se på andre dommeres poeng
- Bruk hele bredden av poengsystemet
- Ikke endre poengene dine etter å ha sett andres
- Ta deg tid til å evaluere hvert kriterium separat
- Ved tretthet, ta en pause for å opprettholde konsentrasjonen

---

## Tilgang og Konfidensialitet

- Nøytralitetsanalysen er tilgjengelig for **konkurransearrangører** og **forbundsadministratorer**
- Hver dommer kan se **sine egne resultater**
- Dataene beregnes i **sanntid** fra eksisterende poeng (ingen nøytralitetsdata lagres permanent)
- Analysen krever et tilstrekkelig antall poeng for å være pålitelig (minimum 3 prestasjoner for samsvar)
