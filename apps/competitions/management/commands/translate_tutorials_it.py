"""
Management command to translate all 81 tutorials from French to Italian.
Updates title_it, steps_it, and tip_it fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_it
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# Structure: {section_order: {title_it, tutorials: {number: {title_it, steps_it, tip_it}}}}
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Sezione 1: Onboarding e Primi Passi (7 tutorial)
    # =========================================================================
    1: {
        'title_it': 'Onboarding e Primi Passi',
        'tutorials': {
            1: {
                'title_it': 'Creare il proprio account e scegliere il ruolo',
                'steps_it': [
                    "Accedere a MartialComp : Vai su martialcomp.com e clicca su 'Iscriviti gratuitamente'. Puoi anche scaricare l'app mobile dal Play Store o dall'App Store.",
                    "Compilare il modulo di registrazione : Inserisci cognome, nome, indirizzo email e password. Puoi anche registrarti tramite Google, Facebook o Apple ID per un accesso semplificato.",
                    "Scegliere il ruolo principale : Seleziona il tuo ruolo: Responsabile Club, Allenatore, Giudice/Arbitro, Praticante o Responsabile Federazione. Questa scelta determina la tua dashboard e le funzionalita, ma potrai aggiungere altri ruoli in seguito.",
                    "Confermare l'email : Controlla la tua casella di posta e clicca sul link di conferma. Il tuo account e ora attivo e puoi accedere alla tua dashboard personalizzata.",
                ],
                'tip_it': 'Puoi avere piu ruoli (es. allenatore E praticante). Passa da un ruolo all\'altro dal menu laterale in qualsiasi momento.',
            },
            2: {
                'title_it': 'Creare il proprio club',
                'steps_it': [
                    "Avviare la procedura guidata : Dalla tua dashboard, clicca su 'Crea un club'. La procedura guidata in 4 passaggi si avvia automaticamente.",
                    "Informazioni generali : Inserisci il nome del club, l'acronimo, l'indirizzo completo e i contatti (telefono, email, sito web). Aggiungi il tuo logo in formato PNG o JPG (dimensione consigliata: 500x500px).",
                    "Scegliere le discipline : Seleziona una o piu discipline tra le 14+ disponibili: Karate, Judo, BJJ, Taekwondo, MMA, Kung Fu, Aikido, Kendo, Muay Thai, Boxe, Capoeira, ecc.",
                    "Personalizzare il sottodominio : Scegli il tuo indirizzo unico: tuo-club.martialcomp.com. Questo sara l'indirizzo pubblico del tuo club, accessibile a tutti.",
                    "Configurare le opzioni : Imposta gli orari di apertura, aggiungi una descrizione e foto del tuo dojo. Attiva o disattiva la registrazione online dei praticanti.",
                ],
                'tip_it': 'Il tuo club viene creato con il piano Gratuito (fino a 10 membri). Tutte le funzionalita sono disponibili fin dall\'inizio. Passa a Premium quando superi i 10 membri.',
            },
            3: {
                'title_it': 'Creare la propria federazione',
                'steps_it': [
                    "Richiedere la creazione : Seleziona il ruolo 'Responsabile Federazione' durante la registrazione o aggiungilo dalle impostazioni. Compila il modulo di creazione con le informazioni ufficiali della tua federazione.",
                    "Informazioni ufficiali : Inserisci il nome completo, l'acronimo, il paese, le discipline coperte, il numero di registrazione ufficiale e i contatti.",
                    "Configurare il sito pubblico : Personalizza la tua pagina pubblica: banner, logo, colori, descrizione, galleria fotografica e link ai tuoi social media.",
                    "Definire la struttura : Configura le leghe regionali se applicabile, definisci le categorie di affiliazione per i club e le tariffe delle quote associative.",
                ],
                'tip_it': 'Le federazioni beneficiano di uno spazio di amministrazione esteso per supervisionare tutti i club affiliati, le competizioni e i gradi.',
            },
            4: {
                'title_it': 'Configurare il profilo allenatore',
                'steps_it': [
                    "Accedere al profilo allenatore : Dal menu laterale, clicca su 'Il mio profilo allenatore'. Se non hai ancora il ruolo allenatore, aggiungilo da Impostazioni > I miei ruoli.",
                    "Inserire le qualifiche : Aggiungi i tuoi diplomi (BPJEPS, DEJEPS, CQP, ecc.), i tuoi gradi in ogni disciplina e i tuoi anni di esperienza.",
                    "Definire le discipline : Seleziona le discipline che insegni e il tuo livello di specializzazione per ognuna (principianti, avanzati, agonismo).",
                    "Impostare la disponibilita : Indica le tue fasce orarie settimanali di insegnamento. Queste informazioni saranno visibili ai club in cerca di allenatori.",
                ],
                'tip_it': 'Un profilo allenatore completo con foto e certificazioni aumenta significativamente la tua visibilita presso i club.',
            },
            5: {
                'title_it': 'Configurare il profilo giudice',
                'steps_it': [
                    "Attivare il ruolo giudice : Da Impostazioni > I miei ruoli, attiva il ruolo 'Giudice / Arbitro'. Inserisci il tuo numero di licenza giudice se applicabile.",
                    "Aggiungere le qualifiche : Indica il tuo livello di giudice (regionale, nazionale, internazionale), le discipline per cui sei qualificato e le tue certificazioni.",
                    "Definire le specialita : Kata/tecniche, combattimento, punteggio artistico... Ogni specialita ti rende idoneo per le competizioni corrispondenti.",
                    "Inserire la disponibilita : Indica le tue zone geografiche e i periodi di disponibilita per le competizioni.",
                ],
                'tip_it': 'Gli organizzatori di competizioni potranno cercarti e invitarti direttamente in base alle tue qualifiche e disponibilita.',
            },
            6: {
                'title_it': 'Configurare il profilo praticante',
                'steps_it': [
                    "Completare le informazioni personali : Inserisci la data di nascita, il sesso, il peso (per le categorie di gara), l'altezza e la foto profilo.",
                    "Aggiungere il grado attuale : Indica la tua disciplina principale, il grado attuale (cintura), la data di conseguimento e l'organismo che lo ha rilasciato.",
                    "Inserire la licenza : Aggiungi il numero di licenza federale, la data di scadenza e il certificato medico valido attuale.",
                    "Contatti di emergenza : Aggiungi almeno un contatto di emergenza (obbligatorio per le competizioni): nome, numero di telefono, relazione.",
                ],
                'tip_it': 'Un profilo completo e necessario per iscriversi alle competizioni. Il peso e il grado determinano automaticamente la tua categoria.',
            },
            7: {
                'title_it': 'Comprendere la dashboard e la navigazione',
                'steps_it': [
                    "La dashboard : La tua dashboard mostra un riepilogo personalizzato: prossimi eventi, messaggi recenti, statistiche rapide e scorciatoie alle tue azioni frequenti.",
                    "La barra laterale : Il menu laterale da accesso a tutte le sezioni: Membri, Competizioni, Gradi, Finanze, Calendario, Impostazioni. Si adatta al tuo ruolo attivo.",
                    "Cambiare ruolo : Se hai piu ruoli (es. allenatore + praticante), clicca sul tuo avatar in alto a destra per cambiare. La dashboard e il menu si adattano automaticamente.",
                    "Notifiche e messaggi : L'icona della campanella in alto a destra mostra le tue notifiche: iscrizioni, risultati, messaggi. Configura le tue preferenze di notifica nelle impostazioni.",
                    "Ricerca globale : Usa la barra di ricerca per trovare rapidamente un praticante, club, competizione o evento.",
                ],
                'tip_it': 'Personalizza la tua dashboard fissando i tuoi widget preferiti. La scorciatoia da tastiera Ctrl+K apre la ricerca rapida.',
            },
        },
    },

    # =========================================================================
    # Sezione 2: Gestione Club (10 tutorial)
    # =========================================================================
    2: {
        'title_it': 'Gestione Club',
        'tutorials': {
            1: {
                'title_it': 'Aggiungere praticanti manualmente',
                'steps_it': [
                    "Aprire il modulo di aggiunta : Da Membri > Aggiungi un praticante, compila il modulo: cognome, nome, data di nascita, sesso, email e telefono.",
                    "Informazioni aggiuntive : Aggiungi il grado attuale, il numero di licenza, la foto identificativa (opzionale) e il certificato medico.",
                    "Assegnare a un gruppo : Assegna il praticante a uno o piu gruppi di allenamento (es. Karate Adulti Avanzato, Judo Bambini Principianti).",
                    "Inviare l'invito : Seleziona 'Invia un invito email' in modo che il praticante possa creare il proprio account e accedere al suo profilo online.",
                ],
                'tip_it': 'Il praticante ricevera un\'email con un link per completare la registrazione e scaricare l\'app mobile.',
            },
            2: {
                'title_it': 'Importazione massiva dei praticanti (CSV/Excel)',
                'steps_it': [
                    "Scaricare il modello : Da Membri > Importa, scarica il modello CSV o Excel. Il file contiene colonne obbligatorie: Cognome, Nome, Data_nascita, Email, e colonne opzionali: Grado, Licenza, Telefono.",
                    "Compilare il file : Completa il file con i dati dei tuoi praticanti. Rispetta i formati: date in GG/MM/AAAA, gradi come testo (es. 'Cintura verde', '2o Dan').",
                    "Caricare e mappare le colonne : Importa il file. L'interfaccia di mappatura ti permette di associare ogni colonna del tuo file ai campi di MartialComp. Verifica la mappatura.",
                    "Validare e correggere : MartialComp rileva gli errori (duplicati, formati non validi). Correggi le righe in errore o saltale. Conferma l'importazione.",
                ],
                'tip_it': 'Puoi importare fino a 500 praticanti in una singola operazione. L\'importazione rileva automaticamente i duplicati per email o cognome + nome + data di nascita.',
            },
            3: {
                'title_it': 'Gestire le schede dei praticanti',
                'steps_it': [
                    "Accedere alla scheda : Dalla lista dei membri, clicca sul nome di un praticante per aprire la sua scheda completa.",
                    "Visualizzare i dettagli : La scheda mostra: informazioni personali, storico dei gradi, competizioni effettuate, presenze e quote associative.",
                    "Modificare le informazioni : Clicca 'Modifica' per aggiornare i dati. Le modifiche sono tracciate nello storico.",
                    "Azioni rapide : Dalla scheda puoi: iscrivere a una competizione, assegnare un grado, inviare un messaggio, generare un certificato.",
                ],
                'tip_it': 'Usa i filtri avanzati (grado, eta, licenza valida, quota pagata) per trovare rapidamente un praticante.',
            },
            4: {
                'title_it': 'Creare un account utente per un praticante',
                'steps_it': [
                    "Accedere alla scheda del praticante : Apri la scheda del praticante interessato dalla lista dei membri.",
                    "Collegare a un account : Clicca 'Crea un account utente'. Un'email di invito verra inviata al praticante con un link per creare la password.",
                    "Impostare i permessi : Scegli cosa puo fare il praticante: visualizzare i risultati, iscriversi alle competizioni, vedere il calendario, pagare online.",
                ],
                'tip_it': 'I praticanti minorenni possono avere un account collegato a quello di un genitore tramite la funzione Gruppo Famiglia.',
            },
            5: {
                'title_it': 'Gestire ruoli e permessi del club',
                'steps_it': [
                    "Accedere alla gestione dei ruoli : Da Impostazioni > Ruoli e permessi, visualizza i ruoli disponibili: Amministratore, Segretario, Tesoriere, Allenatore, Membro.",
                    "Assegnare un ruolo : Seleziona un membro e assegnagli un ruolo. Ogni ruolo da accesso a funzionalita specifiche.",
                    "Personalizzare i permessi : Per ogni ruolo, definisci i diritti: sola lettura, modifica, eliminazione, accesso alle finanze, gestione iscrizioni.",
                    "Controllare gli accessi : Consulta il registro delle attivita per vedere chi ha fatto cosa e quando nell'amministrazione del club.",
                ],
                'tip_it': 'Il ruolo Amministratore ha tutti i diritti. Crea un ruolo Segretario con accesso a membri e calendario ma non alle finanze.',
            },
            6: {
                'title_it': 'Monitorare le presenze / Check-in',
                'steps_it': [
                    "Creare una sessione : Da Presenze > Nuova sessione, seleziona il gruppo di allenamento, la data e l'orario della lezione.",
                    "Registrare per lista : Mostra la lista dei membri del gruppo e spunta i presenti. La registrazione si fa con un solo tocco su mobile.",
                    "Registrare per QR code : Mostra il QR code della sessione. I praticanti lo scansionano con il telefono arrivando al dojo.",
                    "Visualizzare le statistiche : Visualizza i tassi di presenza per praticante, gruppo e periodo. Identifica le assenze ripetute.",
                ],
                'tip_it': 'Il check-in tramite QR code e il metodo piu rapido per gruppi numerosi. Il codice si rinnova ad ogni sessione per prevenire imbrogli.',
            },
            7: {
                'title_it': 'Gestire i programmi di allenamento',
                'steps_it': [
                    "Creare un programma : Da Programmi > Nuovo, definisci il nome, la disciplina, il livello (principiante, intermedio, avanzato) e la durata del ciclo.",
                    "Pianificare le sessioni : Aggiungi le fasce orarie settimanali: giorno, ora di inizio, ora di fine, sala/tatami, allenatore responsabile.",
                    "Definire i contenuti : Per ogni sessione, aggiungi un programma: riscaldamento, lavoro tecnico, sparring/randori, defaticamento. Allega file o video.",
                    "Pubblicare e notificare : Pubblica il programma. I praticanti del gruppo ricevono una notifica con il programma completo.",
                ],
                'tip_it': 'Duplica un programma esistente per creare rapidamente un nuovo ciclo con variazioni.',
            },
            8: {
                'title_it': 'Generare e utilizzare i QR code del club',
                'steps_it': [
                    "Generare il QR code del club : Da Impostazioni > QR Code, genera il QR code del tuo club. Permette ai visitatori di accedere direttamente alla tua pagina pubblica.",
                    "QR code speciali : Genera QR code per: registrazione online, check-in sessione, pagina evento o link all'app mobile.",
                    "Stampare e affiggere : Scarica i QR code in alta risoluzione per la stampa. Formati disponibili: PNG, SVG, PDF (A4 o biglietto da visita).",
                    "Monitorare le statistiche : Visualizza il numero di scansioni per QR code, per giorno e per tipo. Identifica i QR code piu efficaci.",
                ],
                'tip_it': 'Affiggi il QR code di registrazione all\'ingresso del tuo dojo. Ogni scansione e un potenziale cliente!',
            },
            9: {
                'title_it': 'Richiedere l\'affiliazione alla federazione',
                'steps_it': [
                    "Trovare la tua federazione : Da Club > Affiliazione, cerca la tua federazione per nome, disciplina o paese.",
                    "Inviare la richiesta : Compila il modulo di affiliazione: informazioni del club, numero di registrazione, documenti giustificativi (statuto, assicurazione, ecc.).",
                    "Monitorare lo stato : La tua richiesta attraversa fasi: Inviata > In esame > Approvata/Respinta. Ricevi notifiche ad ogni passaggio.",
                    "Rinnovare ogni stagione : L'affiliazione e stagionale. Un promemoria automatico viene inviato 30 giorni prima della scadenza.",
                ],
                'tip_it': 'L\'affiliazione ti da accesso alle competizioni ufficiali della federazione e alla gestione centralizzata delle licenze.',
            },
            10: {
                'title_it': 'Gestire i trasferimenti dei praticanti',
                'steps_it': [
                    "Avviare un trasferimento : Dalla scheda di un praticante, clicca 'Richiedi un trasferimento'. Seleziona il club di destinazione e il motivo del trasferimento.",
                    "Processo di validazione : Il club di destinazione riceve la richiesta e puo accettarla o rifiutarla. Se coinvolta una federazione, anch'essa deve validare.",
                    "Trasferimento effettivo : Una volta validato, il praticante viene automaticamente trasferito con il suo grado e lo storico delle competizioni.",
                    "Visualizzare lo storico : Lo storico dei trasferimenti e visibile nella scheda del praticante e nei rapporti del club.",
                ],
                'tip_it': 'Alcune federazioni impongono periodi di trasferimento (finestre di mercato). MartialComp rispetta automaticamente queste regole.',
            },
        },
    },

    # =========================================================================
    # Sezione 3: Competizioni - Creazione e Configurazione (6 tutorial)
    # =========================================================================
    3: {
        'title_it': 'Competizioni - Creazione e Configurazione',
        'tutorials': {
            1: {
                'title_it': 'Creare una competizione individuale',
                'steps_it': [
                    "Avviare la creazione : Da Competizioni > Crea, scegli il tipo 'Individuale'. Inserisci il nome, la/le disciplina/e, le date e il luogo.",
                    "Definire il formato : Scegli il formato: Combattimento (kumite, randori, sparring), Tecnico (kata, poomsae, forme) o Misto (entrambi).",
                    "Configurare le categorie : Definisci le categorie per sesso, fascia d'eta, peso e/o grado. MartialComp offre modelli di categorie standard per disciplina.",
                    "Opzioni e pubblicazione : Attiva le opzioni desiderate: iscrizione online, pagamento, streaming in diretta, risultati pubblici. Pubblica la competizione.",
                ],
                'tip_it': 'Usa i modelli di categorie (WKF, IJF, ITF...) per risparmiare tempo. Puoi personalizzarli dopo la creazione.',
            },
            2: {
                'title_it': 'Creare una competizione a squadre (Sincro/Song Luyen)',
                'steps_it': [
                    "Scegliere la modalita squadra : Durante la creazione, seleziona il tipo 'Squadra'. Definisci il numero minimo e massimo di membri per squadra.",
                    "Configurare il formato squadra : Scegli il formato: Sincronizzazione (kata/poomsae di squadra), Song Luyen (combattimento preordinato a due) o Combattimento a squadre (staffetta).",
                    "Definire la composizione : Specifica i ruoli all'interno della squadra: numero di titolari, numero di riserve, se le composizioni miste sono consentite o meno.",
                    "Criteri di punteggio squadra : Per il punteggio tecnico, definisci se i giudici valutano la squadra nel suo insieme o ogni membro individualmente.",
                ],
                'tip_it': 'La modalita Sincro permette il punteggio con criteri di sincronizzazione specifici (tempismo, allineamento, espressione condivisa).',
            },
            3: {
                'title_it': 'Configurare le categorie di competizione',
                'steps_it': [
                    "Accedere alla gestione categorie : Dalla competizione creata, vai alla scheda Categorie. Clicca 'Aggiungi una categoria'.",
                    "Definire i criteri : Per ogni categoria, definisci: sesso (M/F/Misto), fascia d'eta (es. 12-14 anni), fascia di peso (es. -60kg), grado minimo/massimo.",
                    "Nominare la categoria : Dai un nome chiaro: 'Cadetti Maschi -52kg' o 'Kata Adulti Donne Avanzato'. MartialComp genera nomi automatici se preferisci.",
                    "Ordinare le categorie : Riordina le categorie tramite trascinamento per stabilire l'ordine di apparizione il giorno della competizione.",
                ],
                'tip_it': 'Importa le categorie da una competizione precedente per risparmiare tempo. Usa l\'opzione \'Duplicazione Intelligente\' per creare varianti.',
            },
            4: {
                'title_it': 'Duplicare una competizione esistente',
                'steps_it': [
                    "Trovare la competizione sorgente : Da Competizioni > Storico, trova la competizione che vuoi duplicare.",
                    "Avviare la duplicazione : Clicca i 3 punti > Duplica. Scegli cosa copiare: categorie, regolamento, impostazioni, tariffe.",
                    "Adattare le impostazioni : Modifica le date, il luogo e i parametri necessari. Categorie e regolamento vengono copiati identicamente.",
                ],
                'tip_it': 'Ideale per le competizioni annuali ricorrenti. Duplica l\'edizione precedente e aggiorna semplicemente le date.',
            },
            5: {
                'title_it': 'Configurare le opzioni di visibilita',
                'steps_it': [
                    "Accedere alle impostazioni di visibilita : Dalla competizione, vai a Impostazioni > Visibilita e condivisione.",
                    "Iscrizioni online : Attiva/disattiva le iscrizioni pubbliche. Imposta le date di apertura e chiusura delle iscrizioni.",
                    "Risultati e classifiche : Scegli se i risultati sono pubblici in tempo reale, pubblicati dopo la validazione o privati (solo organizzatore).",
                    "Streaming in diretta : Attiva la modalita streaming e aggiungi il link YouTube/Twitch/Facebook Live per la visualizzazione sulla pagina pubblica.",
                ],
                'tip_it': 'I risultati in diretta attirano spettatori sulla tua pagina e aumentano la visibilita del tuo club o federazione.',
            },
            6: {
                'title_it': 'Configurare le regole di combattimento',
                'steps_it': [
                    "Scegliere un regolamento : Seleziona un regolamento preconfigurato (WKF, IJF, ITF, IBJJF, ecc.) o creane uno personalizzato.",
                    "Definire il punteggio : Configura le azioni e i loro punti: Yuko (1pt), Waza-ari (2pt), Ippon (3pt), ecc. Aggiungi le penalita (Shido, Hansoku, ecc.).",
                    "Configurare i round : Definisci la durata dei round, il numero di round, le pause e le condizioni di vittoria (punti, Ippon, forfait).",
                    "Regole speciali : Configura le regole specifiche: Golden Score (supplementari), Hantei (decisione dei giudici), fine anticipata per distacco.",
                ],
                'tip_it': 'Salva i tuoi regolamenti personalizzati come modelli per riutilizzarli nelle competizioni future.',
            },
        },
    },

    # =========================================================================
    # Sezione 4: Iscrizioni e Squadre (7 tutorial)
    # =========================================================================
    4: {
        'title_it': 'Iscrizioni e Squadre',
        'tutorials': {
            1: {
                'title_it': 'Iscrivere praticanti a una competizione',
                'steps_it': [
                    "Trovare la competizione : Da Competizioni > Aperte alle iscrizioni, trova la competizione desiderata e clicca 'Iscrivi'.",
                    "Selezionare i praticanti : La lista dei tuoi membri viene mostrata. Seleziona uno o piu praticanti. MartialComp indica automaticamente le categorie ammissibili per ciascuno.",
                    "Confermare le categorie : Per ogni praticante, conferma o cambia la categoria proposta. Il sistema verifica che peso, eta e grado corrispondano.",
                    "Validare e pagare : Conferma le iscrizioni. Se la competizione richiede il pagamento, procedi al pagamento per tutte le iscrizioni.",
                ],
                'tip_it': 'I praticanti con un profilo incompleto (peso mancante, licenza scaduta) saranno segnalati con un avviso rosso.',
            },
            2: {
                'title_it': 'Iscrizione massiva tramite modulo',
                'steps_it': [
                    "Accedere alla modalita massiva : Dalla schermata di iscrizione, clicca 'Iscrizione massiva'. Seleziona la categoria di destinazione.",
                    "Selezionare il gruppo : Filtra per gruppo di allenamento, grado o eta. Seleziona i praticanti idonei con un solo clic.",
                    "Verificare e adattare : La schermata di verifica mostra ogni praticante con la sua categoria. Correggi eventuali errori.",
                    "Confermare il lotto : Valida tutte le iscrizioni in un'unica operazione. Un riepilogo viene inviato per email.",
                ],
                'tip_it': 'L\'iscrizione massiva e ideale per i club che iscrivono 10+ praticanti alla stessa competizione.',
            },
            3: {
                'title_it': 'Creare e gestire le squadre',
                'steps_it': [
                    "Creare una squadra : Dalla competizione, clicca 'Iscrivi una squadra'. Dai un nome alla squadra e seleziona la categoria.",
                    "Aggiungere i membri : Aggiungi i membri della squadra dalla tua lista di praticanti. Rispetta i numeri minimi e massimi definiti.",
                    "Impostare titolari e riserve : Designa titolari e riserve tramite trascinamento. L'ordine di apparizione puo essere impostato qui.",
                    "Validare la squadra : Verifica la conformita della squadra (numero di membri, categorie individuali) e conferma l'iscrizione.",
                ],
                'tip_it': 'Nelle competizioni a squadre, il nome della squadra appare sui tabelloni e nei risultati ufficiali.',
            },
            4: {
                'title_it': 'Cambiare la categoria di una squadra',
                'steps_it': [
                    "Accedere alla squadra : Dalle tue iscrizioni, trova la squadra da modificare e clicca 'Modifica'.",
                    "Cambiare la categoria : Seleziona la nuova categoria dal menu a discesa. Il sistema verifica che la squadra soddisfi i criteri.",
                    "Confermare la modifica : Valida. Se la competizione ha tariffe di iscrizione diverse per categoria, l'adeguamento e automatico.",
                ],
                'tip_it': 'Il cambio di categoria e possibile solo finche le iscrizioni sono ancora aperte.',
            },
            5: {
                'title_it': 'Richiedere un\'intesa (fusione inter-club)',
                'steps_it': [
                    "Identificare la necessita : Il tuo club non ha abbastanza membri per formare una squadra completa? L'intesa permette di fondere squadre di club diversi.",
                    "Creare la richiesta di intesa : Dalla squadra incompleta, clicca 'Proponi un'intesa'. Seleziona il club partner e i posti da occupare.",
                    "Inviare la proposta : Il club partner riceve la richiesta con i dettagli: competizione, categoria, posti disponibili, condizioni.",
                    "Finalizzare l'intesa : Una volta accettata, la squadra fusa appare con i membri di entrambi i club. La squadra porta un nome che combina i due club.",
                ],
                'tip_it': 'L\'intesa e soggetta all\'approvazione dell\'organizzatore della competizione e, se applicabile, della federazione.',
            },
            6: {
                'title_it': 'Accettare/rifiutare una richiesta di intesa',
                'steps_it': [
                    "Ricevere la notifica : Ricevi una notifica di richiesta di intesa. Cliccaci sopra per vedere i dettagli.",
                    "Esaminare la proposta : Verifica: il club richiedente, la competizione, la categoria, i posti da occupare e le condizioni proposte.",
                    "Accettare o rifiutare : Clicca 'Accetta' per validare l'intesa e selezionare i tuoi membri, o 'Rifiuta' con un messaggio esplicativo.",
                ],
                'tip_it': 'Puoi proporre una controproposta modificando le condizioni prima di accettare.',
            },
            7: {
                'title_it': 'Gestire le iscrizioni ricevute (approvazione)',
                'steps_it': [
                    "Accedere al pannello iscrizioni : Dalla competizione, vai alla scheda Iscrizioni. Visualizza le iscrizioni per stato: In attesa, Approvate, Respinte.",
                    "Esaminare e approvare : Clicca su un'iscrizione per verificare le informazioni del praticante. Approva individualmente o in blocco.",
                    "Respingere con motivazione : In caso di rifiuto, seleziona un motivo: categoria errata, licenza non valida, iscrizione tardiva, ecc.",
                    "Esportare la lista : Esporta la lista degli iscritti validi in CSV o PDF per il peso e la gestione il giorno della competizione.",
                ],
                'tip_it': 'Attiva l\'approvazione automatica se non vuoi validare manualmente ogni iscrizione.',
            },
        },
    },

    # =========================================================================
    # Sezione 5: Giorno di Gara - Combattimento (8 tutorial)
    # =========================================================================
    5: {
        'title_it': 'Giorno di Gara - Combattimento',
        'tutorials': {
            1: {
                'title_it': 'Generare i gironi automaticamente',
                'steps_it': [
                    "Accedere alla gestione gironi : Dalla competizione, vai a Gironi > Genera automaticamente. Seleziona le categorie da elaborare.",
                    "Configurare la distribuzione : Definisci: numero di concorrenti per girone, separazione dei membri dello stesso club, teste di serie manuali (opzionale).",
                    "Generare e verificare : Clicca 'Genera'. MartialComp distribuisce i concorrenti evitando scontri intra-club al primo turno.",
                    "Regolare manualmente : Se necessario, sposta i concorrenti tra i gironi tramite trascinamento. Il sistema controlla i conflitti in tempo reale.",
                ],
                'tip_it': 'L\'algoritmo di distribuzione garantisce equita separando i club e bilanciando i livelli di abilita tra i gironi.',
            },
            2: {
                'title_it': 'Organizzare e riorganizzare i gironi',
                'steps_it': [
                    "Panoramica dei gironi : La schermata dei gironi mostra tutte le categorie con il numero di concorrenti, gironi e stato (bozza, validato, in corso).",
                    "Modificare un girone : Clicca su un girone per vedere i concorrenti. Usa il trascinamento per spostare un concorrente in un altro girone.",
                    "Gestire le assenze : Segna un concorrente come assente o ritirato. Il sistema ricalcola automaticamente gli incontri e le classifiche.",
                    "Validare i gironi : Una volta soddisfatto, valida i gironi. Questa azione genera automaticamente la tabella degli incontri.",
                ],
                'tip_it': 'Valida i gironi categoria per categoria per iniziare i combattimenti delle prime categorie mentre finalizzi le altre.',
            },
            3: {
                'title_it': 'Pianificare il calendario dei combattimenti',
                'steps_it': [
                    "Definire le aree di combattimento : Da Programma > Aree, definisci il numero di tatami/ring disponibili e i loro nomi (Tatami 1, Ring A, ecc.).",
                    "Assegnare le fasce orarie : Trascina le categorie sulle aree e le fasce orarie. MartialComp calcola automaticamente la durata stimata.",
                    "Rilevare i conflitti : Il sistema rileva i conflitti: un concorrente iscritto in 2 categorie allo stesso tempo. Usa gli avvisi per regolare.",
                    "Pubblicare il programma : Pubblica il programma. Concorrenti, allenatori e giudici ricevono una notifica con i loro orari di passaggio.",
                ],
                'tip_it': 'Prevedi il 20% di tempo extra per categoria per gestire gli inevitabili ritardi.',
            },
            4: {
                'title_it': 'Utilizzare l\'interfaccia di combattimento (punteggio in diretta)',
                'steps_it': [
                    "Connettersi all'area : Sul tuo tablet o telefono, apri MartialComp e seleziona l'area di combattimento assegnata. Inserisci il tuo PIN giudice.",
                    "L'interfaccia di punteggio : Lo schermo mostra: i 2 concorrenti (rosso/blu), i pulsanti azione (punti, penalita), il cronometro e il punteggio attuale.",
                    "Assegnare i punti : Premi i pulsanti di punteggio: Yuko (+1), Waza-ari (+2), Ippon (+3) per il concorrente rosso o blu. I punti si aggiornano in tempo reale.",
                    "Gestire le penalita : Premi Penalita per assegnare un avvertimento (Shido) o una squalifica (Hansoku). Le penalita sono cumulative.",
                    "Terminare il combattimento : Il cronometro si ferma automaticamente. Valida il risultato (vittoria per punti, Ippon, forfait). La classifica si aggiorna istantaneamente.",
                ],
                'tip_it': 'L\'interfaccia e ottimizzata per tablet in modalita orizzontale. I pulsanti sono volutamente grandi per un uso rapido e senza errori.',
            },
            5: {
                'title_it': 'Modalita Chiosco multi-tatami',
                'steps_it': [
                    "Attivare la modalita Chiosco : Da Impostazioni > Modalita Chiosco, attiva la modalita e imposta un codice PIN per ogni area di combattimento.",
                    "Configurare ogni tablet : Su ogni tablet dell'area, accedi e seleziona l'area corrispondente. Inserisci il PIN per bloccare lo schermo su quest'area.",
                    "Gestione indipendente : Ogni area funziona autonomamente: punteggio, cronometro, visualizzazione. Il tabellone centrale si aggiorna in tempo reale.",
                    "Schermo spettatori : Collega uno schermo aggiuntivo in modalita 'Spettatore' per mostrare il punteggio in grande formato, visibile dalle tribune.",
                ],
                'tip_it': 'La modalita Chiosco impedisce ai giudici di navigare accidentalmente fuori dall\'interfaccia di punteggio.',
            },
            6: {
                'title_it': 'Seguire le classifiche in diretta',
                'steps_it': [
                    "Dashboard in diretta : La schermata di monitoraggio mostra in tempo reale: combattimenti in corso per area, classifiche dei gironi, avanzamento verso le fasi finali.",
                    "Filtrare per categoria : Seleziona una categoria per vedere i dettagli: gironi completati, in corso e in programma, con classifiche provvisorie.",
                    "Notifiche automatiche : Il sistema notifica automaticamente gli allenatori quando i loro concorrenti devono presentarsi all'area di combattimento.",
                ],
                'tip_it': 'Mostra la dashboard su un grande schermo nella zona accoglienza per permettere a tutti i partecipanti di seguire l\'avanzamento.',
            },
            7: {
                'title_it': 'Generare le fasi finali (semifinali/finali)',
                'steps_it': [
                    "Gironi completati : Una volta completati tutti i gironi di una categoria, il sistema calcola i qualificati secondo le regole definite (1o e 2o per girone, ecc.).",
                    "Generare il tabellone : Clicca 'Genera fasi finali'. Il tabellone a eliminazione (quarti, semifinali, finale, finale per il bronzo) viene generato automaticamente.",
                    "Gestire i ripescaggi : Se le regole lo prevedono, i ripescaggi vengono generati automaticamente con i perdenti delle semifinali.",
                    "Lanciare le finali : I combattimenti delle fasi finali appaiono nel programma. Il punteggio funziona come per i gironi.",
                ],
                'tip_it': 'Il tabellone a eliminazione viene generato automaticamente evitando, quando possibile, gli scontri tra concorrenti dello stesso club.',
            },
            8: {
                'title_it': 'Gestire la cerimonia del podio',
                'steps_it': [
                    "Accedere al podio : Dalla categoria completata, clicca 'Podio'. La classifica finale viene mostrata: Oro, Argento, Bronzo (ed eventualmente 2 bronzi).",
                    "Visualizzazione progressiva : Usa la modalita 'Cerimonia' per una visualizzazione progressiva: 3o, poi 2o, poi 1o, con animazioni e effetti sonori.",
                    "Proiettare su grande schermo : Collega la modalita Presentazione a un proiettore per una visualizzazione spettacolare durante la premiazione.",
                    "Condividere i risultati : I podi vengono automaticamente pubblicati sulla pagina della competizione e possono essere condivisi sui social media.",
                ],
                'tip_it': 'Scatta una foto del podio e aggiungila alla competizione per arricchire la galleria e i social media.',
            },
        },
    },

    # =========================================================================
    # Sezione 6: Punteggio Tecnico (6 tutorial)
    # =========================================================================
    6: {
        'title_it': 'Punteggio Tecnico',
        'tutorials': {
            1: {
                'title_it': 'Configurare i criteri di punteggio',
                'steps_it': [
                    "Accedere ai criteri : Dalla competizione, vai a Punteggio > Criteri. Seleziona un modello o crea i tuoi criteri.",
                    "Definire i criteri : Aggiungi criteri di valutazione: Tecnica (posizioni, transizioni), Potenza (kime, dinamica), Ritmo (tempo, fluidita), Espressione (zanshin, spirito).",
                    "Assegnare i pesi : Definisci il peso di ogni criterio: es. Tecnica 40%, Potenza 25%, Ritmo 20%, Espressione 15%. Il totale deve essere 100%.",
                    "Definire la scala : Scegli la scala di valutazione: 1-5, 1-10, 5.0-10.0 o personalizzata. Definisci l'incremento (0.1, 0.5 o 1).",
                ],
                'tip_it': 'I modelli WKF e WTF sono preconfigurati. Personalizzali secondo le tue esigenze specifiche.',
            },
            2: {
                'title_it': 'Assegnare i giudici alle categorie',
                'steps_it': [
                    "Aprire il pannello di assegnazione : Da Punteggio > Giudici, visualizza la lista dei giudici registrati e le categorie da coprire.",
                    "Assegnare per categoria : Trascina i giudici sulle categorie. Definisci il numero di giudici per categoria (solitamente 5 o 7).",
                    "Verifica di neutralita : MartialComp verifica automaticamente i conflitti di interesse: un giudice non puo valutare un concorrente del proprio club.",
                    "Gestire le rotazioni : Pianifica le rotazioni dei giudici tra le categorie per prevenire la stanchezza e mantenere l'equita.",
                ],
                'tip_it': 'Il sistema di rilevamento dei pregiudizi analizza gli scarti di punteggio tra i giudici e avvisa se un giudice valuta sistematicamente troppo alto o troppo basso.',
            },
            3: {
                'title_it': 'Utilizzare la scheda di punteggio tecnico',
                'steps_it': [
                    "Accedere come giudice : Sul tuo tablet, accedi con il tuo account giudice. Seleziona la categoria assegnata.",
                    "Interfaccia di punteggio : Lo schermo mostra il concorrente attuale, i criteri di valutazione e il tastierino numerico. Ogni criterio ha il proprio cursore o tastierino.",
                    "Valutare per turno : Per ogni concorrente, inserisci il tuo punteggio per ogni criterio. Valida la tua valutazione prima di passare al prossimo.",
                    "Salvare : La tua valutazione viene salvata istantaneamente. Puoi modificare i tuoi punteggi finche il turno non viene bloccato dall'organizzatore.",
                ],
                'tip_it': 'L\'interfaccia digitale e ottimizzata per un inserimento rapido su tablet. Un solo tocco per ogni punteggio.',
            },
            4: {
                'title_it': 'Punteggio tecnico di squadra (Sincro)',
                'steps_it': [
                    "Capire la modalita squadra : Nel punteggio Sincro, appaiono criteri aggiuntivi: Sincronizzazione, Allineamento Spaziale, Espressione Condivisa.",
                    "Valutare la squadra nel suo insieme : Se configurato cosi, valuta la squadra nel suo insieme per ogni criterio, inclusa la sincronizzazione.",
                    "Valutare individualmente + squadra : Se configurato per la valutazione mista, valuta ogni membro individualmente POI aggiungi un punteggio squadra per la sincronizzazione.",
                ],
                'tip_it': 'In modalita Sincro, il criterio di sincronizzazione rappresenta tipicamente il 20-30% del punteggio totale.',
            },
            5: {
                'title_it': 'Bloccare e pubblicare i punteggi',
                'steps_it': [
                    "Verificare i punteggi : Dal pannello organizzatore, visualizza i punteggi di tutti i giudici per ogni concorrente. Identifica gli scarti sospetti.",
                    "Bloccare un turno : Clicca 'Blocca' per impedire qualsiasi modifica. Il calcolo finale (rimuovi punteggio piu alto/piu basso, media) viene effettuato.",
                    "Pubblicare i risultati : Pubblica le classifiche. I punteggi dettagliati per giudice possono essere nascosti o visibili secondo la tua configurazione.",
                    "Modalita test / reset : Prima della competizione, usa la modalita test per verificare il sistema. Il reset cancella tutti i punteggi di prova.",
                ],
                'tip_it': 'Il blocco turno per turno permette di pubblicare i risultati turno per turno mentre la competizione continua.',
            },
            6: {
                'title_it': 'Visualizzare le classifiche provvisorie',
                'steps_it': [
                    "Accedere alle classifiche : Dalla scheda Classifiche, visualizza le classifiche in tempo reale con i punteggi per criterio e il punteggio finale.",
                    "Ordinare e filtrare : Ordina per punteggio totale o per criterio specifico. Filtra per girone o tutti i concorrenti.",
                    "Statistiche dei giudici : Visualizza le statistiche: media per giudice, deviazione standard, rilevamento pregiudizi. Uno strumento essenziale per l'equita.",
                ],
                'tip_it': 'La classifica provvisoria e visibile solo a organizzatori e giudici. Viene pubblicata ai concorrenti solo dopo il blocco.',
            },
        },
    },

    # =========================================================================
    # Sezione 7: Risultati e Classifiche (4 tutorial)
    # =========================================================================
    7: {
        'title_it': 'Risultati e Classifiche',
        'tutorials': {
            1: {
                'title_it': 'Visualizzare i risultati della competizione',
                'steps_it': [
                    "Trovare la competizione : Dal menu Competizioni o dalla pagina pubblica, seleziona la competizione desiderata.",
                    "Sfogliare i risultati : I risultati sono organizzati per categoria. Per ogni categoria: podio, classifica completa e dettagli dei punteggi.",
                    "Dettagli del combattimento : Clicca su un combattimento per vedere i dettagli: punteggio per round, penalita, cronometro e eventualmente il video del combattimento.",
                ],
                'tip_it': 'I risultati pubblici sono accessibili senza account MartialComp tramite il link della competizione.',
            },
            2: {
                'title_it': 'Pubblicare e condividere i risultati',
                'steps_it': [
                    "Validare i risultati : Dal pannello organizzatore, rivedi i risultati di ogni categoria. Clicca 'Valida e pubblica'.",
                    "Generare il link pubblico : Viene generato un link permanente alla pagina dei risultati. Copialo per condividerlo.",
                    "Condividere sui social : Usa i pulsanti di condivisione integrati per pubblicare su Facebook, Instagram, Twitter. I podi generano automaticamente un'immagine.",
                    "QR code dei risultati : Genera un QR code dei risultati da esporre nel luogo della competizione per gli spettatori.",
                ],
                'tip_it': 'L\'immagine automatica del podio e formattata per le Instagram Stories (9:16) e Facebook (16:9).',
            },
            3: {
                'title_it': 'Esportare i risultati (CSV/PDF)',
                'steps_it': [
                    "Accedere all'esportazione : Da Risultati > Esporta, scegli il formato: CSV (dati grezzi), PDF (rapporto formattato) o Excel.",
                    "Scegliere il contenuto : Seleziona: Classifica generale, Solo podi, Dettaglio per categoria, Rapporto medaglie per club o Tutto.",
                    "Personalizzare il PDF : Per il PDF, scegli il modello: rapporto ufficiale (con logo federazione), rapporto semplice o diplomi.",
                ],
                'tip_it': 'Il rapporto medaglie per club e particolarmente utile per federazioni e sponsor.',
            },
            4: {
                'title_it': 'Consultare il proprio palmares personale',
                'steps_it': [
                    "Accedere a Il mio palmares : Dal tuo profilo praticante, clicca 'Palmares'. Lo storico delle tue competizioni viene visualizzato.",
                    "Visualizzare le statistiche : Verifica: numero di competizioni, medaglie (oro/argento/bronzo), percentuale di vittorie, progressione nel tempo.",
                    "Condividere il palmares : Genera un link pubblico al tuo palmares o esportalo in PDF per i tuoi fascicoli di candidatura o sponsorizzazione.",
                ],
                'tip_it': 'Il tuo palmares si aggiorna automaticamente dopo ogni competizione. E visibile sul tuo profilo pubblico se lo consenti.',
            },
        },
    },

    # =========================================================================
    # Sezione 8: Gestione dei Gradi (5 tutorial)
    # =========================================================================
    8: {
        'title_it': 'Gestione dei Gradi',
        'tutorials': {
            1: {
                'title_it': 'Configurare il sistema dei gradi',
                'steps_it': [
                    "Accedere alla configurazione : Da Impostazioni > Gradi, seleziona la disciplina e definisci il tuo sistema di gradi.",
                    "Creare i livelli : Aggiungi i livelli in ordine: Cintura bianca, Gialla, Arancione, Verde, Blu, Marrone, Nera 1o Dan, 2o Dan, ecc.",
                    "Definire i prerequisiti : Per ogni grado, definisci: tempo minimo al grado precedente, eta minima, numero minimo di lezioni, se e necessario un esame.",
                    "Assegnare i colori : Assegna i colori delle cinture per la visualizzazione nell'interfaccia e nei profili.",
                ],
                'tip_it': 'I sistemi di gradi standard (Judo, Karate, TKD, BJJ) sono preconfigurati. Puoi personalizzarli o crearne di nuovi.',
            },
            2: {
                'title_it': 'Assegnare un grado a un praticante',
                'steps_it': [
                    "Accedere alla scheda : Dalla scheda del praticante, clicca sulla scheda Gradi poi 'Assegna un nuovo grado'.",
                    "Selezionare il grado : Scegli il grado dalla lista. Il sistema verifica automaticamente i prerequisiti (tempo, eta, esami).",
                    "Inserire i dettagli : Aggiungi la data di assegnazione, il luogo, la giuria/esaminatore e le eventuali osservazioni.",
                    "Assegnazione massiva : Da Gradi > Assegnazione massiva, seleziona piu praticanti e assegna lo stesso grado a tutti.",
                ],
                'tip_it': 'Un\'email di congratulazioni viene automaticamente inviata al praticante con il suo nuovo grado.',
            },
            3: {
                'title_it': 'Organizzare un esame di grado',
                'steps_it': [
                    "Creare l'esame : Da Gradi > Esami, crea un nuovo esame: data, luogo, disciplina, gradi coperti, giuria.",
                    "Iscrivere i candidati : Aggiungi i candidati manualmente o consenti l'auto-iscrizione. Il sistema verifica i prerequisiti di ciascuno.",
                    "Il giorno dell'esame : Usa l'interfaccia esame per valutare ogni candidato: tecniche richieste, combattimento, teoria.",
                    "Pubblicare i risultati : Valida i promossi e i bocciati. I gradi vengono automaticamente assegnati ai candidati che hanno superato l'esame.",
                ],
                'tip_it': 'Gli esami di grado possono essere collegati a una competizione (es. promozione di grado durante un torneo).',
            },
            4: {
                'title_it': 'Gestire lo storico e la progressione dei gradi',
                'steps_it': [
                    "Visualizzare lo storico : La scheda di ogni praticante mostra lo storico completo dei gradi: data, luogo, giuria, osservazioni.",
                    "Visualizzare la progressione : Un grafico mostra la progressione nel tempo. Confronta con la media del club.",
                    "Revocare un grado : In caso di errore, revoca un grado con una motivazione. Lo storico conserva la traccia della revoca.",
                ],
                'tip_it': 'Lo storico dei gradi e trasferibile se il praticante cambia club.',
            },
            5: {
                'title_it': 'Generare certificati di grado',
                'steps_it': [
                    "Accedere ai certificati : Da Gradi > Certificati, seleziona il praticante e il grado per cui generare un certificato.",
                    "Scegliere il modello : Seleziona un modello di certificato: ufficiale (con logo federazione), club o personalizzato.",
                    "Personalizzare : Aggiungi le firme, il timbro del club e le eventuali menzioni speciali. Il QR code di verifica viene aggiunto automaticamente.",
                    "Generare e distribuire : Genera il PDF. Stampa o invia per email. Il QR code permette a chiunque di verificare l'autenticita del certificato.",
                ],
                'tip_it': 'Il QR code di verifica rimanda a una pagina pubblica MartialComp che conferma la validita del grado.',
            },
        },
    },

    # =========================================================================
    # Sezione 9: Gestione Federazione (8 tutorial)
    # =========================================================================
    9: {
        'title_it': 'Gestione Federazione',
        'tutorials': {
            1: {
                'title_it': 'Gestire i club affiliati',
                'steps_it': [
                    "Panoramica : La dashboard della federazione mostra la mappa dei club affiliati, il loro stato (attivo, in attesa, scaduto) e le statistiche.",
                    "Elaborare le richieste : Le nuove richieste di affiliazione appaiono in Club > In attesa. Esamina i documenti e approva o respingi.",
                    "Monitorare i rinnovi : Visualizza le affiliazioni in scadenza. Invia promemoria automatici 30, 15 e 7 giorni prima.",
                ],
                'tip_it': 'La dashboard della federazione fornisce una visione in tempo reale del numero totale di praticanti tesserati in tutti i club.',
            },
            2: {
                'title_it': 'Gestire stagioni e quote associative',
                'steps_it': [
                    "Creare una stagione : Da Stagioni > Nuova, definisci le date di inizio e fine e le tariffe delle quote per tipo (club, individuale, junior, senior).",
                    "Configurare le quote : Definisci gli importi per categoria: affiliazione club (fisso), licenza individuale (per praticante), assicurazione (opzionale).",
                    "Monitorare i pagamenti : Visualizza le quote ricevute, in attesa e in ritardo in tempo reale. Invia promemoria automatici.",
                    "Chiudere la stagione : A fine stagione, chiudila per generare il rapporto finanziario e preparare la stagione successiva.",
                ],
                'tip_it': 'Le quote possono essere pagate online tramite Stripe o tramite bonifico bancario. Il monitoraggio e automatico in entrambi i casi.',
            },
            3: {
                'title_it': 'Supervisionare le competizioni',
                'steps_it': [
                    "Visione globale : Il calendario della federazione mostra tutte le competizioni dei club affiliati, con stato e numero di partecipanti.",
                    "Omologare una competizione : I club sottomettono le loro competizioni per l'omologazione. Verifica le regole, i giudici e valida.",
                    "Visualizzare i risultati : Accedi ai risultati di tutte le competizioni omologate. Le classifiche nazionali si aggiornano automaticamente.",
                ],
                'tip_it': 'Le competizioni omologate dalla federazione sono evidenziate nell\'elenco e nel calendario pubblico.',
            },
            4: {
                'title_it': 'Gestire i giudici e le loro qualifiche',
                'steps_it': [
                    "Database dei giudici : Visualizza il database dei giudici affiliati con le loro qualifiche, specialita e storico delle attivita.",
                    "Gestire i livelli : Assegna i livelli di qualifica: regionale, nazionale, internazionale. Definisci i criteri di promozione.",
                    "Monitoraggio della neutralita : MartialComp analizza le statistiche di punteggio di ogni giudice e rileva potenziali pregiudizi.",
                ],
                'tip_it': 'I giudici con uno storico di punteggio equilibrato vengono evidenziati per le competizioni importanti.',
            },
            5: {
                'title_it': 'Gestire le certificazioni',
                'steps_it': [
                    "Creare un modello : Progetta i tuoi modelli di certificato con il logo della federazione, le menzioni legali e i campi dinamici.",
                    "Emettere certificati : Genera certificati per: gradi, qualifiche dei giudici, diplomi di insegnamento, varie attestazioni.",
                    "Verifica pubblica : Ogni certificato ha un QR code unico. Chiunque puo scansionarlo per verificare l'autenticita su martialcomp.com.",
                ],
                'tip_it': 'I certificati digitali sono a prova di manomissione grazie al QR code di verifica collegato a MartialComp.',
            },
            6: {
                'title_it': 'Personalizzare il sito pubblico della federazione',
                'steps_it': [
                    "Accedere al costruttore del sito : Da Impostazioni > Sito pubblico, apri l'editor della pagina. La tua federazione ha un URL: federazione.martialcomp.com.",
                    "Personalizzare l'aspetto : Scegli colori, tema, banner e logo. Aggiungi una descrizione e i link ai tuoi social media.",
                    "Aggiungere contenuti : Pubblica notizie, gallerie fotografiche, video, calendario delle competizioni e documenti scaricabili.",
                    "Gestire le pagine : Crea pagine aggiuntive: Storia, Dirigenti, Regolamento, Contatti.",
                ],
                'tip_it': 'Il sito pubblico e ottimizzato per il SEO. Piu e completo, meglio si posizionera su Google.',
            },
            7: {
                'title_it': 'Visualizzare statistiche e rapporti',
                'steps_it': [
                    "Dashboard analitica : La dashboard mostra i KPI: numero di club, praticanti, competizioni, licenze attive, crescita.",
                    "Rapporti per club : Genera rapporti dettagliati per club: numero di membri, quote, partecipazione alle competizioni, gradi assegnati.",
                    "Rapporti per disciplina : Analizza la distribuzione per disciplina, eta, sesso. Identifica le tendenze di crescita.",
                    "Esportare e condividere : Esporta i rapporti in PDF, Excel o CSV per le tue assemblee generali e i rapporti ufficiali.",
                ],
                'tip_it': 'I rapporti si aggiornano in tempo reale. Pianifica invii automatici mensili o trimestrali.',
            },
            8: {
                'title_it': 'Gestire i programmi di formazione',
                'steps_it': [
                    "Creare un programma : Da Formazione > Nuovo, definisci il programma: titolo, disciplina, livello, durata, prerequisiti.",
                    "Pianificare le sessioni : Aggiungi le sessioni di formazione: date, luoghi, formatori, numero di posti.",
                    "Gestire le iscrizioni : Allenatori e giudici si iscrivono online. Valida le iscrizioni e invia le convocazioni.",
                    "Monitoraggio e certificazione : Monitora la partecipazione alle sessioni. Emetti le certificazioni ai partecipanti che hanno completato il programma.",
                ],
                'tip_it': 'I programmi di formazione completati appaiono automaticamente nei profili degli allenatori e dei giudici.',
            },
        },
    },

    # =========================================================================
    # Sezione 10: Finanze (5 tutorial)
    # =========================================================================
    10: {
        'title_it': 'Finanze',
        'tutorials': {
            1: {
                'title_it': 'Monitorare le transazioni del club',
                'steps_it': [
                    "Panoramica : La dashboard finanziaria mostra: saldo, entrate del mese, spese e grafico delle tendenze.",
                    "Registrare una transazione : Aggiungi un'entrata o un'uscita: importo, data, categoria (quote associative, attrezzatura, affitto), descrizione.",
                    "Categorizzazione automatica : MartialComp categorizza automaticamente le transazioni ricorrenti. Personalizza le categorie secondo le tue esigenze.",
                ],
                'tip_it': 'Collega il tuo conto bancario per importare automaticamente le transazioni e semplificare la riconciliazione.',
            },
            2: {
                'title_it': 'Creare e inviare fatture',
                'steps_it': [
                    "Creare una fattura : Da Finanze > Fatture > Nuova, seleziona il destinatario (praticante, club, sponsor) e le righe di fatturazione.",
                    "Personalizzare : Aggiungi il tuo logo, le note legali, i termini di pagamento. Scegli la valuta e l'aliquota IVA.",
                    "Inviare : Invia la fattura per email. Il destinatario riceve un link di pagamento online (Stripe) e la fattura in PDF.",
                    "Monitorare i pagamenti : Visualizza le fatture pagate, in attesa e scadute. Invia promemoria automatici.",
                ],
                'tip_it': 'Le quote associative dei praticanti generano automaticamente fatture se attivi questa opzione.',
            },
            3: {
                'title_it': 'Gestire i pagamenti online (Stripe)',
                'steps_it': [
                    "Collegare Stripe : Da Impostazioni > Pagamenti, clicca 'Collega Stripe'. Segui i passaggi per collegare il tuo account Stripe.",
                    "Configurare il checkout : Imposta le tariffe per: quote associative, iscrizioni alle competizioni, negozio. Attiva i pagamenti ricorrenti se necessario.",
                    "Testare il pagamento : Usa la modalita test di Stripe per verificare che tutto funzioni prima di attivare i pagamenti reali.",
                    "Monitorare le entrate : La dashboard Stripe in MartialComp mostra i pagamenti ricevuti, i rimborsi e i trasferimenti al tuo conto bancario.",
                ],
                'tip_it': 'Stripe addebita una commissione dell\'1,4% + 0,25 EUR per transazione in Europa. I fondi vengono trasferiti entro 2-7 giorni.',
            },
            4: {
                'title_it': 'Importare gli estratti conto bancari',
                'steps_it': [
                    "Scaricare l'estratto : Dalla tua banca, esporta l'estratto conto in formato CSV, OFX o QIF.",
                    "Importare in MartialComp : Da Finanze > Importa, carica il file. MartialComp rileva il formato e mappa le colonne.",
                    "Riconciliare : Il sistema abbina automaticamente le transazioni importate alle fatture e quote associative esistenti.",
                    "Validare : Verifica gli abbinamenti, correggi gli errori e valida. Le transazioni non abbinate vengono aggiunte come in sospeso.",
                ],
                'tip_it': 'Le importazioni bancarie mensili mantengono la tua contabilita aggiornata senza inserimento manuale.',
            },
            5: {
                'title_it': 'Gestire le quote associative dei praticanti',
                'steps_it': [
                    "Configurare le tariffe : Da Finanze > Quote associative, imposta le tariffe annuali per categoria: bambino, adolescente, adulto, famiglia.",
                    "Emettere le richieste di pagamento : All'inizio della stagione, genera le richieste di pagamento per tutti i membri. Ognuno riceve un'email con un link di pagamento.",
                    "Monitorare i pagamenti : Visualizza le quote pagate, in attesa e scadute. Lo stato appare nella scheda di ogni praticante.",
                    "Inviare promemoria : Pianifica promemoria automatici: 1 settimana, 2 settimane, 1 mese dopo la data di scadenza.",
                ],
                'tip_it': 'I praticanti con quote scadute possono essere bloccati dall\'iscrizione alle competizioni.',
            },
        },
    },

    # =========================================================================
    # Sezione 11: Eventi e Calendario (3 tutorial)
    # =========================================================================
    11: {
        'title_it': 'Eventi e Calendario',
        'tutorials': {
            1: {
                'title_it': 'Creare un evento (stage, gala, assemblea)',
                'steps_it': [
                    "Creare l'evento : Da Calendario > Nuovo evento, inserisci: tipo (stage, gala, assemblea, porte aperte), titolo, date, luogo e descrizione.",
                    "Configurare le iscrizioni : Attiva le iscrizioni online. Imposta il numero di posti, la tariffa (gratuita o a pagamento) e il termine di iscrizione.",
                    "Pubblicare : Pubblica l'evento. Appare nel calendario del club e puo essere condiviso sui social media.",
                ],
                'tip_it': 'Gli stage con maestri ospiti sono eccellenti strumenti di marketing. Aggiungi la loro foto e biografia per attirare piu persone.',
            },
            2: {
                'title_it': 'Gestire gli eventi ricorrenti',
                'steps_it': [
                    "Creare la ricorrenza : Durante la creazione, seleziona 'Evento ricorrente'. Imposta la frequenza: giornaliera, settimanale, mensile.",
                    "Gestire le eccezioni : Annulla o modifica una singola occorrenza senza influire sulle altre (es. lezione annullata per festivita).",
                    "Modificare la serie : Modifica l'intera serie (es. cambio permanente di orario) o una singola occorrenza.",
                ],
                'tip_it': 'Le lezioni settimanali dovrebbero essere create come eventi ricorrenti per apparire automaticamente nel calendario.',
            },
            3: {
                'title_it': 'Monitorare iscrizioni e presenze',
                'steps_it': [
                    "Visualizzare gli iscritti : Dall'evento, visualizza la lista degli iscritti con il loro stato: iscritto, confermato, annullato.",
                    "Registrare le presenze : Il giorno dell'evento, registra le presenze tramite lista o QR code.",
                    "Esportare : Esporta la lista dei partecipanti in CSV o PDF per i tuoi archivi.",
                ],
                'tip_it': 'Il tasso di partecipazione agli eventi e un indicatore chiave del coinvolgimento dei tuoi membri.',
            },
        },
    },

    # =========================================================================
    # Sezione 12: Gestione Famiglia (3 tutorial)
    # =========================================================================
    12: {
        'title_it': 'Gestione Famiglia',
        'tutorials': {
            1: {
                'title_it': 'Creare un gruppo famiglia',
                'steps_it': [
                    "Accedere ai gruppi famiglia : Dal tuo profilo, vai a Impostazioni > Gruppo Famiglia > Crea.",
                    "Aggiungere i membri : Aggiungi ogni membro della famiglia: coniuge, figli. Collega i loro account MartialComp esistenti o creane di nuovi.",
                    "Impostare il responsabile : Il responsabile del gruppo famiglia riceve tutte le notifiche e gestisce i pagamenti per l'intera famiglia.",
                ],
                'tip_it': 'Alcuni club offrono tariffe familiari (sconto dal 3o membro). Il gruppo famiglia attiva automaticamente questi sconti.',
            },
            2: {
                'title_it': 'Iscrivere tutta la famiglia a una competizione',
                'steps_it': [
                    "Iscrizione di gruppo : Dalla competizione, clicca 'Iscrivi la mia famiglia'. Vengono mostrati i membri idonei del tuo gruppo famiglia.",
                    "Selezionare e confermare : Seleziona i membri da iscrivere. Le categorie vengono automaticamente suggerite per ciascuno.",
                    "Pagamento unico : Paga tutte le iscrizioni in un'unica transazione.",
                ],
                'tip_it': 'L\'iscrizione di gruppo fa risparmiare tempo prezioso quando piu figli partecipano alla stessa competizione.',
            },
            3: {
                'title_it': 'Centro pagamenti famiglia',
                'steps_it': [
                    "Panoramica : Il centro famiglia mostra tutte le quote, iscrizioni e fatture della famiglia su un'unica schermata.",
                    "Pagamento raggruppato : Raggruppa piu pagamenti in sospeso e paga in un'unica transazione.",
                    "Storico : Visualizza lo storico completo dei pagamenti della famiglia con ricevute scaricabili.",
                ],
                'tip_it': 'Attiva l\'addebito diretto automatico per non dimenticare mai una quota associativa.',
            },
        },
    },

    # =========================================================================
    # Sezione 13: Gestione Attivita (Kanban) (2 tutorial)
    # =========================================================================
    13: {
        'title_it': 'Gestione Attivita (Kanban)',
        'tutorials': {
            1: {
                'title_it': 'Utilizzare la bacheca Kanban',
                'steps_it': [
                    "Creare una bacheca : Da Strumenti > Kanban, crea una nuova bacheca: nome, descrizione e membri invitati.",
                    "Aggiungere le colonne : Crea le colonne del tuo flusso di lavoro: Da fare, In corso, In sospeso, Fatto. Personalizza nomi e colori.",
                    "Creare le attivita : Aggiungi attivita con: titolo, descrizione, scadenza, assegnatario, priorita (alta/media/bassa) ed etichette.",
                    "Gestire tramite trascinamento : Sposta le attivita tra le colonne trascinandole. Lo storico dei movimenti viene conservato.",
                ],
                'tip_it': 'Crea una bacheca dedicata per ogni competizione da organizzare. Le attivita standard (prenotare la sede, ordinare le medaglie, ecc.) possono essere importate da un modello.',
            },
            2: {
                'title_it': 'Gestire le attivita organizzative',
                'steps_it': [
                    "Modello competizione : Usa il modello 'Organizzazione Competizione' che contiene attivita standard: logistica, comunicazione, giudici, medaglie, ecc.",
                    "Assegnare ai membri : Assegna ogni attivita a un membro del team organizzativo. Imposta le scadenze.",
                    "Monitorare l'avanzamento : La percentuale di avanzamento complessivo e mostrata in cima alla bacheca. Le attivita in ritardo vengono evidenziate in rosso.",
                ],
                'tip_it': 'La bacheca Kanban e accessibile dall\'app mobile per aggiornare le attivita in movimento.',
            },
        },
    },

    # =========================================================================
    # Sezione 14: Negozio Online (2 tutorial)
    # =========================================================================
    14: {
        'title_it': 'Negozio Online',
        'tutorials': {
            1: {
                'title_it': 'Configurare il negozio del club',
                'steps_it': [
                    "Attivare il negozio : Da Impostazioni > Negozio, attiva la funzionalita e-commerce. Collega il tuo account Stripe se non l'hai gia fatto.",
                    "Aggiungere i prodotti : Crea i tuoi prodotti: nome, descrizione, foto, prezzo, taglie/varianti disponibili, giacenza.",
                    "Organizzare per categorie : Classifica i tuoi prodotti: Uniformi (kimono, dobok, guanti), Attrezzatura (protezioni, borse), Accessori (cinture, stemmi), Merchandising.",
                    "Pubblicare il negozio : Il tuo negozio e accessibile dalla pagina pubblica del tuo club. Condividi il link o il QR code.",
                ],
                'tip_it': 'Offri pacchetti (kimono + cintura + borsa) con uno sconto per aumentare il carrello medio.',
            },
            2: {
                'title_it': 'Effettuare un ordine',
                'steps_it': [
                    "Sfogliare il negozio : Dalla pagina del tuo club, accedi al negozio. Sfoglia i prodotti per categoria.",
                    "Aggiungere al carrello : Seleziona la taglia/variante e aggiungi al carrello. Il carrello persiste tra le sessioni.",
                    "Ordinare e pagare : Conferma il carrello, scegli il metodo di consegna (ritiro al dojo o spedizione postale) e paga online.",
                    "Monitorare l'ordine : Ricevi notifiche ad ogni passaggio: ordine confermato, in preparazione, pronto per il ritiro / spedito.",
                ],
                'tip_it': 'La modalita \'Ritiro al Dojo\' evita le spese di spedizione. L\'allenatore ti consegnera l\'ordine alla prossima lezione.',
            },
        },
    },

    # =========================================================================
    # Sezione 15: Funzionalita Avanzate (5 tutorial)
    # =========================================================================
    15: {
        'title_it': 'Funzionalita Avanzate',
        'tutorials': {
            1: {
                'title_it': 'Configurare lo streaming delle competizioni',
                'steps_it': [
                    "Preparare lo streaming : Crea un evento live su YouTube, Twitch o Facebook. Copia l'URL dello streaming e la chiave di streaming.",
                    "Configurare in MartialComp : Dalla competizione, vai a Impostazioni > Streaming. Incolla l'URL e attiva la visualizzazione sulla pagina pubblica.",
                    "Overlay del punteggio : Attiva l'overlay MartialComp che mostra il punteggio in diretta sullo streaming video. Personalizza la posizione e lo stile.",
                    "Avviare e testare : Avvia lo streaming e verifica che l'overlay funzioni. Gli spettatori vedranno il punteggio in diretta sullo streaming.",
                ],
                'tip_it': 'Lo streaming con overlay del punteggio MartialComp da un aspetto professionale anche alle piccole competizioni.',
            },
            2: {
                'title_it': 'Utilizzare l\'applicazione mobile',
                'steps_it': [
                    "Scaricare l'app : Cerca 'MartialComp' sul Play Store (Android) o App Store (iOS). Installa e apri.",
                    "Accedere : Accedi con il tuo account MartialComp esistente. Puoi anche usare l'accesso tramite Google, Facebook o Apple.",
                    "Scoprire l'interfaccia mobile : L'app offre: profilo, risultati, calendario, notifiche push, QR code personale e iscrizione alle competizioni.",
                    "Modalita offline : I dati essenziali (profilo, grado, licenza) sono disponibili offline. Sincronizzazione automatica quando torni online.",
                ],
                'tip_it': 'Attiva le notifiche push per essere avvisato dei risultati in diretta durante le competizioni.',
            },
            3: {
                'title_it': 'Cambiare ruolo nell\'applicazione',
                'steps_it': [
                    "Accedere al selettore di ruolo : Tocca il tuo avatar in cima allo schermo o scorri da sinistra per aprire il menu laterale.",
                    "Selezionare un ruolo : Appare la tua lista di ruoli: Allenatore, Praticante, Giudice, Responsabile Club. Tocca il ruolo desiderato.",
                    "Interfaccia adattata : La dashboard e il menu si aggiornano immediatamente per riflettere il ruolo selezionato.",
                ],
                'tip_it': 'Puoi essere allenatore in un club e praticante in un altro. Ogni ruolo e collegato alla sua organizzazione.',
            },
            4: {
                'title_it': 'Import/Export avanzato dei dati',
                'steps_it': [
                    "Formati supportati : MartialComp supporta l'importazione e l'esportazione in CSV, Excel (XLSX), JSON e PDF. Ogni modulo ha le proprie opzioni.",
                    "Importazione con mappatura : L'interfaccia di mappatura permette di associare qualsiasi struttura di file ai campi di MartialComp.",
                    "Esportazione personalizzata : Seleziona i campi da esportare, i filtri e il formato. Pianifica esportazioni automatiche ricorrenti.",
                    "Operazioni massive : Le operazioni massive permettono la modifica di massa di: grado, gruppo, stato di iscrizione, ecc.",
                ],
                'tip_it': 'L\'esportazione JSON e ideale per le integrazioni con sistemi di terze parti (sito web, applicazione esterna, CRM).',
            },
            5: {
                'title_it': 'Gestire giudici ad hoc (volontari)',
                'steps_it': [
                    "Creare un giudice temporaneo : Il giorno della competizione, da Giudici > Aggiungi volontario, crea un profilo temporaneo: nome, club e specialita.",
                    "Assegnare un PIN : Un PIN unico viene generato automaticamente. Il volontario usa questo PIN per accedere all'interfaccia di punteggio.",
                    "Assegnare alle categorie : Assegna il giudice volontario alle categorie come un giudice regolare. Puo iniziare a valutare immediatamente.",
                    "Dopo la competizione : Il profilo temporaneo viene archiviato dopo la competizione. I punteggi vengono conservati nello storico.",
                ],
                'tip_it': 'I giudici ad hoc sono essenziali per le piccole competizioni dove il numero di giudici ufficiali e limitato.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to Italian (hardcoded translations)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be updated without saving to database'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes will be saved'))

        sections_updated = 0
        tutorials_updated = 0
        sections_missing = 0
        tutorials_missing = 0

        for section in TutorialSection.objects.all().order_by('order'):
            sec_data = TRANSLATIONS.get(section.order)
            if not sec_data:
                self.stdout.write(self.style.WARNING(
                    f'  No translation for section {section.order}: {section.title}'
                ))
                sections_missing += 1
                continue

            section.title_it = sec_data['title_it']
            if not dry_run:
                section.save(update_fields=['title_it'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_it"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_it = tut_data['title_it']
                tutorial.steps_it = json.dumps(tut_data['steps_it'], ensure_ascii=False)
                tutorial.tip_it = tut_data.get('tip_it', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_it', 'steps_it', 'tip_it'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_it"]}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Translation complete: {sections_updated} sections, {tutorials_updated} tutorials updated'
        ))
        if sections_missing or tutorials_missing:
            self.stdout.write(self.style.WARNING(
                f'Missing translations: {sections_missing} sections, {tutorials_missing} tutorials'
            ))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes were saved'))
