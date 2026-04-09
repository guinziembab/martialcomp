# MartialComp Dashbord

## Introduksjon

Denne katalogen inneholder komplett dokumentasjon for de ulike dashbordene (kontrollpanelene) som er tilgjengelige i MartialComp-applikasjonen. Hver brukertype har et spesifikt dashbord tilpasset sin rolle, med funksjoner som er skreddersydd for deres behov.

## Typer Dashbord

MartialComp tilbyr flere dashbord, hvert designet for en spesifikk rolle:

1. [**Deltaker-dashbord**](./participants/README_no.md) - For kampsportutøvere som deltar i konkurranser
2. [**Klubb-dashbord**](./clubs/README_no.md) - For klubbledere og administratorer
3. [**Forbunds-dashbord**](./federations/README_no.md) - For forbundsadministratorer
4. [**Dommer-dashbord**](./referees/README_no.md) - For dommere som vurderer konkurranser
5. [**Flerdisiplin-trener-dashbord**](./coaches/README_no.md) - For trenere som administrerer flere disipliner
6. [**Kamp-dashbord**](./combat/README_no.md) - Spesialisert grensesnitt for kampadministrasjon

## Tilgang til Dashbord

Hver bruker blir automatisk videresendt til dashbordet som tilsvarer sin rolle etter innlogging. Videresendingen håndteres av `dashboard`-visningen i filen `competitions/views/dashboard/base.py`.

## Felles Struktur for Dashbord

Alle dashbord deler en felles struktur:

- **Topptekst**: Viser brukerens navn, rolle, og gir tilgang til innstillinger og utlogging
- **Sidefelt**: Navigasjon til de ulike seksjonene i dashbordet
- **Hovedinnhold**: Viser informasjon og funksjoner spesifikke for hver seksjon
- **Bunntekst**: Informasjon om applikasjonens versjon og nyttige lenker

## Tilpasning av Dashbord

Brukere kan tilpasse visse aspekter av sitt dashbord:
- Valg av widgets som vises på startsiden
- Rekkefølge for visning av informasjon
- Varslingsinnstillinger

## Felles Funksjoner

Alle dashbord tilbyr disse grunnleggende funksjonene:
- Oversikt med nøkkelstatistikk
- Varsler og meldinger
- Administrasjon av brukerprofil
- Kalender for kommende arrangementer
- Tilgang til dokumentasjon

## Flerspråklig Støtte

Alle dashbord støtter flerspråklighet og er tilgjengelige på følgende språk:
- Fransk (fr) - Standardspråk
- Engelsk (en)
- Spansk (es)
- Italiensk (it)
- Tysk (de)
- Norsk (no)
- Japansk (ja)
- Kinesisk (zh)
- Hindi (hi)
- Arabisk (ar)
- Swahili (sw)
- Amharisk (am)
- Zulu (zu)
- Yoruba (yo)
- Portugisisk (pt)
- Koreansk (ko)

## Teknisk Design

Dashbordene er implementert ved hjelp av:
- Django for backend
- HTML/CSS/JavaScript for frontend
- Bootstrap for responsiv layout
- AJAX-teknologi for dynamiske oppdateringer

## Detaljert Dokumentasjon

For mer informasjon om hvert dashbord, se lenkene ovenfor eller utforsk undermappene i denne katalogen.
