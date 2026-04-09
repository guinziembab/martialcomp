# MartialComp Dashboards

## Einführung

Dieses Verzeichnis enthält die vollständige Dokumentation der verschiedenen Dashboards, die in der MartialComp-Anwendung verfügbar sind. Jeder Benutzertyp verfügt über ein spezifisches Dashboard für seine Rolle, das an seine Bedürfnisse angepasste Funktionen bietet.

## Dashboard-Typen

MartialComp bietet mehrere Dashboards, die jeweils für eine bestimmte Rolle konzipiert sind:

1. [**Teilnehmer-Dashboard**](./participants/README.md) - Für Kampfkunst-Praktizierende, die an Wettkämpfen teilnehmen
2. [**Verein-Dashboard**](./clubs/README.md) - Für Vereinsleiter und ihre Administratoren
3. [**Verbands-Dashboard**](./federations/README.md) - Für Verbandsadministratoren
4. [**Schiedsrichter/Kampfrichter-Dashboard**](./referees/README.md) - Für Schiedsrichter und Kampfrichter, die Wettkämpfe bewerten
5. [**Multidisziplin-Trainer-Dashboard**](./coaches/README.md) - Für Trainer, die mehrere Disziplinen betreuen
6. [**Kampf-Dashboard**](./combat/README.md) - Spezialisierte Oberfläche für die Kampfverwaltung

## Zugang zu den Dashboards

Jeder Benutzer wird nach der Anmeldung automatisch zum seinem Rolle entsprechenden Dashboard weitergeleitet. Die Weiterleitung wird durch die `dashboard`-View in der Datei `competitions/views/dashboard/base.py` verwaltet.

## Gemeinsame Struktur der Dashboards

Alle Dashboards teilen eine gemeinsame Struktur:

- **Kopfzeile**: Zeigt den Benutzernamen, die Rolle an und bietet Zugang zu den Einstellungen und zur Abmeldung
- **Seitenleiste**: Navigation zu den verschiedenen Bereichen des Dashboards
- **Hauptinhalt**: Zeigt die spezifischen Informationen und Funktionen jedes Bereichs an
- **Fußzeile**: Informationen zur Anwendungsversion und nützliche Links

## Dashboard-Anpassung

Benutzer können bestimmte Aspekte ihres Dashboards anpassen:
- Auswahl der auf der Startseite angezeigten Widgets
- Reihenfolge der Informationsanzeige
- Benachrichtigungseinstellungen

## Gemeinsame Funktionen

Alle Dashboards bieten diese Grundfunktionen:
- Übersicht mit wichtigen Statistiken
- Benachrichtigungen und Warnungen
- Benutzerprofilverwaltung
- Kalender kommender Veranstaltungen
- Zugang zur Dokumentation

## Mehrsprachige Unterstützung

Alle Dashboards unterstützen Mehrsprachigkeit und sind in folgenden Sprachen verfügbar:
- Französisch (fr) - Standardsprache
- Englisch (en)
- Spanisch (es)
- Italienisch (it)
- Deutsch (de)
- Norwegisch (no)
- Japanisch (ja)
- Chinesisch (zh)
- Hindi (hi)
- Arabisch (ar)
- Swahili (sw)
- Amharisch (am)
- Zulu (zu)
- Yoruba (yo)
- Portugiesisch (pt)
- Koreanisch (ko)

## Technisches Design

Die Dashboards sind implementiert mit:
- Django für das Backend
- HTML/CSS/JavaScript für das Frontend
- Bootstrap für responsives Layout
- AJAX-Technologie für dynamische Aktualisierungen

## Ausführliche Dokumentation

Weitere Details zu jedem Dashboard finden Sie in den obigen Links oder in den Unterordnern dieses Verzeichnisses.
