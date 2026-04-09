"""
Management command to translate all 81 tutorials from French to German.
Updates title_de, steps_de, and tip_de fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_de
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Abschnitt 1: Onboarding und Erste Schritte (7 Tutorials)
    # =========================================================================
    1: {
        'title_de': 'Onboarding und Erste Schritte',
        'tutorials': {
            1: {
                'title_de': 'Konto erstellen und Rolle waehlen',
                'steps_de': [
                    "Auf MartialComp zugreifen : Gehe zu martialcomp.com und klicke auf 'Kostenlos registrieren'. Du kannst auch die mobile App aus dem Play Store oder App Store herunterladen.",
                    "Registrierungsformular ausfuellen : Gib deinen Nachnamen, Vornamen, deine E-Mail-Adresse und ein Passwort ein. Du kannst dich auch mit Google, Facebook oder Apple ID fuer einen vereinfachten Zugang registrieren.",
                    "Hauptrolle waehlen : Waehle deine Rolle: Vereinsleiter, Trainer, Kampfrichter/Schiedsrichter, Sportler oder Verbandsverantwortlicher. Diese Wahl bestimmt dein Dashboard und die Funktionen, du kannst aber spaeter weitere Rollen hinzufuegen.",
                    "E-Mail bestaetigen : Pruefe deinen Posteingang und klicke auf den Bestaetigungslink. Dein Konto ist aktiv und du kannst auf dein personalisiertes Dashboard zugreifen.",
                ],
                'tip_de': 'Du kannst mehrere Rollen haben (z.B. Trainer UND Sportler). Wechsle jederzeit zwischen deinen Rollen ueber das Seitenmenue.',
            },
            2: {
                'title_de': 'Deinen Verein erstellen',
                'steps_de': [
                    "Erstellungsassistenten starten : Klicke auf deinem Dashboard auf 'Verein erstellen'. Der 4-Schritte-Einrichtungsassistent startet automatisch.",
                    "Allgemeine Informationen : Gib den Vereinsnamen, das Kuerzel, die vollstaendige Adresse und die Kontaktdaten (Telefon, E-Mail, Website) ein. Fuege dein Logo im PNG- oder JPG-Format hinzu (empfohlene Groesse: 500x500px).",
                    "Disziplinen waehlen : Waehle eine oder mehrere Disziplinen aus den 14+ verfuegbaren: Karate, Judo, BJJ, Taekwondo, MMA, Kung Fu, Aikido, Kendo, Muay Thai, Boxen, Capoeira usw.",
                    "Subdomain personalisieren : Waehle deine einzigartige Adresse: dein-verein.martialcomp.com. Dies wird die oeffentliche Adresse deines Vereins sein, fuer alle zugaenglich.",
                    "Optionen konfigurieren : Lege die Oeffnungszeiten fest, fuege eine Beschreibung und Fotos deines Dojos hinzu. Aktiviere oder deaktiviere die Online-Registrierung von Sportlern.",
                ],
                'tip_de': 'Dein Verein wird mit dem kostenlosen Plan erstellt (bis zu 10 Mitglieder). Alle Funktionen sind von Anfang an verfuegbar. Upgrade auf Premium, wenn du 10 Mitglieder ueberschreitest.',
            },
            3: {
                'title_de': 'Deinen Verband erstellen',
                'steps_de': [
                    "Erstellung beantragen : Waehle die Rolle 'Verbandsverantwortlicher' bei der Registrierung oder fuege sie in den Einstellungen hinzu. Fuelle das Erstellungsformular mit den offiziellen Informationen deines Verbandes aus.",
                    "Offizielle Informationen : Gib den vollstaendigen Namen, das Kuerzel, das Land, die abgedeckten Disziplinen, die offizielle Registrierungsnummer und die Kontaktdaten ein.",
                    "Oeffentliche Seite konfigurieren : Personalisiere deine oeffentliche Seite: Banner, Logo, Farben, Beschreibung, Fotogalerie und Links zu deinen sozialen Netzwerken.",
                    "Struktur definieren : Konfiguriere deine regionalen Ligen falls zutreffend, definiere die Mitgliedschaftskategorien fuer Vereine und die Beitragstarife.",
                ],
                'tip_de': 'Verbaende verfuegen ueber einen erweiterten Verwaltungsbereich zur Ueberwachung aller angeschlossenen Vereine, Wettkaempfe und Grade.',
            },
            4: {
                'title_de': 'Dein Trainerprofil einrichten',
                'steps_de': [
                    "Trainerprofil aufrufen : Klicke im Seitenmenue auf 'Mein Trainerprofil'. Falls du die Trainerrolle noch nicht hast, fuege sie unter Einstellungen > Meine Rollen hinzu.",
                    "Qualifikationen eingeben : Fuege deine Diplome (BPJEPS, DEJEPS, CQP usw.), deine Grade in jeder Disziplin und deine Erfahrungsjahre hinzu.",
                    "Disziplinen festlegen : Waehle die Disziplinen, die du unterrichtest, und dein Spezialisierungsniveau in jeder (Anfaenger, Fortgeschrittene, Wettkampf).",
                    "Verfuegbarkeit festlegen : Gib deine woechentlichen Unterrichtszeiten an. Diese Information ist fuer Vereine sichtbar, die Trainer suchen.",
                ],
                'tip_de': 'Ein vollstaendiges Trainerprofil mit Foto und Zertifizierungen erhoeht deine Sichtbarkeit bei Vereinen erheblich.',
            },
            5: {
                'title_de': 'Dein Kampfrichterprofil einrichten',
                'steps_de': [
                    "Kampfrichterrolle aktivieren : Aktiviere unter Einstellungen > Meine Rollen die Rolle 'Kampfrichter / Schiedsrichter'. Gib deine Kampfrichter-Lizenznummer ein, falls vorhanden.",
                    "Qualifikationen hinzufuegen : Gib dein Kampfrichterniveau an (regional, national, international), die Disziplinen, fuer die du qualifiziert bist, und deine Zertifizierungen.",
                    "Spezialisierungen festlegen : Kata/Techniken, Kampf, kuenstlerische Bewertung... Jede Spezialisierung berechtigt dich fuer die entsprechenden Wettkaempfe.",
                    "Verfuegbarkeit eingeben : Gib deine geografischen Gebiete und Verfuegbarkeitszeitraeume fuer Wettkaempfe an.",
                ],
                'tip_de': 'Wettkampforganisatoren koennen dich anhand deiner Qualifikationen und Verfuegbarkeit suchen und direkt einladen.',
            },
            6: {
                'title_de': 'Dein Sportlerprofil einrichten',
                'steps_de': [
                    "Persoenliche Informationen vervollstaendigen : Gib dein Geburtsdatum, Geschlecht, Gewicht (fuer Wettkampfkategorien), Groesse und Profilfoto ein.",
                    "Aktuellen Grad hinzufuegen : Gib deine Hauptdisziplin, deinen aktuellen Grad (Guertel), das Datum der Verleihung und die ausstellende Organisation an.",
                    "Lizenz eingeben : Fuege deine Verbandslizenz-Nummer, das Ablaufdatum und das aktuelle aerztliche Attest hinzu.",
                    "Notfallkontakte : Fuege mindestens einen Notfallkontakt hinzu (Pflicht fuer Wettkaempfe): Name, Telefon, Verwandtschaftsverhaeltnis.",
                ],
                'tip_de': 'Ein vollstaendiges Profil ist erforderlich, um sich fuer Wettkaempfe anzumelden. Gewicht und Grad bestimmen automatisch deine Kategorie.',
            },
            7: {
                'title_de': 'Dashboard und Navigation verstehen',
                'steps_de': [
                    "Das Dashboard : Dein Dashboard zeigt eine personalisierte Uebersicht: naechste Veranstaltungen, aktuelle Nachrichten, Schnellstatistiken und Direktzugriffe auf deine haeufigen Aktionen.",
                    "Die Seitenleiste : Das Seitenmenue bietet Zugang zu allen Bereichen: Mitglieder, Wettkaempfe, Grade, Finanzen, Kalender, Einstellungen. Es passt sich deiner aktiven Rolle an.",
                    "Rolle wechseln : Wenn du mehrere Rollen hast (z.B. Trainer + Sportler), klicke auf deinen Avatar oben rechts zum Wechseln. Dashboard und Menue passen sich automatisch an.",
                    "Benachrichtigungen und Nachrichten : Das Glockensymbol oben rechts zeigt deine Benachrichtigungen: Anmeldungen, Ergebnisse, Nachrichten. Konfiguriere deine Benachrichtigungseinstellungen in den Einstellungen.",
                    "Globale Suche : Nutze die Suchleiste, um schnell einen Sportler, Verein, Wettkampf oder eine Veranstaltung zu finden.",
                ],
                'tip_de': 'Personalisiere dein Dashboard, indem du deine Lieblings-Widgets anheftest. Die Tastenkombination Strg+K oeffnet die Schnellsuche.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 2: Vereinsverwaltung (10 Tutorials)
    # =========================================================================
    2: {
        'title_de': 'Vereinsverwaltung',
        'tutorials': {
            1: {
                'title_de': 'Sportler manuell hinzufuegen',
                'steps_de': [
                    "Aufnahmeformular oeffnen : Gehe zu Mitglieder > Sportler hinzufuegen und fuelle das Formular aus: Nachname, Vorname, Geburtsdatum, Geschlecht, E-Mail und Telefon.",
                    "Zusaetzliche Informationen : Fuege den aktuellen Grad, die Lizenznummer, das Passfoto (optional) und das aerztliche Attest hinzu.",
                    "Einer Gruppe zuweisen : Weise den Sportler einer oder mehreren Trainingsgruppen zu (z.B. Karate Erwachsene Fortgeschritten, Judo Kinder Anfaenger).",
                    "Einladung senden : Markiere 'Einladungs-E-Mail senden', damit der Sportler sein eigenes Konto erstellen und auf sein Online-Profil zugreifen kann.",
                ],
                'tip_de': 'Der Sportler erhaelt eine E-Mail mit einem Link, um seine Registrierung abzuschliessen und die mobile App herunterzuladen.',
            },
            2: {
                'title_de': 'Massenimport von Sportlern (CSV/Excel)',
                'steps_de': [
                    "Vorlage herunterladen : Lade unter Mitglieder > Importieren die CSV- oder Excel-Vorlage herunter. Die Datei enthaelt Pflichtspalten: Nachname, Vorname, Geburtsdatum, E-Mail und optionale Spalten: Grad, Lizenz, Telefon.",
                    "Datei ausfuellen : Fuege die Daten deiner Sportler ein. Beachte die Formate: Daten als TT/MM/JJJJ, Grade als Text (z.B. 'Gruener Guertel', '2. Dan').",
                    "Hochladen und Spalten zuordnen : Importiere die Datei. Die Zuordnungsoberflaeche ermoeglicht es, jede Spalte deiner Datei den MartialComp-Feldern zuzuordnen. Ueberpr uefe die Zuordnung.",
                    "Validieren und korrigieren : MartialComp erkennt Fehler (Duplikate, ungueltige Formate). Korrigiere die fehlerhaften Zeilen oder ueberspringe sie. Bestaetige den Import.",
                ],
                'tip_de': 'Du kannst bis zu 500 Sportler in einem einzigen Vorgang importieren. Der Import erkennt automatisch Duplikate anhand von E-Mail oder Nachname + Vorname + Geburtsdatum.',
            },
            3: {
                'title_de': 'Sportlerprofile verwalten',
                'steps_de': [
                    "Profil aufrufen : Klicke in der Mitgliederliste auf den Namen eines Sportlers, um sein vollstaendiges Profil zu oeffnen.",
                    "Details anzeigen : Das Profil zeigt: persoenliche Informationen, Gradhistorie, absolvierte Wettkaempfe, Anwesenheit und Beitraege.",
                    "Informationen bearbeiten : Klicke auf 'Bearbeiten', um die Daten zu aktualisieren. Aenderungen werden in der Historie protokolliert.",
                    "Schnellaktionen : Vom Profil aus kannst du: fuer einen Wettkampf anmelden, einen Grad zuweisen, eine Nachricht senden, ein Zertifikat erstellen.",
                ],
                'tip_de': 'Nutze die erweiterten Filter (Grad, Alter, gueltige Lizenz, bezahlter Beitrag), um schnell einen Sportler zu finden.',
            },
            4: {
                'title_de': 'Benutzerkonto fuer einen Sportler erstellen',
                'steps_de': [
                    "Sportlerprofil aufrufen : Oeffne das Profil des entsprechenden Sportlers aus der Mitgliederliste.",
                    "Mit einem Konto verknuepfen : Klicke auf 'Benutzerkonto erstellen'. Eine Einladungs-E-Mail mit einem Link zur Passworterstellung wird an den Sportler gesendet.",
                    "Berechtigungen festlegen : Waehle, was der Sportler tun kann: seine Ergebnisse einsehen, sich fuer Wettkaempfe anmelden, den Kalender einsehen, online bezahlen.",
                ],
                'tip_de': 'Minderjaehrige Sportler koennen ein Konto haben, das ueber die Familiengruppen-Funktion mit dem eines Elternteils verknuepft ist.',
            },
            5: {
                'title_de': 'Rollen und Berechtigungen des Vereins verwalten',
                'steps_de': [
                    "Rollenverwaltung aufrufen : Unter Einstellungen > Rollen und Berechtigungen siehst du die verfuegbaren Rollen: Administrator, Sekretaer, Schatzmeister, Trainer, Mitglied.",
                    "Rolle zuweisen : Waehle ein Mitglied aus und weise ihm eine Rolle zu. Jede Rolle gewaehrt Zugang zu bestimmten Funktionen.",
                    "Berechtigungen anpassen : Definiere fuer jede Rolle die Rechte: nur Lesen, Bearbeiten, Loeschen, Zugang zu Finanzen, Verwaltung von Anmeldungen.",
                    "Zugriffe pruefen : Pruefe das Aktivitaetsprotokoll, um zu sehen, wer was und wann in der Vereinsverwaltung getan hat.",
                ],
                'tip_de': 'Die Administratorrolle hat alle Rechte. Erstelle eine Sekretaerrolle mit Zugang zu Mitgliedern und Kalender, aber ohne Finanzzugang.',
            },
            6: {
                'title_de': 'Anwesenheitsverfolgung / Check-in',
                'steps_de': [
                    "Sitzung erstellen : Gehe zu Anwesenheit > Neue Sitzung, waehle die Trainingsgruppe, das Datum und die Uhrzeit der Unterrichtsstunde.",
                    "Per Liste erfassen : Zeige die Mitgliederliste der Gruppe an und markiere die Anwesenden. Die Erfassung erfolgt per Fingertipp auf dem Mobilgeraet.",
                    "Per QR-Code erfassen : Zeige den QR-Code der Sitzung an. Die Sportler scannen ihn mit ihrem Handy bei Ankunft im Dojo.",
                    "Statistiken anzeigen : Sieh die Anwesenheitsquoten pro Sportler, Gruppe und Zeitraum ein. Identifiziere wiederholte Abwesenheiten.",
                ],
                'tip_de': 'Der QR-Code-Check-in ist die schnellste Methode fuer grosse Gruppen. Der Code wird bei jeder Sitzung erneuert, um Missbrauch zu verhindern.',
            },
            7: {
                'title_de': 'Trainingsprogramme verwalten',
                'steps_de': [
                    "Programm erstellen : Gehe zu Programme > Neu, definiere den Namen, die Disziplin, das Niveau (Anfaenger, Mittelstufe, Fortgeschritten) und die Zyklusdauer.",
                    "Sitzungen planen : Fuege die woechentlichen Zeitfenster hinzu: Tag, Startzeit, Endzeit, Raum/Tatami, verantwortlicher Trainer.",
                    "Inhalte definieren : Fuege fuer jede Sitzung einen Plan hinzu: Aufwaermen, Techniktraining, Sparring/Randori, Cool-Down. Haenge Dateien oder Videos an.",
                    "Veroeffentlichen und benachrichtigen : Veroeffentliche das Programm. Die Sportler der Gruppe erhalten eine Benachrichtigung mit dem vollstaendigen Programm.",
                ],
                'tip_de': 'Dupliziere ein bestehendes Programm, um schnell einen neuen Zyklus mit Variationen zu erstellen.',
            },
            8: {
                'title_de': 'QR-Codes des Vereins erstellen und nutzen',
                'steps_de': [
                    "Vereins-QR-Code generieren : Gehe zu Einstellungen > QR-Codes und generiere den QR-Code deines Vereins. Er ermoeglicht Besuchern den direkten Zugang zu deiner oeffentlichen Seite.",
                    "Spezielle QR-Codes : Generiere QR-Codes fuer: Online-Registrierung, Sitzungs-Check-in, Veranstaltungsseite oder Link zur mobilen App.",
                    "Drucken und ausstellen : Lade die QR-Codes in hoher Aufloesung zum Drucken herunter. Verfuegbare Formate: PNG, SVG, PDF (A4 oder Visitenkarte).",
                    "Statistiken verfolgen : Sieh die Anzahl der Scans pro QR-Code, pro Tag und nach Typ ein. Identifiziere die effektivsten QR-Codes.",
                ],
                'tip_de': 'Haenge den Registrierungs-QR-Code am Eingang deines Dojos auf. Jeder Scan ist ein potenzieller Kunde!',
            },
            9: {
                'title_de': 'Verbandsmitgliedschaft beantragen',
                'steps_de': [
                    "Deinen Verband finden : Gehe zu Verein > Mitgliedschaft und suche deinen Verband nach Name, Disziplin oder Land.",
                    "Antrag einreichen : Fuelle das Mitgliedschaftsformular aus: Vereinsinformationen, Registrierungsnummer, Nachweisdokumente (Satzung, Versicherung usw.).",
                    "Status verfolgen : Dein Antrag durchlaeuft die Phasen: Eingereicht > In Pruefung > Genehmigt/Abgelehnt. Du erhaeltst bei jedem Schritt Benachrichtigungen.",
                    "Jaehrlich erneuern : Die Mitgliedschaft gilt pro Saison. Eine automatische Erinnerung wird 30 Tage vor Ablauf gesendet.",
                ],
                'tip_de': 'Die Mitgliedschaft gibt dir Zugang zu den offiziellen Wettkaempfen des Verbandes und zur zentralen Lizenzverwaltung.',
            },
            10: {
                'title_de': 'Vereinswechsel von Sportlern verwalten',
                'steps_de': [
                    "Vereinswechsel einleiten : Klicke im Profil eines Sportlers auf 'Vereinswechsel beantragen'. Waehle den Zielverein und den Grund des Wechsels aus.",
                    "Validierungsprozess : Der Zielverein erhaelt den Antrag und kann ihn annehmen oder ablehnen. Wenn ein Verband beteiligt ist, muss dieser ebenfalls validieren.",
                    "Effektiver Wechsel : Nach der Validierung wird der Sportler automatisch mit seinem Grad und seiner Wettkampfhistorie uebertragen.",
                    "Historie einsehen : Die Wechselhistorie ist im Sportlerprofil und in den Vereinsberichten sichtbar.",
                ],
                'tip_de': 'Einige Verbaende schreiben Wechselperioden (Transferfenster) vor. MartialComp respektiert diese Regeln automatisch.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 3: Wettkaempfe - Erstellung und Konfiguration (6 Tutorials)
    # =========================================================================
    3: {
        'title_de': 'Wettkaempfe - Erstellung und Konfiguration',
        'tutorials': {
            1: {
                'title_de': 'Einen Einzelwettkampf erstellen',
                'steps_de': [
                    "Erstellung starten : Gehe zu Wettkaempfe > Erstellen und waehle den Typ 'Einzel'. Gib den Namen, die Disziplin(en), die Daten und den Ort ein.",
                    "Format festlegen : Waehle das Format: Kampf (Kumite, Randori, Sparring), Technik (Kata, Poomsae, Formen) oder Gemischt (beides).",
                    "Kategorien konfigurieren : Definiere die Kategorien nach Geschlecht, Altersgruppe, Gewicht und/oder Grad. MartialComp bietet Standard-Kategorie-Vorlagen nach Disziplin.",
                    "Optionen und Veroeffentlichung : Aktiviere die gewuenschten Optionen: Online-Anmeldung, Bezahlung, Live-Streaming, oeffentliche Ergebnisse. Veroeffentliche den Wettkampf.",
                ],
                'tip_de': 'Nutze die Kategorie-Vorlagen (WKF, IJF, ITF...) um Zeit zu sparen. Du kannst sie nach der Erstellung anpassen.',
            },
            2: {
                'title_de': 'Einen Teamwettkampf erstellen (Synchron/Song Luyen)',
                'steps_de': [
                    "Teammodus waehlen : Waehle bei der Erstellung den Typ 'Team'. Definiere die minimale und maximale Anzahl von Teammitgliedern.",
                    "Teamformat konfigurieren : Waehle das Format: Synchronisation (Team-Kata/Poomsae), Song Luyen (vorgegebener Kampf fuer zwei) oder Teamkampf (Staffel).",
                    "Zusammensetzung definieren : Lege die Rollen im Team fest: Anzahl Stammspieler, Anzahl Ersatzspieler, ob gemischte Zusammensetzungen erlaubt sind oder nicht.",
                    "Team-Bewertungskriterien : Fuer die technische Bewertung lege fest, ob die Kampfrichter das Team als Ganzes oder jedes Mitglied einzeln bewerten.",
                ],
                'tip_de': 'Der Synchron-Modus ermoeglicht die Bewertung mit spezifischen Synchronisationskriterien (Timing, Ausrichtung, gemeinsamer Ausdruck).',
            },
            3: {
                'title_de': 'Wettkampfkategorien konfigurieren',
                'steps_de': [
                    "Kategorienverwaltung aufrufen : Gehe im erstellten Wettkampf zur Registerkarte Kategorien. Klicke auf 'Kategorie hinzufuegen'.",
                    "Kriterien definieren : Definiere fuer jede Kategorie: Geschlecht (M/W/Gemischt), Altersgruppe (z.B. 12-14 Jahre), Gewichtsklasse (z.B. -60kg), Mindest-/Hoechstgrad.",
                    "Kategorie benennen : Gib einen klaren Namen: 'Kadetten Maennlich -52kg' oder 'Kata Erwachsene Weiblich Fortgeschritten'. MartialComp generiert auf Wunsch automatische Namen.",
                    "Kategorien sortieren : Ordne die Kategorien per Drag-and-Drop neu an, um die Reihenfolge am Wettkampftag festzulegen.",
                ],
                'tip_de': 'Importiere die Kategorien eines vorherigen Wettkampfs, um Zeit zu sparen. Nutze die Option \'Intelligente Duplizierung\' zum Erstellen von Varianten.',
            },
            4: {
                'title_de': 'Einen bestehenden Wettkampf duplizieren',
                'steps_de': [
                    "Quellwettkampf finden : Gehe zu Wettkaempfe > Verlauf und finde den Wettkampf, den du duplizieren moechtest.",
                    "Duplizierung starten : Klicke auf die 3 Punkte > Duplizieren. Waehle aus, was kopiert werden soll: Kategorien, Regelwerk, Konfiguration, Tarife.",
                    "Konfiguration anpassen : Aendere die Daten, den Ort und die notwendigen Parameter. Kategorien und Regelwerk werden identisch uebernommen.",
                ],
                'tip_de': 'Ideal fuer jaehrlich wiederkehrende Wettkaempfe. Dupliziere die vorherige Ausgabe und aktualisiere einfach die Daten.',
            },
            5: {
                'title_de': 'Sichtbarkeitsoptionen konfigurieren',
                'steps_de': [
                    "Sichtbarkeitseinstellungen aufrufen : Gehe im Wettkampf zu Konfiguration > Sichtbarkeit und Teilen.",
                    "Online-Anmeldungen : Aktiviere/deaktiviere die oeffentlichen Anmeldungen. Lege das Oeffnungs- und Schlussdatum der Anmeldungen fest.",
                    "Ergebnisse und Ranglisten : Waehle, ob die Ergebnisse in Echtzeit oeffentlich, nach Validierung veroeffentlicht oder privat (nur Organisator) sind.",
                    "Live-Streaming : Aktiviere den Streaming-Modus und fuege den YouTube/Twitch/Facebook-Live-Link hinzu, um ihn auf der oeffentlichen Seite anzuzeigen.",
                ],
                'tip_de': 'Live-Ergebnisse ziehen Zuschauer auf deine Seite und erhoehen die Sichtbarkeit deines Vereins oder Verbandes.',
            },
            6: {
                'title_de': 'Kampfregeln konfigurieren',
                'steps_de': [
                    "Regelwerk waehlen : Waehle ein vorkonfiguriertes Regelwerk (WKF, IJF, ITF, IBJJF usw.) oder erstelle ein eigenes.",
                    "Punktevergabe definieren : Konfiguriere die Aktionen und ihre Punkte: Yuko (1 Pkt.), Waza-ari (2 Pkt.), Ippon (3 Pkt.) usw. Fuege Strafen hinzu (Shido, Hansoku usw.).",
                    "Runden konfigurieren : Definiere die Rundendauer, die Anzahl der Runden, die Pausen und die Siegbedingungen (Punkte, Ippon, Aufgabe).",
                    "Sonderregeln : Konfiguriere spezifische Regeln: Golden Score (Verlaengerung), Hantei (Kampfrichterentscheid), vorzeitiges Ende bei Punktevorsprung.",
                ],
                'tip_de': 'Speichere deine individuellen Regelwerke als Vorlagen, um sie bei zukuenftigen Wettkaempfen wiederzuverwenden.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 4: Anmeldungen und Teams (7 Tutorials)
    # =========================================================================
    4: {
        'title_de': 'Anmeldungen und Teams',
        'tutorials': {
            1: {
                'title_de': 'Sportler fuer einen Wettkampf anmelden',
                'steps_de': [
                    "Wettkampf finden : Gehe zu Wettkaempfe > Fuer Anmeldungen offen, finde den gewuenschten Wettkampf und klicke auf 'Anmelden'.",
                    "Sportler auswaehlen : Die Liste deiner Mitglieder wird angezeigt. Waehle einen oder mehrere Sportler aus. MartialComp zeigt automatisch die berechtigten Kategorien fuer jeden an.",
                    "Kategorien bestaetigen : Bestaetige oder aendere fuer jeden Sportler die vorgeschlagene Kategorie. Das System prueft, ob Gewicht, Alter und Grad uebereinstimmen.",
                    "Bestaetigen und bezahlen : Bestaetige die Anmeldungen. Wenn der Wettkampf eine Gebuehr erhebt, fahre mit der Bezahlung aller Anmeldungen fort.",
                ],
                'tip_de': 'Sportler mit unvollstaendigem Profil (fehlendes Gewicht, abgelaufene Lizenz) werden mit einer roten Warnung markiert.',
            },
            2: {
                'title_de': 'Massenanmeldung per Formular',
                'steps_de': [
                    "Massenmodus aufrufen : Klicke auf dem Anmeldungsbildschirm auf 'Massenanmeldung'. Waehle die Zielkategorie aus.",
                    "Gruppe auswaehlen : Filtere nach Trainingsgruppe, Grad oder Alter. Waehle die berechtigten Sportler mit einem einzigen Klick aus.",
                    "Pruefen und anpassen : Der Pruefbildschirm zeigt jeden Sportler mit seiner Kategorie. Korrigiere eventuelle Fehler.",
                    "Gruppe bestaetigen : Validiere alle Anmeldungen in einem einzigen Vorgang. Eine Zusammenfassung wird per E-Mail gesendet.",
                ],
                'tip_de': 'Die Massenanmeldung ist ideal fuer Vereine, die 10+ Sportler fuer denselben Wettkampf anmelden.',
            },
            3: {
                'title_de': 'Teams erstellen und verwalten',
                'steps_de': [
                    "Team erstellen : Klicke im Wettkampf auf 'Team anmelden'. Gib dem Team einen Namen und waehle die Kategorie aus.",
                    "Mitglieder hinzufuegen : Fuege Teammitglieder aus deiner Sportlerliste hinzu. Beachte die definierten Mindest- und Hoechstzahlen.",
                    "Stamm- und Ersatzspieler festlegen : Bestimme Stamm- und Ersatzspieler per Drag-and-Drop. Die Aufstellungsreihenfolge kann hier festgelegt werden.",
                    "Team validieren : Pruefe die Konformitaet des Teams (Mitgliederzahl, Einzelkategorien) und bestaetige die Anmeldung.",
                ],
                'tip_de': 'Bei Teamwettkaempfen erscheint der Teamname auf den Anzeigetafeln und in den offiziellen Ergebnissen.',
            },
            4: {
                'title_de': 'Teamkategorie aendern',
                'steps_de': [
                    "Team aufrufen : Finde in deinen Anmeldungen das zu aendernde Team und klicke auf 'Bearbeiten'.",
                    "Kategorie aendern : Waehle die neue Kategorie aus dem Dropdown-Menue. Das System prueft, ob das Team die Kriterien erfuellt.",
                    "Aenderung bestaetigen : Validiere. Wenn der Wettkampf unterschiedliche Anmeldegebuehren pro Kategorie hat, erfolgt die Anpassung automatisch.",
                ],
                'tip_de': 'Die Kategorienaenderung ist nur moeglich, solange die Anmeldungen offen sind.',
            },
            5: {
                'title_de': 'Eine Startgemeinschaft beantragen (vereinsuebergreifende Fusion)',
                'steps_de': [
                    "Bedarf identifizieren : Dein Verein hat nicht genuegend Mitglieder fuer ein vollstaendiges Team? Die Startgemeinschaft ermoeglicht die Fusion von Teams verschiedener Vereine.",
                    "Startgemeinschaftsantrag erstellen : Klicke beim unvollstaendigen Team auf 'Startgemeinschaft vorschlagen'. Waehle den Partnerverein und die zu besetzenden Plaetze aus.",
                    "Vorschlag senden : Der Partnerverein erhaelt den Antrag mit den Details: Wettkampf, Kategorie, verfuegbare Plaetze, Bedingungen.",
                    "Startgemeinschaft abschliessen : Nach Annahme erscheint das fusionierte Team mit den Mitgliedern beider Vereine. Das Team traegt einen kombinierten Namen beider Vereine.",
                ],
                'tip_de': 'Die Startgemeinschaft bedarf der Genehmigung des Wettkampforganisators und gegebenenfalls des Verbandes.',
            },
            6: {
                'title_de': 'Startgemeinschaftsantrag annehmen/ablehnen',
                'steps_de': [
                    "Benachrichtigung erhalten : Du erhaeltst eine Benachrichtigung ueber einen Startgemeinschaftsantrag. Klicke, um die Details anzuzeigen.",
                    "Vorschlag pruefen : Pruefe: den antragstellenden Verein, den Wettkampf, die Kategorie, die zu besetzenden Plaetze und die vorgeschlagenen Bedingungen.",
                    "Annehmen oder ablehnen : Klicke auf 'Annehmen', um die Startgemeinschaft zu validieren und deine Mitglieder auszuwaehlen, oder 'Ablehnen' mit einer erlaeuternden Nachricht.",
                ],
                'tip_de': 'Du kannst einen Gegenvorschlag machen, indem du die Bedingungen vor der Annahme aenderst.',
            },
            7: {
                'title_de': 'Eingegangene Anmeldungen verwalten (Genehmigung)',
                'steps_de': [
                    "Anmeldungsuebersicht aufrufen : Gehe im Wettkampf zur Registerkarte Anmeldungen. Sieh die Anmeldungen nach Status: Ausstehend, Genehmigt, Abgelehnt.",
                    "Pruefen und genehmigen : Klicke auf eine Anmeldung, um die Sportlerinformationen zu pruefen. Genehmige einzeln oder im Stapel.",
                    "Mit Begruendung ablehnen : Waehle bei Ablehnung einen Grund: falsche Kategorie, ungueltige Lizenz, verspaetete Anmeldung usw.",
                    "Liste exportieren : Exportiere die Liste der gueltigen Anmeldungen als CSV oder PDF fuer das Wiegen und die Verwaltung am Wettkampftag.",
                ],
                'tip_de': 'Aktiviere die automatische Genehmigung, wenn du nicht jede Anmeldung manuell validieren moechtest.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 5: Wettkampftag - Kampf (8 Tutorials)
    # =========================================================================
    5: {
        'title_de': 'Wettkampftag - Kampf',
        'tutorials': {
            1: {
                'title_de': 'Gruppen automatisch generieren',
                'steps_de': [
                    "Gruppenverwaltung aufrufen : Gehe im Wettkampf zu Gruppen > Automatisch generieren. Waehle die zu verarbeitenden Kategorien aus.",
                    "Verteilung konfigurieren : Definiere: Anzahl der Kaempfer pro Gruppe, Trennung von Mitgliedern desselben Vereins, manuelle Setzliste (optional).",
                    "Generieren und pruefen : Klicke auf 'Generieren'. MartialComp verteilt die Kaempfer und vermeidet vereinsinterne Begegnungen in der ersten Runde.",
                    "Manuell anpassen : Falls noetig, verschiebe Kaempfer per Drag-and-Drop zwischen den Gruppen. Das System prueft Konflikte in Echtzeit.",
                ],
                'tip_de': 'Der Verteilungsalgorithmus garantiert Fairness, indem er Vereine trennt und die Leistungsniveaus zwischen den Gruppen ausgleicht.',
            },
            2: {
                'title_de': 'Gruppen organisieren und umstrukturieren',
                'steps_de': [
                    "Gruppenuebersicht : Der Gruppenbildschirm zeigt alle Kategorien mit Anzahl der Kaempfer, Gruppen und Status (Entwurf, Validiert, Laufend).",
                    "Gruppe bearbeiten : Klicke auf eine Gruppe, um die Kaempfer anzuzeigen. Nutze Drag-and-Drop, um einen Kaempfer in eine andere Gruppe zu verschieben.",
                    "Abwesenheiten verwalten : Markiere einen Kaempfer als abwesend oder zurueckgezogen. Das System berechnet automatisch die Begegnungen und Ranglisten neu.",
                    "Gruppen validieren : Sobald du zufrieden bist, validiere die Gruppen. Diese Aktion generiert automatisch den Begegnungsplan.",
                ],
                'tip_de': 'Validiere die Gruppen Kategorie fuer Kategorie, um die Kaempfe der ersten Kategorien zu beginnen, waehrend du die uebrigen fertigstellst.',
            },
            3: {
                'title_de': 'Den Kampfzeitplan planen',
                'steps_de': [
                    "Kampfflaechen definieren : Gehe zu Zeitplan > Flaechen und definiere die Anzahl der verfuegbaren Tatamis/Rings und ihre Namen (Tatami 1, Ring A usw.).",
                    "Zeitfenster zuweisen : Ziehe die Kategorien auf die Flaechen und Zeitfenster. MartialComp berechnet automatisch die geschaetzte Dauer.",
                    "Konflikte erkennen : Das System erkennt Konflikte: ein Kaempfer, der in 2 Kategorien gleichzeitig angemeldet ist. Nutze die Warnungen zur Anpassung.",
                    "Zeitplan veroeffentlichen : Veroeffentliche den Zeitplan. Kaempfer, Trainer und Kampfrichter erhalten eine Benachrichtigung mit ihren Einsatzzeiten.",
                ],
                'tip_de': 'Plane 20% zusaetzliche Zeit pro Kategorie ein, um die unvermeidlichen Verzoegerungen aufzufangen.',
            },
            4: {
                'title_de': 'Die Kampfschnittstelle nutzen (Live-Bewertung)',
                'steps_de': [
                    "Mit der Flaeche verbinden : Oeffne auf deinem Tablet oder Handy MartialComp und waehle deine zugewiesene Kampfflaeche aus. Gib deine Kampfrichter-PIN ein.",
                    "Die Bewertungsschnittstelle : Der Bildschirm zeigt: die 2 Kaempfer (Rot/Blau), Aktionstasten (Punkte, Strafen), den Timer und den aktuellen Punktestand.",
                    "Punkte vergeben : Druecke die Bewertungstasten: Yuko (+1), Waza-ari (+2), Ippon (+3) fuer den roten oder blauen Kaempfer. Die Punkte werden in Echtzeit aktualisiert.",
                    "Strafen verwalten : Druecke Strafe, um eine Verwarnung (Shido) oder Disqualifikation (Hansoku) zu vergeben. Die Strafen sind kumulativ.",
                    "Kampf beenden : Der Timer stoppt automatisch. Validiere das Ergebnis (Sieg nach Punkten, Ippon, Aufgabe). Die Rangliste wird sofort aktualisiert.",
                ],
                'tip_de': 'Die Schnittstelle ist fuer Tablets im Querformat optimiert. Die Tasten sind absichtlich gross fuer eine schnelle und fehlerfreie Bedienung.',
            },
            5: {
                'title_de': 'Kiosk-Modus Multi-Tatami',
                'steps_de': [
                    "Kiosk-Modus aktivieren : Gehe zu Konfiguration > Kiosk-Modus, aktiviere den Modus und lege eine PIN fuer jede Kampfflaeche fest.",
                    "Jedes Tablet konfigurieren : Melde dich auf jedem Flaechen-Tablet an und waehle die entsprechende Flaeche aus. Gib die PIN ein, um den Bildschirm auf diese Flaeche zu sperren.",
                    "Unabhaengiger Betrieb : Jede Flaeche funktioniert autonom: Bewertung, Timer, Anzeige. Die zentrale Anzeigetafel wird in Echtzeit aktualisiert.",
                    "Zuschauer-Bildschirm : Verbinde einen zusaetzlichen Bildschirm im 'Zuschauer'-Modus, um die Punktzahl im Grossformat anzuzeigen, sichtbar von den Raengen.",
                ],
                'tip_de': 'Der Kiosk-Modus verhindert, dass Kampfrichter versehentlich aus der Bewertungsschnittstelle navigieren.',
            },
            6: {
                'title_de': 'Ranglisten live verfolgen',
                'steps_de': [
                    "Live-Dashboard : Der Verfolgungsbildschirm zeigt in Echtzeit: laufende Kaempfe pro Flaeche, Gruppenranglisten, Fortschritt zu den Finalphasen.",
                    "Nach Kategorie filtern : Waehle eine Kategorie, um die Details zu sehen: abgeschlossene, laufende und ausstehende Gruppen mit vorlaeufigen Ranglisten.",
                    "Automatische Benachrichtigungen : Das System benachrichtigt Trainer automatisch, wenn ihre Kaempfer sich an der Kampfflaeche einfinden muessen.",
                ],
                'tip_de': 'Zeige das Dashboard auf einem grossen Bildschirm im Empfangsbereich an, damit alle Teilnehmer den Fortschritt verfolgen koennen.',
            },
            7: {
                'title_de': 'Finalphasen generieren (Halbfinale/Finale)',
                'steps_de': [
                    "Gruppen abgeschlossen : Sobald alle Gruppen einer Kategorie abgeschlossen sind, berechnet das System die Qualifizierten nach den definierten Regeln (1. und 2. pro Gruppe usw.).",
                    "Turnierbaum generieren : Klicke auf 'Finalphasen generieren'. Der Eliminierungsbaum (Viertelfinale, Halbfinale, Finale, Kampf um Bronze) wird automatisch erstellt.",
                    "Trostrunden verwalten : Wenn die Regeln es vorsehen, werden Trostrunden automatisch mit den Verlierern der Halbfinals generiert.",
                    "Finals starten : Die Kaempfe der Finalphasen erscheinen im Zeitplan. Die Bewertung funktioniert genauso wie bei den Gruppen.",
                ],
                'tip_de': 'Der Eliminierungsbaum wird automatisch erstellt und vermeidet dabei nach Moeglichkeit Begegnungen zwischen Kaempfern desselben Vereins.',
            },
            8: {
                'title_de': 'Die Siegerehrung verwalten',
                'steps_de': [
                    "Podium aufrufen : Klicke in der abgeschlossenen Kategorie auf 'Podium'. Die Endrangliste wird angezeigt: Gold, Silber, Bronze (und moeglicherweise 2x Bronze).",
                    "Schrittweise Enthuellung : Nutze den 'Zeremonie'-Modus fuer eine schrittweise Enthuellung: 3. Platz, dann 2. Platz, dann 1. Platz mit Animationen und Soundeffekten.",
                    "Auf Grossbildschirm projizieren : Verbinde den Praesentationsmodus mit einem Projektor fuer eine spektakulaere Anzeige waehrend der Medaillenverleihung.",
                    "Ergebnisse teilen : Die Podien werden automatisch auf der Wettkampfseite veroeffentlicht und koennen in sozialen Netzwerken geteilt werden.",
                ],
                'tip_de': 'Mache ein Foto des Podiums und fuege es zum Wettkampf hinzu, um die Galerie und die sozialen Netzwerke zu bereichern.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 6: Technische Bewertung (6 Tutorials)
    # =========================================================================
    6: {
        'title_de': 'Technische Bewertung',
        'tutorials': {
            1: {
                'title_de': 'Bewertungskriterien konfigurieren',
                'steps_de': [
                    "Kriterien aufrufen : Gehe im Wettkampf zu Bewertung > Kriterien. Waehle eine Vorlage oder erstelle eigene Kriterien.",
                    "Kriterien definieren : Fuege Bewertungskriterien hinzu: Technik (Stellungen, Uebergaenge), Kraft (Kime, Dynamik), Rhythmus (Tempo, Fluss), Ausdruck (Zanshin, Geist).",
                    "Gewichtungen zuweisen : Definiere die Gewichtung jedes Kriteriums: z.B. Technik 40%, Kraft 25%, Rhythmus 20%, Ausdruck 15%. Die Summe muss 100% ergeben.",
                    "Skala festlegen : Waehle die Bewertungsskala: 1-5, 1-10, 5.0-10.0 oder individuell. Definiere die Schrittweite (0.1, 0.5 oder 1).",
                ],
                'tip_de': 'Die WKF- und WTF-Vorlagen sind vorkonfiguriert. Passe sie nach deinen spezifischen Beduerfnissen an.',
            },
            2: {
                'title_de': 'Kampfrichter den Kategorien zuweisen',
                'steps_de': [
                    "Zuweisungspanel oeffnen : Gehe zu Bewertung > Kampfrichter und sieh die Liste der registrierten Kampfrichter und die abzudeckenden Kategorien.",
                    "Nach Kategorie zuweisen : Ziehe die Kampfrichter auf die Kategorien. Definiere die Anzahl der Kampfrichter pro Kategorie (ueblicherweise 5 oder 7).",
                    "Neutralitaetspruefung : MartialComp prueft automatisch Interessenkonflikte: ein Kampfrichter kann keinen Kaempfer seines eigenen Vereins bewerten.",
                    "Rotationen verwalten : Plane die Rotationen der Kampfrichter zwischen Kategorien, um Ermuedung vorzubeugen und Fairness zu gewaehrleisten.",
                ],
                'tip_de': 'Das Bias-Erkennungssystem analysiert Bewertungsunterschiede zwischen Kampfrichtern und warnt, wenn ein Kampfrichter systematisch zu hoch oder niedrig bewertet.',
            },
            3: {
                'title_de': 'Das technische Bewertungsblatt nutzen',
                'steps_de': [
                    "Als Kampfrichter anmelden : Melde dich auf deinem Tablet mit deinem Kampfrichterkonto an. Waehle die zugewiesene Kategorie aus.",
                    "Bewertungsschnittstelle : Der Bildschirm zeigt den aktuellen Kaempfer, die Bewertungskriterien und das Zahlenfeld. Jedes Kriterium hat seinen eigenen Schieberegler oder sein Zahlenfeld.",
                    "Runde fuer Runde bewerten : Gib fuer jeden Kaempfer deine Bewertung fuer jedes Kriterium ein. Validiere deine Bewertung, bevor du zum naechsten uebergehst.",
                    "Speichern : Deine Bewertung wird sofort gespeichert. Du kannst deine Bewertungen aendern, solange die Runde nicht vom Organisator gesperrt wurde.",
                ],
                'tip_de': 'Die digitale Schnittstelle ist fuer eine schnelle Eingabe auf Tablets optimiert. Ein einziger Tipp fuer jede Bewertung.',
            },
            4: {
                'title_de': 'Technische Teambewertung (Synchron)',
                'steps_de': [
                    "Teammodus verstehen : Bei der Synchron-Bewertung erscheinen zusaetzliche Kriterien: Synchronisation, Raeumliche Ausrichtung, Gemeinsamer Ausdruck.",
                    "Team als Ganzes bewerten : Wenn so konfiguriert, bewerte das Team als Ganzes fuer jedes Kriterium, einschliesslich der Synchronisation.",
                    "Einzeln + Team bewerten : Wenn fuer gemischte Bewertung konfiguriert, bewerte jedes Mitglied einzeln UND fuege dann eine Teambewertung fuer die Synchronisation hinzu.",
                ],
                'tip_de': 'Im Synchron-Modus macht das Synchronisationskriterium typischerweise 20-30% der Gesamtbewertung aus.',
            },
            5: {
                'title_de': 'Bewertungen sperren und veroeffentlichen',
                'steps_de': [
                    "Bewertungen pruefen : Sieh vom Organisator-Dashboard aus die Bewertungen aller Kampfrichter fuer jeden Kaempfer ein. Identifiziere verdaechtige Unterschiede.",
                    "Runde sperren : Klicke auf 'Sperren', um jede Aenderung zu verhindern. Die Endberechnung (hoechste/niedrigste Bewertung streichen, Durchschnitt) wird durchgefuehrt.",
                    "Ergebnisse veroeffentlichen : Veroeffentliche die Ranglisten. Die detaillierten Bewertungen pro Kampfrichter koennen je nach Konfiguration ausgeblendet oder angezeigt werden.",
                    "Testmodus / Zuruecksetzen : Nutze vor dem Wettkampf den Testmodus, um das System zu ueberpruefen. Das Zuruecksetzen loescht alle Testbewertungen.",
                ],
                'tip_de': 'Die rundenweise Sperrung ermoeglicht die Veroeffentlichung von Ergebnissen Runde fuer Runde, waehrend der Wettkampf weiterlaeuft.',
            },
            6: {
                'title_de': 'Vorlaeufige Ranglisten anzeigen',
                'steps_de': [
                    "Ranglisten aufrufen : Sieh auf der Registerkarte Ranglisten die Echtzeit-Ranglisten mit den Bewertungen pro Kriterium und der Endbewertung ein.",
                    "Sortieren und filtern : Sortiere nach Gesamtbewertung oder nach spezifischem Kriterium. Filtere nach Gruppe oder allen Kaempfern.",
                    "Kampfrichterstatistiken : Sieh die Statistiken ein: Durchschnitt pro Kampfrichter, Standardabweichung, Bias-Erkennung. Ein unverzichtbares Werkzeug fuer die Fairness.",
                ],
                'tip_de': 'Die vorlaeufige Rangliste ist nur fuer Organisatoren und Kampfrichter sichtbar. Sie wird den Kaempfern erst nach der Sperrung veroeffentlicht.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 7: Ergebnisse und Palmares (4 Tutorials)
    # =========================================================================
    7: {
        'title_de': 'Ergebnisse und Palmares',
        'tutorials': {
            1: {
                'title_de': 'Wettkampfergebnisse anzeigen',
                'steps_de': [
                    "Wettkampf finden : Waehle im Menue Wettkaempfe oder auf der oeffentlichen Seite den gewuenschten Wettkampf aus.",
                    "Ergebnisse einsehen : Die Ergebnisse sind nach Kategorie geordnet. Fuer jede Kategorie: Podium, vollstaendige Rangliste und Bewertungsdetails.",
                    "Kampfdetails : Klicke auf einen Kampf, um die Details zu sehen: Bewertung pro Runde, Strafen, Timer und moeglicherweise das Kampfvideo.",
                ],
                'tip_de': 'Die oeffentlichen Ergebnisse sind ohne MartialComp-Konto ueber den Wettkampf-Link zugaenglich.',
            },
            2: {
                'title_de': 'Ergebnisse veroeffentlichen und teilen',
                'steps_de': [
                    "Ergebnisse validieren : Pruefe im Organisator-Dashboard die Ergebnisse jeder Kategorie. Klicke auf 'Validieren und veroeffentlichen'.",
                    "Oeffentlichen Link generieren : Ein permanenter Link zur Ergebnisseite wird generiert. Kopiere ihn zum Teilen.",
                    "In sozialen Netzwerken teilen : Nutze die integrierten Teilen-Buttons fuer Facebook, Instagram, Twitter. Die Podien generieren automatisch ein Bild.",
                    "Ergebnis-QR-Code : Generiere einen Ergebnis-QR-Code zum Aushang am Wettkampfort fuer die Zuschauer.",
                ],
                'tip_de': 'Das automatische Podiumsbild ist fuer Instagram Stories (9:16) und Facebook (16:9) formatiert.',
            },
            3: {
                'title_de': 'Ergebnisse exportieren (CSV/PDF)',
                'steps_de': [
                    "Export aufrufen : Gehe zu Ergebnisse > Exportieren und waehle das Format: CSV (Rohdaten), PDF (formatierter Bericht) oder Excel.",
                    "Inhalt waehlen : Waehle aus: Gesamtrangliste, nur Podien, Detail pro Kategorie, Medaillenspiegel pro Verein oder Alles.",
                    "PDF anpassen : Waehle fuer das PDF die Vorlage: offizieller Bericht (mit Verbandslogo), einfacher Bericht oder Urkunden.",
                ],
                'tip_de': 'Der Medaillenspiegel pro Verein ist besonders nuetzlich fuer Verbaende und Sponsoren.',
            },
            4: {
                'title_de': 'Deinen persoenlichen Palmares einsehen',
                'steps_de': [
                    "Auf Mein Palmares zugreifen : Klicke in deinem Sportlerprofil auf 'Palmares'. Deine Wettkampfhistorie wird angezeigt.",
                    "Statistiken anzeigen : Sieh ein: Anzahl der Wettkaempfe, Medaillen (Gold/Silber/Bronze), Siegquote, Entwicklung ueber die Zeit.",
                    "Palmares teilen : Generiere einen oeffentlichen Link zu deinem Palmares oder exportiere ihn als PDF fuer Bewerbungsunterlagen oder Sponsoring-Anfragen.",
                ],
                'tip_de': 'Dein Palmares wird nach jedem Wettkampf automatisch aktualisiert. Er ist in deinem oeffentlichen Profil sichtbar, wenn du es erlaubst.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 8: Gradverwaltung (5 Tutorials)
    # =========================================================================
    8: {
        'title_de': 'Gradverwaltung',
        'tutorials': {
            1: {
                'title_de': 'Das Gradsystem konfigurieren',
                'steps_de': [
                    "Konfiguration aufrufen : Gehe zu Einstellungen > Grade, waehle die Disziplin aus und definiere dein Gradsystem.",
                    "Stufen erstellen : Fuege die Stufen in der Reihenfolge hinzu: Weisser Guertel, Gelb, Orange, Gruen, Blau, Braun, Schwarz 1. Dan, 2. Dan usw.",
                    "Voraussetzungen definieren : Definiere fuer jeden Grad: Mindestzeit im vorherigen Grad, Mindestalter, Mindestanzahl an Unterrichtsstunden, ob eine Pruefung erforderlich ist.",
                    "Farben zuweisen : Weise die Guertelfarben fuer die Darstellung in der Oberflaeche und den Profilen zu.",
                ],
                'tip_de': 'Die Standard-Gradsysteme (Judo, Karate, TKD, BJJ) sind vorkonfiguriert. Du kannst sie anpassen oder neue erstellen.',
            },
            2: {
                'title_de': 'Einem Sportler einen Grad zuweisen',
                'steps_de': [
                    "Profil aufrufen : Klicke im Sportlerprofil auf die Registerkarte Grade und dann auf 'Neuen Grad zuweisen'.",
                    "Grad auswaehlen : Waehle den Grad aus der Liste. Das System prueft automatisch die Voraussetzungen (Zeit, Alter, Pruefungen).",
                    "Details eingeben : Fuege das Datum der Zuweisung, den Ort, die Pruefungskommission/den Pruefer und Anmerkungen hinzu.",
                    "Massenzuweisung : Gehe zu Grade > Massenzuweisung, waehle mehrere Sportler aus und weise allen den gleichen Grad zu.",
                ],
                'tip_de': 'Eine Glueckwunsch-E-Mail wird automatisch an den Sportler mit seinem neuen Grad gesendet.',
            },
            3: {
                'title_de': 'Eine Gradpruefung organisieren',
                'steps_de': [
                    "Pruefung erstellen : Gehe zu Grade > Pruefungen und erstelle eine neue Pruefung: Datum, Ort, Disziplin, abgedeckte Grade, Pruefungskommission.",
                    "Kandidaten anmelden : Fuege Kandidaten manuell hinzu oder erlaube die Selbstanmeldung. Das System prueft die Voraussetzungen jedes Einzelnen.",
                    "Am Pruefungstag : Nutze die Pruefungsschnittstelle, um jeden Kandidaten zu bewerten: erforderliche Techniken, Kampf, Theorie.",
                    "Ergebnisse veroeffentlichen : Validiere die Bestandenen und Durchgefallenen. Die Grade werden den bestandenen Kandidaten automatisch zugewiesen.",
                ],
                'tip_de': 'Gradpruefungen koennen mit einem Wettkampf verknuepft werden (z.B. Gradverleihung waehrend eines Turniers).',
            },
            4: {
                'title_de': 'Gradhistorie und -entwicklung verwalten',
                'steps_de': [
                    "Historie anzeigen : Das Profil jedes Sportlers zeigt die vollstaendige Gradhistorie: Datum, Ort, Pruefungskommission, Anmerkungen.",
                    "Entwicklung visualisieren : Ein Diagramm zeigt die Entwicklung ueber die Zeit. Vergleiche mit dem Vereinsdurchschnitt.",
                    "Grad widerrufen : Im Fehlerfall widerrufe einen Grad mit Begruendung. Die Historie behaelt den Eintrag des Widerrufs.",
                ],
                'tip_de': 'Die Gradhistorie ist uebertragbar, wenn der Sportler den Verein wechselt.',
            },
            5: {
                'title_de': 'Gradzertifikate erstellen',
                'steps_de': [
                    "Zertifikate aufrufen : Gehe zu Grade > Zertifikate, waehle den Sportler und den Grad, fuer den ein Zertifikat erstellt werden soll.",
                    "Vorlage waehlen : Waehle eine Zertifikatsvorlage: offiziell (mit Verbandslogo), Verein oder individuell.",
                    "Anpassen : Fuege die Unterschriften, das Vereinssiegel und besondere Vermerke hinzu. Der Verifizierungs-QR-Code wird automatisch hinzugefuegt.",
                    "Erstellen und verteilen : Erstelle das PDF. Drucke es aus oder sende es per E-Mail. Der QR-Code ermoeglicht es jedem, die Echtheit des Zertifikats zu ueberpruefen.",
                ],
                'tip_de': 'Der Verifizierungs-QR-Code fuehrt zu einer oeffentlichen MartialComp-Seite, die die Gueltigkeit des Grades bestaetigt.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 9: Verbandsverwaltung (8 Tutorials)
    # =========================================================================
    9: {
        'title_de': 'Verbandsverwaltung',
        'tutorials': {
            1: {
                'title_de': 'Angeschlossene Vereine verwalten',
                'steps_de': [
                    "Uebersicht : Das Verbandsdashboard zeigt die Karte der angeschlossenen Vereine, ihren Status (aktiv, ausstehend, abgelaufen) und Statistiken.",
                    "Antraege bearbeiten : Neue Mitgliedschaftsantraege erscheinen unter Vereine > Ausstehend. Pruefe die Dokumente und genehmige oder lehne ab.",
                    "Verlaengerungen ueberwachen : Sieh die bald ablaufenden Mitgliedschaften ein. Sende automatische Erinnerungen 30, 15 und 7 Tage vorher.",
                ],
                'tip_de': 'Das Verbandsdashboard bietet einen Echtzeit-Ueberblick ueber die Gesamtzahl der lizenzierten Sportler aller Vereine.',
            },
            2: {
                'title_de': 'Saisons und Beitraege verwalten',
                'steps_de': [
                    "Saison erstellen : Gehe zu Saisons > Neu, definiere das Start- und Enddatum sowie die Beitragstarife nach Typ (Verein, Einzel, Junior, Senior).",
                    "Beitraege konfigurieren : Definiere die Betraege pro Kategorie: Vereinsmitgliedschaft (Festbetrag), Einzellizenz (pro Sportler), Versicherung (optional).",
                    "Zahlungen verfolgen : Sieh die eingegangenen, ausstehenden und ueberfaelligen Beitraege in Echtzeit ein. Sende automatische Erinnerungen.",
                    "Saison abschliessen : Schliesse am Ende der Saison ab, um den Finanzbericht zu erstellen und die naechste Saison vorzubereiten.",
                ],
                'tip_de': 'Beitraege koennen online via Stripe oder per Bankueberweisung bezahlt werden. Die Verfolgung ist in beiden Faellen automatisch.',
            },
            3: {
                'title_de': 'Wettkaempfe ueberwachen',
                'steps_de': [
                    "Gesamtuebersicht : Der Verbandskalender zeigt alle Wettkaempfe der angeschlossenen Vereine mit Status und Teilnehmerzahl.",
                    "Wettkampf anerkennen : Vereine reichen ihre Wettkaempfe zur Anerkennung ein. Pruefe die Regeln, die Kampfrichter und validiere.",
                    "Ergebnisse einsehen : Greife auf die Ergebnisse aller anerkannten Wettkaempfe zu. Die nationalen Ranglisten werden automatisch aktualisiert.",
                ],
                'tip_de': 'Vom Verband anerkannte Wettkaempfe werden im Verzeichnis und im oeffentlichen Kalender hervorgehoben.',
            },
            4: {
                'title_de': 'Kampfrichter und ihre Qualifikationen verwalten',
                'steps_de': [
                    "Kampfrichter-Datenbank : Sieh die Datenbank der angeschlossenen Kampfrichter mit ihren Qualifikationen, Spezialisierungen und Aktivitaetshistorie ein.",
                    "Qualifikationsstufen verwalten : Weise Qualifikationsstufen zu: regional, national, international. Definiere die Befoerderungskriterien.",
                    "Neutralitaetsueberwachung : MartialComp analysiert die Bewertungsstatistiken jedes Kampfrichters und erkennt moegliche Voreingenommenheit.",
                ],
                'tip_de': 'Kampfrichter mit einer ausgeglichenen Bewertungshistorie werden fuer wichtige Wettkaempfe hervorgehoben.',
            },
            5: {
                'title_de': 'Zertifizierungen verwalten',
                'steps_de': [
                    "Vorlage erstellen : Gestalte deine Zertifikatsvorlagen mit dem Verbandslogo, den rechtlichen Angaben und den dynamischen Feldern.",
                    "Zertifikate ausstellen : Erstelle Zertifikate fuer: Grade, Kampfrichterqualifikationen, Lehrdiplome, verschiedene Bescheinigungen.",
                    "Oeffentliche Verifizierung : Jedes Zertifikat hat einen einzigartigen QR-Code. Jeder kann ihn scannen, um die Echtheit auf martialcomp.com zu ueberpruefen.",
                ],
                'tip_de': 'Digitale Zertifikate sind dank des mit MartialComp verknuepften Verifizierungs-QR-Codes faelschungssicher.',
            },
            6: {
                'title_de': 'Die oeffentliche Verbandsseite personalisieren',
                'steps_de': [
                    "Website-Baukasten aufrufen : Gehe zu Einstellungen > Oeffentliche Seite und oeffne den Seiteneditor. Dein Verband hat eine URL: verband.martialcomp.com.",
                    "Erscheinung anpassen : Waehle Farben, Thema, Banner und Logo. Fuege eine Beschreibung und Links zu deinen sozialen Netzwerken hinzu.",
                    "Inhalte hinzufuegen : Veroeffentliche Neuigkeiten, Fotogalerien, Videos, Wettkampfkalender und herunterladbare Dokumente.",
                    "Seiten verwalten : Erstelle zusaetzliche Seiten: Geschichte, Vorstand, Regelwerk, Kontakt.",
                ],
                'tip_de': 'Die oeffentliche Seite ist SEO-optimiert. Je vollstaendiger sie ist, desto besser wird sie bei Google platziert.',
            },
            7: {
                'title_de': 'Statistiken und Berichte anzeigen',
                'steps_de': [
                    "Analyse-Dashboard : Das Dashboard zeigt die KPIs: Anzahl der Vereine, Sportler, Wettkaempfe, aktive Lizenzen, Wachstum.",
                    "Berichte pro Verein : Erstelle detaillierte Berichte pro Verein: Mitgliederzahl, Beitraege, Wettkampfteilnahme, verliehene Grade.",
                    "Berichte pro Disziplin : Analysiere die Verteilung nach Disziplin, Alter, Geschlecht. Identifiziere Wachstumstrends.",
                    "Exportieren und teilen : Exportiere die Berichte als PDF, Excel oder CSV fuer deine Jahreshauptversammlungen und offiziellen Berichte.",
                ],
                'tip_de': 'Die Berichte werden in Echtzeit aktualisiert. Plane automatische monatliche oder vierteljaehrliche Versendungen.',
            },
            8: {
                'title_de': 'Ausbildungsprogramme verwalten',
                'steps_de': [
                    "Programm erstellen : Gehe zu Ausbildung > Neu und definiere das Programm: Titel, Disziplin, Niveau, Dauer, Voraussetzungen.",
                    "Sitzungen planen : Fuege die Ausbildungssitzungen hinzu: Daten, Orte, Ausbilder, Platzzahl.",
                    "Anmeldungen verwalten : Trainer und Kampfrichter melden sich online an. Validiere die Anmeldungen und sende die Einberufungen.",
                    "Nachverfolgung und Zertifizierung : Verfolge die Anwesenheit bei den Sitzungen. Stelle den Teilnehmern, die das Programm abgeschlossen haben, Zertifizierungen aus.",
                ],
                'tip_de': 'Abgeschlossene Ausbildungsprogramme erscheinen automatisch in den Profilen von Trainern und Kampfrichtern.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 10: Finanzen (5 Tutorials)
    # =========================================================================
    10: {
        'title_de': 'Finanzen',
        'tutorials': {
            1: {
                'title_de': 'Vereinstransaktionen verfolgen',
                'steps_de': [
                    "Uebersicht : Das Finanz-Dashboard zeigt: Saldo, Einnahmen des Monats, Ausgaben und Trenddiagramm.",
                    "Transaktion erfassen : Fuege eine Einnahme oder Ausgabe hinzu: Betrag, Datum, Kategorie (Beitraege, Ausruestung, Miete), Beschreibung.",
                    "Automatische Kategorisierung : MartialComp kategorisiert wiederkehrende Transaktionen automatisch. Passe die Kategorien nach deinen Beduerfnissen an.",
                ],
                'tip_de': 'Verbinde dein Bankkonto, um Transaktionen automatisch zu importieren und den Abgleich zu vereinfachen.',
            },
            2: {
                'title_de': 'Rechnungen erstellen und versenden',
                'steps_de': [
                    "Rechnung erstellen : Gehe zu Finanzen > Rechnungen > Neu, waehle den Empfaenger (Sportler, Verein, Sponsor) und die Rechnungsposten.",
                    "Anpassen : Fuege dein Logo, die rechtlichen Hinweise und die Zahlungsbedingungen hinzu. Waehle die Waehrung und den Mehrwertsteuersatz.",
                    "Versenden : Sende die Rechnung per E-Mail. Der Empfaenger erhaelt einen Online-Zahlungslink (Stripe) und die Rechnung als PDF.",
                    "Zahlungen verfolgen : Sieh die bezahlten, ausstehenden und ueberfaelligen Rechnungen ein. Sende automatische Erinnerungen.",
                ],
                'tip_de': 'Die Beitraege der Sportler generieren automatisch Rechnungen, wenn du diese Option aktivierst.',
            },
            3: {
                'title_de': 'Online-Zahlungen verwalten (Stripe)',
                'steps_de': [
                    "Stripe verbinden : Gehe zu Einstellungen > Zahlungen und klicke auf 'Stripe verbinden'. Folge den Schritten, um dein Stripe-Konto zu verknuepfen.",
                    "Checkout konfigurieren : Lege die Tarife fest fuer: Beitraege, Wettkampfanmeldungen, Shop. Aktiviere bei Bedarf wiederkehrende Zahlungen.",
                    "Zahlung testen : Nutze den Stripe-Testmodus, um alles zu ueberpruefen, bevor du echte Zahlungen aktivierst.",
                    "Einnahmen verfolgen : Das Stripe-Dashboard in MartialComp zeigt empfangene Zahlungen, Erstattungen und Ueberweisungen auf dein Bankkonto.",
                ],
                'tip_de': 'Stripe berechnet eine Gebuehr von 1,4% + 0,25 EUR pro Transaktion in Europa. Die Gutschrift erfolgt in 2-7 Tagen.',
            },
            4: {
                'title_de': 'Kontoauszuege importieren',
                'steps_de': [
                    "Auszug herunterladen : Exportiere den Kontoauszug von deiner Bank im Format CSV, OFX oder QIF.",
                    "In MartialComp importieren : Gehe zu Finanzen > Importieren und lade die Datei hoch. MartialComp erkennt das Format und ordnet die Spalten zu.",
                    "Abgleichen : Das System ordnet die importierten Transaktionen automatisch den bestehenden Rechnungen und Beitraegen zu.",
                    "Validieren : Pruefe die Zuordnungen, korrigiere Fehler und validiere. Nicht zugeordnete Transaktionen werden als ausstehend hinzugefuegt.",
                ],
                'tip_de': 'Monatliche Bankimporte halten deine Buchhaltung ohne manuellen Aufwand auf dem neuesten Stand.',
            },
            5: {
                'title_de': 'Mitgliedsbeitraege der Sportler verwalten',
                'steps_de': [
                    "Tarife konfigurieren : Gehe zu Finanzen > Beitraege und lege die Jahrestarife nach Kategorie fest: Kind, Jugendlicher, Erwachsener, Familie.",
                    "Zahlungsaufforderungen erstellen : Erstelle zu Saisonbeginn die Zahlungsaufforderungen fuer alle Mitglieder. Jeder erhaelt eine E-Mail mit einem Zahlungslink.",
                    "Zahlungen verfolgen : Sieh die bezahlten, ausstehenden und ueberfaelligen Beitraege ein. Der Status erscheint im Profil jedes Sportlers.",
                    "Erinnerungen senden : Plane automatische Erinnerungen: 1 Woche, 2 Wochen, 1 Monat nach dem Faelligkeitsdatum.",
                ],
                'tip_de': 'Sportler mit ueberfaelligen Beitraegen koennen von der Wettkampfanmeldung ausgeschlossen werden.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 11: Veranstaltungen und Kalender (3 Tutorials)
    # =========================================================================
    11: {
        'title_de': 'Veranstaltungen und Kalender',
        'tutorials': {
            1: {
                'title_de': 'Eine Veranstaltung erstellen (Seminar, Gala, Versammlung)',
                'steps_de': [
                    "Veranstaltung erstellen : Gehe zu Kalender > Neue Veranstaltung und gib ein: Typ (Seminar, Gala, Versammlung, Tag der offenen Tuer), Titel, Daten, Ort und Beschreibung.",
                    "Anmeldungen konfigurieren : Aktiviere die Online-Anmeldungen. Lege die Platzzahl, den Preis (kostenlos oder kostenpflichtig) und den Anmeldeschluss fest.",
                    "Veroeffentlichen : Veroeffentliche die Veranstaltung. Sie erscheint im Vereinskalender und kann in sozialen Netzwerken geteilt werden.",
                ],
                'tip_de': 'Seminare mit Gastmeistern sind hervorragende Marketinginstrumente. Fuege ihr Foto und ihre Biografie hinzu, um mehr Teilnehmer anzuziehen.',
            },
            2: {
                'title_de': 'Wiederkehrende Veranstaltungen verwalten',
                'steps_de': [
                    "Wiederholung erstellen : Markiere bei der Erstellung 'Wiederkehrende Veranstaltung'. Lege die Haeufigkeit fest: taeglich, woechentlich, monatlich.",
                    "Ausnahmen verwalten : Sage ein einzelnes Vorkommen ab oder aendere es, ohne die anderen zu beeinflussen (z.B. Kurs faellt wegen Feiertag aus).",
                    "Serie aendern : Aendere die gesamte Serie (z.B. permanente Zeitaenderung) oder nur ein einzelnes Vorkommen.",
                ],
                'tip_de': 'Woechentliche Kurse sollten als wiederkehrende Veranstaltungen erstellt werden, damit sie automatisch im Kalender erscheinen.',
            },
            3: {
                'title_de': 'Anmeldungen und Anwesenheit verfolgen',
                'steps_de': [
                    "Angemeldete anzeigen : Sieh in der Veranstaltung die Liste der Angemeldeten mit ihrem Status ein: angemeldet, bestaetigt, abgesagt.",
                    "Anwesenheit erfassen : Erfasse am Tag der Veranstaltung die Anwesenheit per Liste oder QR-Code.",
                    "Exportieren : Exportiere die Teilnehmerliste als CSV oder PDF fuer deine Unterlagen.",
                ],
                'tip_de': 'Die Teilnahmequote bei Veranstaltungen ist ein wichtiger Indikator fuer das Engagement deiner Mitglieder.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 12: Familienverwaltung (3 Tutorials)
    # =========================================================================
    12: {
        'title_de': 'Familienverwaltung',
        'tutorials': {
            1: {
                'title_de': 'Eine Familiengruppe erstellen',
                'steps_de': [
                    "Familiengruppen aufrufen : Gehe in deinem Profil zu Einstellungen > Familiengruppe > Erstellen.",
                    "Mitglieder hinzufuegen : Fuege jedes Familienmitglied hinzu: Ehepartner, Kinder. Verknuepfe ihre bestehenden MartialComp-Konten oder erstelle neue.",
                    "Verantwortlichen festlegen : Der Verantwortliche der Familiengruppe erhaelt alle Benachrichtigungen und verwaltet die Zahlungen fuer die ganze Familie.",
                ],
                'tip_de': 'Einige Vereine bieten Familientarife an (Rabatt ab dem 3. Mitglied). Die Familiengruppe aktiviert diese Rabatte automatisch.',
            },
            2: {
                'title_de': 'Die ganze Familie fuer einen Wettkampf anmelden',
                'steps_de': [
                    "Gruppenanmeldung : Klicke im Wettkampf auf 'Meine Familie anmelden'. Die berechtigten Mitglieder deiner Familiengruppe werden angezeigt.",
                    "Auswaehlen und bestaetigen : Waehle die anzumeldenden Mitglieder aus. Die Kategorien werden fuer jedes automatisch vorgeschlagen.",
                    "Einmalige Zahlung : Bezahle alle Anmeldungen in einer einzigen Transaktion.",
                ],
                'tip_de': 'Die Gruppenanmeldung spart wertvolle Zeit, wenn mehrere Kinder am selben Wettkampf teilnehmen.',
            },
            3: {
                'title_de': 'Familien-Zahlungszentrale',
                'steps_de': [
                    "Uebersicht : Die Familienzentrale zeigt alle Beitraege, Anmeldungen und Rechnungen der Familie auf einem einzigen Bildschirm.",
                    "Gebuendelte Zahlung : Fasse mehrere ausstehende Zahlungen zusammen und bezahle in einer einzigen Transaktion.",
                    "Historie : Sieh die vollstaendige Zahlungshistorie der Familie mit herunterladbaren Quittungen ein.",
                ],
                'tip_de': 'Aktiviere die automatische Lastschrift, um nie einen Beitrag zu vergessen.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 13: Aufgabenverwaltung (Kanban) (2 Tutorials)
    # =========================================================================
    13: {
        'title_de': 'Aufgabenverwaltung (Kanban)',
        'tutorials': {
            1: {
                'title_de': 'Das Kanban-Board nutzen',
                'steps_de': [
                    "Board erstellen : Gehe zu Werkzeuge > Kanban und erstelle ein neues Board: Name, Beschreibung und eingeladene Mitglieder.",
                    "Spalten hinzufuegen : Erstelle die Spalten deines Workflows: Zu erledigen, In Bearbeitung, Wartend, Erledigt. Passe Namen und Farben an.",
                    "Aufgaben erstellen : Fuege Aufgaben hinzu mit: Titel, Beschreibung, Faelligkeitsdatum, Verantwortlicher, Prioritaet (hoch/mittel/niedrig) und Tags.",
                    "Per Drag-and-Drop verwalten : Verschiebe Aufgaben zwischen den Spalten durch Ziehen. Die Verschiebungshistorie wird aufbewahrt.",
                ],
                'tip_de': 'Erstelle ein eigenes Board fuer jeden zu organisierenden Wettkampf. Standardaufgaben (Halle buchen, Medaillen bestellen usw.) koennen aus einer Vorlage importiert werden.',
            },
            2: {
                'title_de': 'Organisatorische Aufgaben verwalten',
                'steps_de': [
                    "Wettkampfvorlage : Nutze die Vorlage 'Wettkampforganisation', die Standardaufgaben enthaelt: Logistik, Kommunikation, Kampfrichter, Medaillen usw.",
                    "Mitgliedern zuweisen : Weise jede Aufgabe einem Mitglied des Organisationsteams zu. Lege die Fristen fest.",
                    "Fortschritt verfolgen : Der allgemeine Fortschrittsbalken wird oben im Board angezeigt. Ueberfaellige Aufgaben werden rot hervorgehoben.",
                ],
                'tip_de': 'Das Kanban-Board ist ueber die mobile App zugaenglich, um Aufgaben unterwegs zu aktualisieren.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 14: Online-Shop (2 Tutorials)
    # =========================================================================
    14: {
        'title_de': 'Online-Shop',
        'tutorials': {
            1: {
                'title_de': 'Den Vereins-Shop einrichten',
                'steps_de': [
                    "Shop aktivieren : Gehe zu Einstellungen > Shop und aktiviere die E-Commerce-Funktionalitaet. Verbinde dein Stripe-Konto, falls noch nicht geschehen.",
                    "Produkte hinzufuegen : Erstelle deine Produkte: Name, Beschreibung, Fotos, Preis, verfuegbare Groessen/Varianten, Lagerbestand.",
                    "Nach Kategorien organisieren : Ordne deine Produkte ein: Uniformen (Kimono, Dobok, Handschuhe), Ausruestung (Schutzausruestung, Taschen), Zubehoer (Guertel, Aufnaeher), Merchandising.",
                    "Shop veroeffentlichen : Dein Shop ist ueber die oeffentliche Seite deines Vereins zugaenglich. Teile den Link oder QR-Code.",
                ],
                'tip_de': 'Biete Pakete (Kimono + Guertel + Tasche) mit Rabatt an, um den durchschnittlichen Bestellwert zu erhoehen.',
            },
            2: {
                'title_de': 'Eine Bestellung aufgeben',
                'steps_de': [
                    "Shop durchstoebern : Gehe ueber die Seite deines Vereins zum Shop. Stoebere die Produkte nach Kategorie durch.",
                    "In den Warenkorb legen : Waehle die Groesse/Variante und lege sie in den Warenkorb. Der Warenkorb bleibt zwischen den Sitzungen erhalten.",
                    "Bestellen und bezahlen : Bestaetige deinen Warenkorb, waehle die Liefermethode (Abholung im Dojo oder Postversand) und bezahle online.",
                    "Bestellung verfolgen : Erhalte Benachrichtigungen bei jedem Schritt: Bestellung bestaetigt, in Vorbereitung, abholbereit / versendet.",
                ],
                'tip_de': 'Der Modus \'Abholung im Dojo\' spart Versandkosten. Dein Trainer uebergibt dir deine Bestellung im naechsten Training.',
            },
        },
    },

    # =========================================================================
    # Abschnitt 15: Erweiterte Funktionen (5 Tutorials)
    # =========================================================================
    15: {
        'title_de': 'Erweiterte Funktionen',
        'tutorials': {
            1: {
                'title_de': 'Wettkampf-Streaming einrichten',
                'steps_de': [
                    "Streaming vorbereiten : Erstelle ein Live-Event auf YouTube, Twitch oder Facebook. Kopiere die Streaming-URL und den Streaming-Schluessel.",
                    "In MartialComp konfigurieren : Gehe im Wettkampf zu Konfiguration > Streaming. Fuege die URL ein und aktiviere die Anzeige auf der oeffentlichen Seite.",
                    "Bewertungs-Overlay : Aktiviere das MartialComp-Overlay, das die Live-Bewertung im Video-Stream anzeigt. Passe Position und Stil an.",
                    "Starten und testen : Starte den Stream und ueberpruefen, ob das Overlay funktioniert. Zuschauer sehen die Live-Bewertung im Stream.",
                ],
                'tip_de': 'Streaming mit MartialComp-Bewertungs-Overlay verleiht auch kleinen Wettkaempfen ein professionelles Erscheinungsbild.',
            },
            2: {
                'title_de': 'Die mobile App nutzen',
                'steps_de': [
                    "App herunterladen : Suche 'MartialComp' im Play Store (Android) oder App Store (iOS). Installiere und oeffne sie.",
                    "Anmelden : Melde dich mit deinem bestehenden MartialComp-Konto an. Du kannst auch die Anmeldung mit Google, Facebook oder Apple nutzen.",
                    "Mobile Oberflaeche entdecken : Die App bietet: Profil, Ergebnisse, Kalender, Push-Benachrichtigungen, persoenlichen QR-Code und Wettkampfanmeldung.",
                    "Offline-Modus : Wesentliche Daten (Profil, Grad, Lizenz) sind ohne Verbindung verfuegbar. Automatische Synchronisation bei Wiederverbindung.",
                ],
                'tip_de': 'Aktiviere Push-Benachrichtigungen, um Live-Ergebniswarnungen waehrend der Wettkaempfe zu erhalten.',
            },
            3: {
                'title_de': 'Rolle in der App wechseln',
                'steps_de': [
                    "Rollenauswahl aufrufen : Tippe auf deinen Avatar oben auf dem Bildschirm oder wische von links, um das Seitenmenue zu oeffnen.",
                    "Rolle auswaehlen : Deine Rollenliste wird angezeigt: Trainer, Sportler, Kampfrichter, Vereinsleiter. Tippe auf die gewuenschte Rolle.",
                    "Angepasste Oberflaeche : Dashboard und Menue werden sofort aktualisiert, um die ausgewaehlte Rolle widerzuspiegeln.",
                ],
                'tip_de': 'Du kannst Trainer in einem Verein und Sportler in einem anderen sein. Jede Rolle ist mit ihrer Organisation verknuepft.',
            },
            4: {
                'title_de': 'Erweiterter Datenimport/-export',
                'steps_de': [
                    "Unterstuetzte Formate : MartialComp unterstuetzt den Import und Export in CSV, Excel (XLSX), JSON und PDF. Jedes Modul hat seine eigenen Optionen.",
                    "Import mit Zuordnung : Die Zuordnungsoberflaeche ermoeglicht es, jede Dateistruktur den MartialComp-Feldern zuzuordnen.",
                    "Benutzerdefinierter Export : Waehle die zu exportierenden Felder, Filter und das Format. Plane automatische wiederkehrende Exporte.",
                    "Massenoperationen : Massenoperationen ermoeglichen die gleichzeitige Aenderung von: Grad, Gruppe, Anmeldestatus usw.",
                ],
                'tip_de': 'Der JSON-Export ist ideal fuer Integrationen mit Drittsystemen (Website, externe Anwendung, CRM).',
            },
            5: {
                'title_de': 'Ad-hoc-Kampfrichter verwalten (Freiwillige)',
                'steps_de': [
                    "Temporaeren Kampfrichter erstellen : Gehe am Wettkampftag zu Kampfrichter > Freiwilligen hinzufuegen und erstelle ein temporaeres Profil: Name, Verein und Spezialisierung.",
                    "PIN zuweisen : Eine einzigartige PIN wird automatisch generiert. Der Freiwillige nutzt diese PIN, um auf die Bewertungsschnittstelle zuzugreifen.",
                    "Kategorien zuweisen : Weise den freiwilligen Kampfrichter den Kategorien zu wie einen regulaeren Kampfrichter. Er kann sofort mit der Bewertung beginnen.",
                    "Nach dem Wettkampf : Das temporaere Profil wird nach dem Wettkampf archiviert. Die Bewertungen bleiben in der Historie erhalten.",
                ],
                'tip_de': 'Ad-hoc-Kampfrichter sind unverzichtbar fuer kleine Wettkaempfe, bei denen die Anzahl offizieller Kampfrichter begrenzt ist.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to German (hardcoded translations)'

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

            section.title_de = sec_data['title_de']
            if not dry_run:
                section.save(update_fields=['title_de'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_de"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_de = tut_data['title_de']
                tutorial.steps_de = json.dumps(tut_data['steps_de'], ensure_ascii=False)
                tutorial.tip_de = tut_data.get('tip_de', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_de', 'steps_de', 'tip_de'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_de"]}')

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
