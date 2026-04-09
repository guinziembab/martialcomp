# Analisi della Neutralità dei Giudici

## Obiettivo

Il modulo di analisi della neutralità permette di valutare oggettivamente l'imparzialità di ogni giudice durante una competizione. Rileva automaticamente i potenziali pregiudizi confrontando i punteggi assegnati secondo diversi criteri statistici.

Questo modulo è uno strumento di **formazione e miglioramento continuo** per i giudici, non uno strumento disciplinare. Permette a ogni giudice di prendere coscienza delle proprie tendenze inconsce al fine di progredire.

---

## Punteggio di Neutralità (0-100)

Ogni giudice riceve un **punteggio globale di neutralità** calcolato su 100 punti. Più alto è il punteggio, più il giudice è considerato imparziale.

Il punteggio è calcolato sottraendo le penalità dal punteggio perfetto di 100, secondo 4 criteri ponderati:

| Criterio | Peso | Penalità massima |
|----------|------|------------------|
| Pregiudizio di club | 30% | -30 punti |
| Pregiudizio di nazionalità | 25% | -25 punti |
| Pregiudizio di posizionamento | 20% | -20 punti |
| Concordanza con i pari | 25% | -25 punti |

### Livelli di rischio

| Punteggio | Livello | Significato |
|-----------|---------|-------------|
| **80-100** | Rischio basso (verde) | Il giudice valuta in modo coerente e imparziale |
| **60-79** | Rischio moderato (arancione) | Tendenze rilevate, da monitorare |
| **0-59** | Rischio elevato (rosso) | Pregiudizi significativi rilevati, formazione raccomandata |

---

## Criterio 1: Pregiudizio di Club

### Principio
Questo criterio confronta la media dei punteggi che un giudice attribuisce ai praticanti del **proprio club** rispetto ai praticanti **degli altri club**.

### Calcolo
```
Differenza = Media(punteggi per praticanti dello stesso club) - Media(punteggi per gli altri praticanti)
```

### Soglie di rilevamento

| Differenza (valore assoluto) | Severità | Interpretazione |
|------------------------------|----------|-----------------|
| < 0,3 punti | Neutro | Nessun pregiudizio rilevato |
| 0,3 a 0,5 punti | Basso | Leggero favoritismo o sfavoritismo |
| 0,5 a 0,8 punti | Moderato | Tendenza significativa da monitorare |
| > 0,8 punti | Elevato | Pregiudizio marcato, azione correttiva raccomandata |

### Come interpretare
- **Valore positivo** (+): il giudice tende a valutare più favorevolmente i praticanti del proprio club
- **Valore negativo** (-): il giudice tende a essere più severo con i praticanti del proprio club (sovracompensazione)
- Entrambe le situazioni sono pregiudizi da correggere

### Penalità sul punteggio globale

| Severità | Penalità |
|----------|----------|
| Neutro | 0 punti |
| Basso | -10 punti |
| Moderato | -20 punti |
| Elevato | -30 punti |

---

## Criterio 2: Pregiudizio di Nazionalità

### Principio
Questo criterio confronta la media dei punteggi attribuiti ai praticanti della **stessa nazionalità** del giudice rispetto ai praticanti di **altre nazionalità**.

### Calcolo
```
Differenza = Media(punteggi stessa nazionalità) - Media(punteggi altre nazionalità)
```

### Soglie di rilevamento

| Differenza (valore assoluto) | Severità | Interpretazione |
|------------------------------|----------|-----------------|
| < 0,2 punti | Neutro | Nessun pregiudizio rilevato |
| 0,2 a 0,4 punti | Basso | Leggero favoritismo o sfavoritismo |
| 0,4 a 0,6 punti | Moderato | Tendenza significativa |
| > 0,6 punti | Elevato | Pregiudizio marcato |

### Come interpretare
- **Soglie più rigide** rispetto al pregiudizio di club, poiché la nazionalità non dovrebbe avere alcuna influenza sul punteggio tecnico
- **Valore positivo**: favoritismo verso la propria nazionalità
- **Valore negativo**: severità eccessiva verso la propria nazionalità

### Penalità sul punteggio globale

| Severità | Penalità |
|----------|----------|
| Neutro | 0 punti |
| Basso | -8 punti |
| Moderato | -16 punti |
| Elevato | -25 punti |

---

## Criterio 3: Pregiudizio di Posizionamento

### Principio
Questo criterio confronta la **media generale dei punteggi** di un giudice rispetto alla **media di tutti i giudici** della competizione. Rileva i giudici sistematicamente troppo generosi o troppo severi.

### Calcolo
```
Differenza = Media(tutti i punteggi del giudice) - Media(tutti i punteggi di tutti i giudici)
```

### Soglie di rilevamento

| Differenza (valore assoluto) | Severità | Interpretazione |
|------------------------------|----------|-----------------|
| < 0,2 punti | Neutro | Nella media, punteggio calibrato |
| 0,2 a 0,4 punti | Basso | Leggermente generoso o severo |
| 0,4 a 0,6 punti | Moderato | Generoso o severo in modo notevole |
| > 0,6 punti | Elevato | Molto generoso o molto severo |

