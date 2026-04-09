# Dashboard MartialComp

## Introduzione

Questa directory contiene la documentazione completa dei diversi dashboard disponibili nell'applicazione MartialComp. Ogni tipo di utente dispone di un dashboard specifico per il suo ruolo, che offre funzionalità adattate alle sue esigenze.

## Tipi di Dashboard

MartialComp propone diversi dashboard, ciascuno progettato per un ruolo specifico:

1. [**Dashboard Partecipante**](./participants/README.md) - Per i praticanti di arti marziali che partecipano alle competizioni
2. [**Dashboard Club**](./clubs/README.md) - Per i gestori di club e i loro amministratori
3. [**Dashboard Federazione**](./federations/README.md) - Per gli amministratori delle federazioni
4. [**Dashboard Arbitro/Giudice**](./referees/README.md) - Per gli arbitri e i giudici che valutano le competizioni
5. [**Dashboard Allenatore Multidisciplina**](./coaches/README.md) - Per gli allenatori che gestiscono più discipline
6. [**Dashboard Combattimento**](./combat/README.md) - Interfaccia specializzata per la gestione dei combattimenti

## Accesso ai Dashboard

Ogni utente viene automaticamente reindirizzato al dashboard corrispondente al suo ruolo dopo il login. Il reindirizzamento è gestito dalla vista `dashboard` nel file `competitions/views/dashboard/base.py`.

## Struttura Comune dei Dashboard

Tutti i dashboard condividono una struttura comune:

- **Intestazione**: Visualizza il nome dell'utente, il ruolo, e dà accesso alle impostazioni e alla disconnessione
- **Barra laterale**: Navigazione verso le diverse sezioni del dashboard
- **Contenuto principale**: Visualizza le informazioni e le funzionalità specifiche di ogni sezione
- **Piè di pagina**: Informazioni sulla versione dell'applicazione e link utili

## Personalizzazione dei Dashboard

Gli utenti possono personalizzare alcuni aspetti del loro dashboard:
- Scelta dei widget visualizzati nella pagina principale
- Ordine di visualizzazione delle informazioni
- Preferenze di notifica

## Funzionalità Comuni

Tutti i dashboard offrono queste funzionalità di base:
- Panoramica con statistiche chiave
- Notifiche e avvisi
- Gestione del profilo utente
- Calendario degli eventi in programma
- Accesso alla documentazione

## Supporto Multilingue

Tutti i dashboard supportano il multilinguismo e sono disponibili nelle seguenti lingue:
- Francese (fr) - Lingua predefinita
- Inglese (en)
- Spagnolo (es)
- Italiano (it)
- Tedesco (de)
- Norvegese (no)
- Giapponese (ja)
- Cinese (zh)
- Hindi (hi)
- Arabo (ar)
- Swahili (sw)
- Amarico (am)
- Zulu (zu)
- Yoruba (yo)
- Portoghese (pt)
- Coreano (ko)

## Progettazione Tecnica

I dashboard sono implementati utilizzando:
- Django per il backend
- HTML/CSS/JavaScript per il frontend
- Bootstrap per il layout responsive
- Tecnologia AJAX per gli aggiornamenti dinamici

## Documentazione Dettagliata

Per maggiori dettagli su ciascun dashboard, consultate i link sopra o esplorate le sottocartelle di questa directory.