### Come interpretare
- **Valore positivo** (+): il giudice valuta sistematicamente al di sopra della media (generoso)
- **Valore negativo** (-): il giudice valuta sistematicamente al di sotto della media (severo)
- Un buon giudice si situa nella fascia neutra (< 0,2 punti di scarto)

### Penalità sul punteggio globale

| Severità | Penalità |
|----------|----------|
| Neutro | 0 punti |
| Basso | -5 punti |
| Moderato | -12 punti |
| Elevato | -20 punti |

---

## Criterio 4: Concordanza con i Pari

### Principio
Questo criterio misura quanto i punteggi di un giudice sono **in accordo con quelli degli altri giudici** per le stesse prestazioni. Un giudice i cui punteggi divergono costantemente dai colleghi può presentare un problema di calibrazione o di pregiudizio.

### Calcolo
Per ogni prestazione valutata dal giudice:
```
Media degli altri = Media(punteggi degli altri giudici per questa prestazione)
Scarto = |Punteggio del giudice - Media degli altri|
Concordanza individuale = max(0, 100 - (Scarto × 20))
```

Il **punteggio di concordanza globale** è la media di tutte le concordanze individuali.

### Interpretazione

| Concordanza | Significato |
|-------------|-------------|
| **90-100%** | Eccellente concordanza, punteggio molto allineato |
| **75-89%** | Buona concordanza |
| **60-74%** | Concordanza accettabile ma da migliorare |
| **< 60%** | Concordanza bassa, **allarme generato** |

### Impatto sul punteggio globale
La concordanza influenza il punteggio di neutralità tramite un bonus/malus:
```
Aggiustamento = (Concordanza - 50) / 2
```
- Concordanza del 100%: bonus di +25 punti
- Concordanza del 50%: né bonus né malus
- Concordanza dello 0%: malus di -25 punti

### Condizioni
- Un minimo di **3 prestazioni** valutate è richiesto affinché il calcolo sia significativo
- Solo i punteggi attivi (non di allenamento) vengono presi in considerazione

---

## Sistema di Allarmi

Gli allarmi vengono generati automaticamente nei seguenti casi:

| Condizione | Allarme |
|------------|---------|
| Pregiudizio di club moderato o elevato | "Pregiudizio club rilevato" con il valore dello scarto |
| Pregiudizio di nazionalità moderato o elevato | "Pregiudizio nazionalità rilevato" con il valore dello scarto |
| Posizionamento elevato solamente | "Posizione estrema" con lo scarto dalla media |
| Concordanza < 60% | "Bassa concordanza con gli altri giudici" |

Gli allarmi sono visibili nella scheda dettagliata di ogni giudice nell'interfaccia di analisi.

---

## Podio dei Giudici Più Imparziali

Alla fine dell'analisi, un **podio** mette in evidenza i 3 giudici che hanno ottenuto i migliori punteggi di neutralità:

- **1° posto (Oro)**: Punteggio di neutralità più alto
- **2° posto (Argento)**: Secondo miglior punteggio
- **3° posto (Bronzo)**: Terzo miglior punteggio

Questa classifica premia l'imparzialità e incoraggia tutti i giudici a migliorare.

---

## Raccomandazioni per i Giudici

### Come migliorare il proprio punteggio di neutralità

1. **Pregiudizio di club**: Fate particolare attenzione quando valutate un praticante del vostro club. Applicate gli stessi criteri tecnici che per gli altri.

2. **Pregiudizio di nazionalità**: Concentratevi esclusivamente sulla tecnica e sull'esecuzione. La nazionalità del praticante non deve influenzare la vostra valutazione.

3. **Posizionamento**: Calibrate i vostri punteggi allineandovi ai criteri definiti. Né troppo generosi né troppo severi. In caso di dubbio, fate riferimento al baremo ufficiale.

4. **Concordanza**: Se i vostri punteggi divergono spesso da quelli dei vostri colleghi, ciò può indicare un problema di comprensione dei criteri. Partecipate alle sessioni di calibrazione.

### Buone pratiche

- Valutate ogni prestazione in modo indipendente, senza guardare i punteggi degli altri giudici
- Utilizzate tutta l'estensione della scala di punteggio
- Non modificate i vostri punteggi dopo aver visto quelli degli altri
- Prendetevi il tempo di valutare ogni criterio separatamente
- In caso di stanchezza, fate una pausa per mantenere la concentrazione

---

## Accesso e Riservatezza

- L'analisi della neutralità è accessibile agli **organizzatori di competizione** e agli **amministratori di federazione**
- Ogni giudice può consultare **i propri risultati**
- I dati sono calcolati in **tempo reale** a partire dai punteggi esistenti (nessun dato di neutralità viene archiviato permanentemente)
- L'analisi richiede un numero sufficiente di punteggi per essere affidabile (minimo 3 prestazioni per la concordanza)
