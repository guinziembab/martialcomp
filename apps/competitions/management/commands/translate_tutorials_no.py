"""
Management command to translate all 81 tutorials from French to Norwegian (Bokmal).
Updates title_no, steps_no, and tip_no fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_no
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Seksjon 1: Onboarding og Forste steg (7 veiledninger)
    # =========================================================================
    1: {
        'title_no': 'Onboarding og Forste steg',
        'tutorials': {
            1: {
                'title_no': 'Opprett kontoen din og velg din rolle',
                'steps_no': [
                    'Ga til MartialComp : Gaa til martialcomp.com og klikk paa \'Registrer deg gratis\'. Du kan ogsaa laste ned mobilappen fra Play Store eller App Store.',
                    'Fyll ut registreringsskjemaet : Skriv inn etternavn, fornavn, e-postadresse og passord. Du kan ogsaa registrere deg med Google, Facebook eller Apple ID for forenklet tilgang.',
                    'Velg din hovedrolle : Velg din rolle: Klubbansvarlig, Trener, Dommer/Kampdommar, Utover eller Forbundsansvarlig. Dette valget bestemmer dashbordet og funksjonene dine, men du kan legge til andre roller senere.',
                    'Bekreft e-posten din : Sjekk innboksen din og klikk paa bekreftelseslenken. Kontoen din er aktiv og du har tilgang til ditt personlige dashbord.',
                ],
                'tip_no': 'Du kan ha flere roller (f.eks. trener OG utover). Bytt mellom rollene dine fra sidemenyen naar som helst.',
            },
            2: {
                'title_no': 'Opprett klubben din',
                'steps_no': [
                    'Start opprettelsesveiviseren : Fra dashbordet ditt, klikk paa \'Opprett en klubb\'. Konfigurasjonsveiviseren med 4 trinn starter automatisk.',
                    'Generell informasjon : Skriv inn klubbnavn, forkortelse, fullstendig adresse og kontaktinformasjon (telefon, e-post, nettside). Legg til logoen din i PNG- eller JPG-format (anbefalt storrelse: 500x500px).',
                    'Velg disipliner : Velg en eller flere disipliner blant de 14+ tilgjengelige: Karate, Judo, BJJ, Taekwondo, MMA, Kung Fu, Aikido, Kendo, Muay Thai, Boksing, Capoeira osv.',
                    'Tilpass underdomenet ditt : Velg din unike adresse: din-klubb.martialcomp.com. Dette blir den offentlige adressen til klubben din, tilgjengelig for alle.',
                    'Konfigurer alternativer : Angi aapningstider, legg til en beskrivelse og bilder av dojoet ditt. Aktiver eller deaktiver nettbasert registrering av utovere.',
                ],
                'tip_no': 'Klubben din opprettes med Gratis-planen (opptil 10 medlemmer). Alle funksjoner er tilgjengelige fra starten. Oppgrader til Premium naar du overstiger 10 medlemmer.',
            },
            3: {
                'title_no': 'Opprett forbundet ditt',
                'steps_no': [
                    'Be om opprettelse : Velg rollen \'Forbundsansvarlig\' under registrering eller legg den til fra innstillingene. Fyll ut opprettelsesskjemaet med den offisielle informasjonen til forbundet ditt.',
                    'Offisiell informasjon : Skriv inn fullt navn, forkortelse, land, dekkede disipliner, offisielt registreringsnummer og kontaktinformasjon.',
                    'Konfigurer det offentlige nettstedet : Tilpass den offentlige siden din: banner, logo, farger, beskrivelse, bildegalleri og lenker til sosiale medier.',
                    'Definer strukturen : Konfigurer regionale ligaer hvis aktuelt, definer tilhoringskategorier for klubber og avgiftssatser.',
                ],
                'tip_no': 'Forbund har et utvidet administrasjonsomraade for aa overvake alle tilknyttede klubber, konkurranser og grader.',
            },
            4: {
                'title_no': 'Konfigurer trenerprofilen din',
                'steps_no': [
                    'Gaa til trenerprofilen : Fra sidemenyen, klikk paa \'Min trenerprofil\'. Hvis du ikke har trenerrollen ennaa, legg den til fra Innstillinger > Mine roller.',
                    'Skriv inn kvalifikasjonene dine : Legg til diplomene dine (BPJEPS, DEJEPS, CQP osv.), gradene dine i hver disiplin og antall aars erfaring.',
                    'Definer disiplinene dine : Velg disiplinene du underviser i og ditt spesialiseringsnivaa i hver (nybegynnere, viderekomne, konkurranse).',
                    'Angi tilgjengeligheten din : Oppgi dine ukentlige undervisningstider. Denne informasjonen vil vaere synlig for klubber som soker trenere.',
                ],
                'tip_no': 'En komplett trenerprofil med bilde og sertifiseringer oker synligheten din overfor klubber betraktelig.',
            },
            5: {
                'title_no': 'Konfigurer dommerprofilen din',
                'steps_no': [
                    'Aktiver dommerrollen : Fra Innstillinger > Mine roller, aktiver rollen \'Dommer / Kampdommar\'. Skriv inn dommerlisensen din hvis aktuelt.',
                    'Legg til kvalifikasjonene dine : Oppgi dommernivaet ditt (regionalt, nasjonalt, internasjonalt), disiplinene du er kvalifisert for og sertifiseringene dine.',
                    'Definer spesialitetene dine : Kata/teknikker, kamp, artistisk poenggivning... Hver spesialitet kvalifiserer deg for de tilsvarende konkurransene.',
                    'Oppgi tilgjengeligheten din : Angi dine geografiske omraader og perioder med tilgjengelighet for konkurranser.',
                ],
                'tip_no': 'Konkurranse-arrangorer kan soke deg opp og invitere deg direkte basert paa kvalifikasjonene og tilgjengeligheten din.',
            },
            6: {
                'title_no': 'Konfigurer utoverprofilen din',
                'steps_no': [
                    'Fyll ut personlig informasjon : Skriv inn fodselsdato, kjonn, vekt (for konkurransekategorier), hoyde og profilbilde.',
                    'Legg til din naavaerende grad : Oppgi hoveddisiplinen din, din naavaerende grad (belte), dato for oppnaaelse og utstedende organisasjon.',
                    'Skriv inn lisensen din : Legg til forbundslisensen din, utlopsdato og gyldig legeattest.',
                    'Nodkontakter : Legg til minst en nodkontakt (obligatorisk for konkurranser): navn, telefon, slektskap.',
                ],
                'tip_no': 'En komplett profil er nodvendig for aa melde seg paa konkurranser. Vekt og grad bestemmer automatisk kategorien din.',
            },
            7: {
                'title_no': 'Forstaa dashbordet og navigasjonen',
                'steps_no': [
                    'Dashbordet : Dashbordet ditt viser et personlig sammendrag: kommende hendelser, nylige meldinger, hurtigstatistikk og snarveier til dine vanligste handlinger.',
                    'Sidemenyen : Sidemenyen gir tilgang til alle seksjonene: Medlemmer, Konkurranser, Grader, Okonomi, Kalender, Innstillinger. Den tilpasser seg den aktive rollen din.',
                    'Bytte rolle : Hvis du har flere roller (f.eks. trener + utover), klikk paa avataren din overst til hoyre for aa bytte. Dashbordet og menyen tilpasser seg automatisk.',
                    'Varsler og meldinger : Bjelleikonet overst til hoyre viser varslene dine: paameldinger, resultater, meldinger. Konfigurer varselinnstillingene i innstillingene.',
                    'Globalt sok : Bruk sokefeltet for raskt aa finne en utover, klubb, konkurranse eller hendelse.',
                ],
                'tip_no': 'Tilpass dashbordet ved aa feste favorittwidgetene dine. Tastatursnarveien Ctrl+K aapner hurtigsok.',
            },
        },
    },

    # =========================================================================
    # Seksjon 2: Klubbadministrasjon (10 veiledninger)
    # =========================================================================
    2: {
        'title_no': 'Klubbadministrasjon',
        'tutorials': {
            1: {
                'title_no': 'Legge til utovere manuelt',
                'steps_no': [
                    'Aapne registreringsskjemaet : Fra Medlemmer > Legg til en utover, fyll ut skjemaet: etternavn, fornavn, fodselsdato, kjonn, e-post og telefon.',
                    'Tilleggsinformasjon : Legg til naavaerende grad, lisensnummer, identifikasjonsbilde (valgfritt) og legeattest.',
                    'Tilordne til en gruppe : Tilordne utoveren til en eller flere treningsgrupper (f.eks. Karate Voksne Videregaaende, Judo Barn Nybegynner).',
                    'Send invitasjonen : Kryss av for \'Send en invitasjons-e-post\' slik at utoveren kan opprette sin egen konto og faa tilgang til sin profil paa nett.',
                ],
                'tip_no': 'Utoveren vil motta en e-post med en lenke for aa fullstendige registreringen og laste ned mobilappen.',
            },
            2: {
                'title_no': 'Masseimport av utovere (CSV/Excel)',
                'steps_no': [
                    'Last ned malen : Fra Medlemmer > Importer, last ned CSV- eller Excel-malen. Filen inneholder obligatoriske kolonner: Etternavn, Fornavn, Fodselsdato, E-post, og valgfrie kolonner: Grad, Lisens, Telefon.',
                    'Fyll ut filen : Fyll ut filen med utovernes data. Folg formatene: datoer i DD/MM/AAAA, grader som tekst (f.eks. \'Gront belte\', \'2. Dan\').',
                    'Last opp og kartlegg kolonner : Importer filen. Kartleggingsgrensesnittet lar deg koble hver kolonne i filen din til feltene i MartialComp. Kontroller kartleggingen.',
                    'Valider og korriger : MartialComp oppdager feil (duplikater, ugyldige formater). Korriger rader med feil eller hopp over dem. Bekreft importen.',
                ],
                'tip_no': 'Du kan importere opptil 500 utovere i en enkelt operasjon. Importen oppdager automatisk duplikater via e-post eller etternavn + fornavn + fodselsdato.',
            },
            3: {
                'title_no': 'Administrere utovernes profiler',
                'steps_no': [
                    'Gaa til profilen : Fra medlemslisten, klikk paa navnet til en utover for aa aapne den fullstendige profilen.',
                    'Se detaljer : Profilen viser: personlig informasjon, gradhistorikk, gjennomforte konkurranser, oppmote og avgifter.',
                    'Redigere informasjonen : Klikk paa \'Rediger\' for aa oppdatere dataene. Endringer loggfores i historikken.',
                    'Hurtighandlinger : Fra profilen kan du: melde paa en konkurranse, tildele en grad, sende en melding, generere et sertifikat.',
                ],
                'tip_no': 'Bruk avanserte filtre (grad, alder, gyldig lisens, betalt avgift) for raskt aa finne en utover.',
            },
            4: {
                'title_no': 'Opprette en brukerkonto for en utover',
                'steps_no': [
                    'Gaa til utoverens profil : Aapne den aktuelle utoverens profil fra medlemslisten.',
                    'Koble til en konto : Klikk paa \'Opprett en brukerkonto\'. En invitasjons-e-post sendes til utoveren med en lenke for aa opprette passordet sitt.',
                    'Angi tillatelser : Velg hva utoveren kan gjore: se resultatene sine, melde seg paa konkurranser, se kalenderen, betale paa nett.',
                ],
                'tip_no': 'Mindreaarige utovere kan ha en konto koblet til en forelders konto gjennom Familiegruppe-funksjonen.',
            },
            5: {
                'title_no': 'Administrere roller og tillatelser i klubben',
                'steps_no': [
                    'Gaa til rolleadministrasjon : Fra Innstillinger > Roller og tillatelser, se tilgjengelige roller: Administrator, Sekretaer, Kasserer, Trener, Medlem.',
                    'Tildele en rolle : Velg et medlem og tildel en rolle. Hver rolle gir tilgang til spesifikke funksjoner.',
                    'Tilpasse tillatelser : For hver rolle, definer rettighetene: kun lesing, redigering, sletting, tilgang til okonomi, paameldingsadministrasjon.',
                    'Revidere tilganger : Se aktivitetsloggen for aa se hvem som gjorde hva og naar i klubbens administrasjon.',
                ],
                'tip_no': 'Administrator-rollen har alle rettigheter. Opprett en Sekretaer-rolle med tilgang til medlemmer og kalender, men ikke okonomi.',
            },
            6: {
                'title_no': 'Oppmoteregistrering / Innsjekking',
                'steps_no': [
                    'Opprette en okt : Fra Oppmote > Ny okt, velg treningsgruppen, datoen og tidspunktet for timen.',
                    'Registrere via liste : Vis listen over gruppens medlemmer og merk av de tilstedevaeerende. Registreringen gjores med ett trykk paa mobil.',
                    'Registrere via QR-kode : Vis QR-koden for okten. Utoverne skanner den med telefonen naar de ankommer dojoet.',
                    'Se statistikk : Se oppmoteprosenter per utover, gruppe og periode. Identifiser gjentatte fravaar.',
                ],
                'tip_no': 'Innsjekking via QR-kode er den raskeste metoden for store grupper. Koden fornyes for hver okt for aa forhindre juks.',
            },
            7: {
                'title_no': 'Administrere treningsprogrammer',
                'steps_no': [
                    'Opprette et program : Fra Programmer > Nytt, definer navnet, disiplinen, nivaet (nybegynner, mellomnivaa, videregaaende) og varigheten paa syklusen.',
                    'Planlegge oktene : Legg til ukentlige tidsluker: dag, starttid, sluttid, sal/tatami, ansvarlig trener.',
                    'Definere innholdet : For hver okt, legg til en plan: oppvarming, teknisk arbeid, sparring/randori, nedtrapping. Legg ved filer eller videoer.',
                    'Publisere og varsle : Publiser programmet. Utoverne i gruppen mottar et varsel med det fullstendige programmet.',
                ],
                'tip_no': 'Dupliser et eksisterende program for raskt aa opprette en ny syklus med variasjoner.',
            },
            8: {
                'title_no': 'Generere og bruke klubbens QR-koder',
                'steps_no': [
                    'Generere klubbens QR-kode : Fra Innstillinger > QR-koder, generer klubbens QR-kode. Den lar besokende gaa direkte til den offentlige siden din.',
                    'Spesielle QR-koder : Generer QR-koder for: nettregistrering, oktsinnsjekking, hendelsesside eller lenke til mobilappen.',
                    'Skrive ut og vise : Last ned QR-kodene i hoy opplosning for utskrift. Tilgjengelige formater: PNG, SVG, PDF (A4 eller visittkort).',
                    'Overvake statistikk : Se antall skanninger per QR-kode, per dag og per type. Identifiser de mest effektive QR-kodene.',
                ],
                'tip_no': 'Vis registrerings-QR-koden ved inngangen til dojoet. Hver skanning er en potensiell kunde!',
            },
            9: {
                'title_no': 'Soke om tilknytning til forbundet',
                'steps_no': [
                    'Finn forbundet ditt : Fra Klubb > Tilknytning, sok etter forbundet ditt ved navn, disiplin eller land.',
                    'Send soknaden : Fyll ut tilknytningsskjemaet: klubbinformasjon, registreringsnummer, stottedokumenter (vedtekter, forsikring osv.).',
                    'Folg med paa statusen : Soknaden din gaar gjennom stadier: Sendt > Under vurdering > Godkjent/Avvist. Du mottar varsler for hvert trinn.',
                    'Forny hver sesong : Tilknytningen gjelder per sesong. En automatisk paaminnelse sendes 30 dager for utlop.',
                ],
                'tip_no': 'Tilknytningen gir tilgang til forbundets offisielle konkurranser og sentralisert lisensadministrasjon.',
            },
            10: {
                'title_no': 'Administrere overganger av utovere',
                'steps_no': [
                    'Starte en overgang : Fra en utovers profil, klikk paa \'Be om overgang\'. Velg destinasjonsklubben og aarsaken til overgangen.',
                    'Valideringsprosess : Destinasjonsklubben mottar foresporselen og kan godta eller avslaa. Hvis et forbund er involvert, maa det ogsaa validere.',
                    'Overgang gjennomfort : Naar den er validert, overføres utoveren automatisk med sin grad og konkurransehistorikk.',
                    'Se historikken : Overgangshistorikken er synlig paa utoverens profil og i klubbens rapporter.',
                ],
                'tip_no': 'Noen forbund har overgangsperioder (overgangsvinduer). MartialComp folger automatisk disse reglene.',
            },
        },
    },

    # =========================================================================
    # Seksjon 3: Konkurranser - Opprettelse og konfigurasjon (6 veiledninger)
    # =========================================================================
    3: {
        'title_no': 'Konkurranser - Opprettelse og konfigurasjon',
        'tutorials': {
            1: {
                'title_no': 'Opprette en individuell konkurranse',
                'steps_no': [
                    'Starte opprettelsen : Fra Konkurranser > Opprett, velg typen \'Individuell\'. Skriv inn navn, disiplin(er), datoer og sted.',
                    'Definere formatet : Velg formatet: Kamp (kumite, randori, sparring), Teknisk (kata, poomsae, former) eller Blandet (begge).',
                    'Konfigurere kategoriene : Definer kategoriene etter kjonn, aldersgruppe, vekt og/eller grad. MartialComp tilbyr standard kategorimaler per disiplin.',
                    'Alternativer og publisering : Aktiver onskede alternativer: nettbasert paamelding, betaling, direktestrømming, offentlige resultater. Publiser konkurransen.',
                ],
                'tip_no': 'Bruk kategorimaler (WKF, IJF, ITF...) for aa spare tid. Du kan tilpasse dem etter opprettelsen.',
            },
            2: {
                'title_no': 'Opprette en lagkonkurranse (Synkro/Song Luyen)',
                'steps_no': [
                    'Velge lagmodus : Under opprettelsen, velg typen \'Lag\'. Definer minimum og maksimum antall medlemmer per lag.',
                    'Konfigurere lagformatet : Velg formatet: Synkronisering (lag-kata/poomsae), Song Luyen (forhaaandsbestemt kamp for to) eller Lagkamp (stafett).',
                    'Definere sammensetningen : Spesifiser rollene i laget: antall faste spillere, antall reserver, om blandede sammensetninger er tillatt eller ikke.',
                    'Lagpoengkriterier : For teknisk poenggivning, definer om dommerne vurderer laget samlet eller hvert medlem individuelt.',
                ],
                'tip_no': 'Synkroniseringsmodus tillater poenggivning med spesifikke synkroniseringskriterier (timing, oppstilling, felles uttrykk).',
            },
            3: {
                'title_no': 'Konfigurere konkurransekategorier',
                'steps_no': [
                    'Gaa til kategoriadministrasjon : Fra den opprettede konkurransen, gaa til fanen Kategorier. Klikk paa \'Legg til en kategori\'.',
                    'Definere kriteriene : For hver kategori, definer: kjonn (M/K/Blandet), aldersgruppe (f.eks. 12-14 aar), vektklasse (f.eks. -60kg), minimum/maksimum grad.',
                    'Navngi kategorien : Gi den et tydelig navn: \'Kadett Herre -52kg\' eller \'Kata Voksen Dame Videregaaende\'. MartialComp genererer automatiske navn om du foretrekker det.',
                    'Sortere kategoriene : Omorganiser kategoriene med dra-og-slipp for aa fastsette rekkefølgen paa konkurransedagen.',
                ],
                'tip_no': 'Importer kategoriene fra en tidligere konkurranse for aa spare tid. Bruk alternativet \'Smart duplisering\' for aa lage varianter.',
            },
            4: {
                'title_no': 'Duplisere en eksisterende konkurranse',
                'steps_no': [
                    'Finne kildekonkurransen : Fra Konkurranser > Historikk, finn konkurransen du vil duplisere.',
                    'Starte dupliseringen : Klikk paa de 3 prikkene > Dupliser. Velg hva som skal kopieres: kategorier, regelverk, konfigurasjon, priser.',
                    'Justere konfigurasjonen : Endre datoer, sted og nodvendige parametere. Kategoriene og regelverket kopieres identisk.',
                ],
                'tip_no': 'Ideelt for aarlige tilbakevendende konkurranser. Dupliser forrige aars utgave og oppdater bare datoene.',
            },
            5: {
                'title_no': 'Konfigurere synlighetsalternativer',
                'steps_no': [
                    'Gaa til synlighetsinnstillinger : Fra konkurransen, gaa til Innstillinger > Synlighet og deling.',
                    'Nettpaamelding : Aktiver/deaktiver offentlige paameldinger. Angi aapnings- og lukkingsdatoer for paameldinger.',
                    'Resultater og rangeringer : Velg om resultatene er offentlige i sanntid, publisert etter validering eller private (kun arrangor).',
                    'Direktestrømming : Aktiver strømmemodus og legg til YouTube/Twitch/Facebook Live-lenken for aa vise den paa den offentlige siden.',
                ],
                'tip_no': 'Sanntidsresultater tiltrekker seere til siden din og oker synligheten til klubben eller forbundet ditt.',
            },
            6: {
                'title_no': 'Konfigurere kampregler',
                'steps_no': [
                    'Velge et regelverk : Velg et forhaaandskonfigurert regelverk (WKF, IJF, ITF, IBJJF osv.) eller opprett et tilpasset.',
                    'Definere poenggivningen : Konfigurer handlinger og poeng: Yuko (1p), Waza-ari (2p), Ippon (3p) osv. Legg til straffer (Shido, Hansoku osv.).',
                    'Konfigurere rundene : Definer rundevarighet, antall runder, pauser og vinnervilkaar (poeng, Ippon, oppgivelse).',
                    'Spesialregler : Konfigurer spesifikke regler: Golden Score (ekstra tid), Hantei (dommeravgjorelse), tidlig avslutning ved poengforskjell.',
                ],
                'tip_no': 'Lagre dine tilpassede regelverk som maler for aa gjenbruke dem i fremtidige konkurranser.',
            },
        },
    },

    # =========================================================================
    # Seksjon 4: Paameldinger og lag (7 veiledninger)
    # =========================================================================
    4: {
        'title_no': 'Paameldinger og lag',
        'tutorials': {
            1: {
                'title_no': 'Melde paa utovere til en konkurranse',
                'steps_no': [
                    'Finne konkurransen : Fra Konkurranser > Aapne for paamelding, finn onsket konkurranse og klikk paa \'Meld paa\'.',
                    'Velge utoverne : Listen over medlemmene dine vises. Velg en eller flere utovere. MartialComp angir automatisk kvalifiserte kategorier for hver enkelt.',
                    'Bekrefte kategoriene : For hver utover, bekreft eller endre den foreslaaatte kategorien. Systemet kontrollerer at vekt, alder og grad stemmer.',
                    'Validere og betale : Bekreft paameldingene. Hvis konkurransen krever betaling, gaa videre til betaling av alle paameldinger.',
                ],
                'tip_no': 'Utovere med ufullstendig profil (manglende vekt, utlopt lisens) vil bli markert med et rodt varsel.',
            },
            2: {
                'title_no': 'Massepaamelding via skjema',
                'steps_no': [
                    'Gaa til massemodus : Fra paameldingsskjermen, klikk paa \'Massepaamelding\'. Velg maalkategorien.',
                    'Velge gruppen : Filtrer etter treningsgruppe, grad eller alder. Velg kvalifiserte utovere med ett klikk.',
                    'Kontrollere og justere : Kontrollskjermen viser hver utover med sin kategori. Korriger eventuelle feil.',
                    'Bekrefte partiet : Valider alle paameldinger i en enkelt operasjon. Et sammendrag sendes paa e-post.',
                ],
                'tip_no': 'Massepaamelding er ideelt for klubber som melder paa 10+ utovere til samme konkurranse.',
            },
            3: {
                'title_no': 'Opprette og administrere lag',
                'steps_no': [
                    'Opprette et lag : Fra konkurransen, klikk paa \'Meld paa et lag\'. Gi laget et navn og velg kategorien.',
                    'Legge til medlemmer : Legg til lagmedlemmer fra utoverlisten din. Overhold definerte minimums- og maksimumstall.',
                    'Angi faste spillere og reserver : Angi faste spillere og reserver med dra-og-slipp. Rekkefølgen kan ogsaa settes her.',
                    'Validere laget : Kontroller lagets samsvar (antall medlemmer, individuelle kategorier) og bekreft paameldingen.',
                ],
                'tip_no': 'I lagkonkurranser vises lagnavnet paa resultattavlene og i de offisielle resultatene.',
            },
            4: {
                'title_no': 'Endre kategori for et lag',
                'steps_no': [
                    'Gaa til laget : Fra paameldingene dine, finn laget som skal endres og klikk paa \'Rediger\'.',
                    'Endre kategorien : Velg den nye kategorien fra nedtrekksmenyen. Systemet kontrollerer at laget oppfyller kriteriene.',
                    'Bekrefte endringen : Valider. Hvis konkurransen har ulike paameldingsavgifter per kategori, justeres dette automatisk.',
                ],
                'tip_no': 'Kategoriendring er bare mulig saa lenge paameldingene er aapne.',
            },
            5: {
                'title_no': 'Soke om allianse (fusjon mellom klubber)',
                'steps_no': [
                    'Identifisere behovet : Har ikke klubben din nok medlemmer til aa danne et komplett lag? Alliansen gjor det mulig aa slaa sammen lag fra forskjellige klubber.',
                    'Opprette alliansesoknad : Fra det ufullstendige laget, klikk paa \'Foresla en allianse\'. Velg partnerklubb og plassene som skal fylles.',
                    'Sende forslaget : Partnerklubben mottar foresporselen med detaljer: konkurranse, kategori, tilgjengelige plasser, vilkaar.',
                    'Fullstendige alliansen : Naar den er akseptert, vises det sammenslaaatte laget med medlemmer fra begge klubber. Laget faar et navn som kombinerer begge klubber.',
                ],
                'tip_no': 'Alliansen er underlagt godkjenning fra konkurranse-arrangoren og, hvis aktuelt, forbundet.',
            },
            6: {
                'title_no': 'Godta/avslaa en alliansesoknad',
                'steps_no': [
                    'Motta varselet : Du mottar et varsel om alliansesoknad. Klikk for aa se detaljene.',
                    'Gjennomgaa forslaget : Kontroller: den sokende klubben, konkurransen, kategorien, plassene som skal fylles og de foreslaaatte vilkaarene.',
                    'Godta eller avslaa : Klikk paa \'Godta\' for aa validere alliansen og velge dine medlemmer, eller \'Avslaa\' med en forklarende melding.',
                ],
                'tip_no': 'Du kan foresla et motforslag ved aa endre vilkaarene for aksept.',
            },
            7: {
                'title_no': 'Administrere mottatte paameldinger (godkjenning)',
                'steps_no': [
                    'Gaa til paameldingspanelet : Fra konkurransen, gaa til fanen Paameldinger. Se paameldinger etter status: Ventende, Godkjent, Avvist.',
                    'Gjennomgaa og godkjenne : Klikk paa en paamelding for aa kontrollere utoverens informasjon. Godkjenn enkeltvis eller i parti.',
                    'Avvise med begrunnelse : Ved avvisning, velg en aarsak: feil kategori, ugyldig lisens, for sen paamelding osv.',
                    'Eksportere listen : Eksporter listen over gyldige pameldte i CSV eller PDF for veiing og administrasjon paa konkurransedagen.',
                ],
                'tip_no': 'Aktiver automatisk godkjenning hvis du ikke vil validere hver paamelding manuelt.',
            },
        },
    },

    # =========================================================================
    # Seksjon 5: Konkurransedag - Kamp (8 veiledninger)
    # =========================================================================
    5: {
        'title_no': 'Konkurransedag - Kamp',
        'tutorials': {
            1: {
                'title_no': 'Generere puljene automatisk',
                'steps_no': [
                    'Gaa til puljeadministrasjon : Fra konkurransen, gaa til Puljer > Generer automatisk. Velg kategoriene som skal behandles.',
                    'Konfigurere fordelingen : Definer: antall utovere per pulje, separering av medlemmer fra samme klubb, manuelle seedinger (valgfritt).',
                    'Generere og kontrollere : Klikk paa \'Generer\'. MartialComp fordeler utoverne og unngaar intern-klubb-oppgjor i forste runde.',
                    'Justere manuelt : Om nodvendig, flytt utovere mellom puljer med dra-og-slipp. Systemet kontrollerer konflikter i sanntid.',
                ],
                'tip_no': 'Fordelingsalgoritmen garanterer rettferdighet ved aa separere klubber og balansere ferdighetsnivaaer mellom puljene.',
            },
            2: {
                'title_no': 'Organisere og omorganisere puljer',
                'steps_no': [
                    'Piljeoversikt : Puljeskjermen viser alle kategorier med antall utovere, puljer og status (utkast, validert, paagaar).',
                    'Redigere en pulje : Klikk paa en pulje for aa se utoverne. Bruk dra-og-slipp for aa flytte en utover til en annen pulje.',
                    'Haandtere fravaar : Merk en utover som fravaerende eller trukket. Systemet beregner automatisk kampoppsettet og rangeringene paa nytt.',
                    'Validere puljene : Naar du er fornoyd, valider puljene. Denne handlingen genererer automatisk kamptabellen.',
                ],
                'tip_no': 'Valider puljene kategori for kategori for aa starte kampene i de forste kategoriene mens du ferdigstiller de andre.',
            },
            3: {
                'title_no': 'Planlegge kampprogrammet',
                'steps_no': [
                    'Definere kampomraadene : Fra Program > Omraader, definer antall tatamier/ringer tilgjengelig og navnene deres (Tatami 1, Ring A osv.).',
                    'Tilordne tidsluker : Dra kategoriene til omraader og tidsluker. MartialComp beregner automatisk estimert varighet.',
                    'Oppdage konflikter : Systemet oppdager konflikter: en utover meldt paa i 2 kategorier paa samme tid. Bruk varslene for aa justere.',
                    'Publisere programmet : Publiser programmet. Utovere, trenere og dommere mottar et varsel med sine deltakelsestider.',
                ],
                'tip_no': 'Planlegg 20% ekstra tid per kategori for aa haandtere uunngaaelige forsinkelser.',
            },
            4: {
                'title_no': 'Bruke kampgrensesnittet (live poenggivning)',
                'steps_no': [
                    'Koble til omraadet : Paa nettbrettet eller telefonen din, aapne MartialComp og velg ditt tildelte kampomraade. Skriv inn dommer-PIN-koden din.',
                    'Poenggivningsgrensesnittet : Skjermen viser: de 2 utoverne (rod/blaa), handlingsknapper (poeng, straffer), tidtakeren og naavaerende poengstilling.',
                    'Gi poeng : Trykk paa poengknappene: Yuko (+1), Waza-ari (+2), Ippon (+3) for rod eller blaa utover. Poengene oppdateres i sanntid.',
                    'Haandtere straffer : Trykk paa Straff for aa gi en advarsel (Shido) eller diskvalifikasjon (Hansoku). Straffene er kumulative.',
                    'Avslutte kampen : Tidtakeren stopper automatisk. Valider resultatet (seier paa poeng, Ippon, oppgivelse). Rangeringen oppdateres umiddelbart.',
                ],
                'tip_no': 'Grensesnittet er optimalisert for nettbrett i liggende modus. Knappene er bevisst store for rask og feilfri bruk.',
            },
            5: {
                'title_no': 'Kioskmodus for flere tatamier',
                'steps_no': [
                    'Aktivere kioskmodus : Fra Innstillinger > Kioskmodus, aktiver modusen og sett en PIN-kode for hvert kampomraade.',
                    'Konfigurere hvert nettbrett : Paa hvert nettbrett i omraadet, logg inn og velg det tilsvarende omraadet. Skriv inn PIN-koden for aa laase skjermen til dette omraadet.',
                    'Uavhengig haandtering : Hvert omraade fungerer autonomt: poenggivning, tidtaker, visning. Den sentrale resultattavlen oppdateres i sanntid.',
                    'Tilskuerskjerm : Koble til en ekstra skjerm i \'Tilskuer\'-modus for aa vise poengstillingen i stort format, synlig fra tribunen.',
                ],
                'tip_no': 'Kioskmodus forhindrer at dommere ved et uhell navigerer bort fra poenggivningsgrensesnittet.',
            },
            6: {
                'title_no': 'Folge rangeringene i sanntid',
                'steps_no': [
                    'Sanntidspanel : Oppfolgingsskjermen viser i sanntid: paagaaende kamper per omraade, puljerangeringer og fremgang mot sluttfaser.',
                    'Filtrere etter kategori : Velg en kategori for aa se detaljer: fullforte, paagaaende og ventende puljer med provisoriske rangeringer.',
                    'Automatiske varsler : Systemet varsler automatisk trenere naar deres utovere maa stille paa kampomraadet.',
                ],
                'tip_no': 'Vis panelet paa en stor skjerm i resepsjonsomraadet slik at alle deltakere kan folge fremgangen.',
            },
            7: {
                'title_no': 'Generere sluttfaser (semifinaler/finaler)',
                'steps_no': [
                    'Puljer fullfort : Naar alle puljene i en kategori er fullfort, beregner systemet kvalifiserte utovere etter de definerte reglene (1. og 2. i hver pulje osv.).',
                    'Generere tabellen : Klikk paa \'Generer sluttfaser\'. Utslagstabellen (kvartfinaler, semifinaler, finale, bronsefinale) genereres automatisk.',
                    'Haandtere repechage : Hvis reglene tilsier det, genereres repechage automatisk med taperne fra semifinalene.',
                    'Starte finalene : Kampene i sluttfasene vises i programmet. Poenggivningen fungerer paa samme maate som for puljene.',
                ],
                'tip_no': 'Utslagstabellen genereres automatisk og unngaar, naar mulig, oppgjor mellom utovere fra samme klubb.',
            },
            8: {
                'title_no': 'Administrere podiumseremonien',
                'steps_no': [
                    'Gaa til podiet : Fra den fullforte kategorien, klikk paa \'Podium\'. Den endelige rangeringen vises: Gull, Solv, Bronse (og eventuelt 2 bronse).',
                    'Progressiv visning : Bruk \'Seremoni\'-modusen for progressiv visning: 3. plass, deretter 2. plass, deretter 1. plass, med animasjoner og lydeffekter.',
                    'Projisere paa storskjerm : Koble presentasjonsmodusen til en projektor for en spektakulaer visning under medaljeseremonien.',
                    'Dele resultater : Podiumene publiseres automatisk paa konkurransesiden og kan deles paa sosiale medier.',
                ],
                'tip_no': 'Ta et bilde av podiet og legg det til i konkurransen for aa berike galleriet og sosiale medier.',
            },
        },
    },

    # =========================================================================
    # Seksjon 6: Teknisk poenggivning (6 veiledninger)
    # =========================================================================
    6: {
        'title_no': 'Teknisk poenggivning',
        'tutorials': {
            1: {
                'title_no': 'Konfigurere poenggivningskriterier',
                'steps_no': [
                    'Gaa til kriteriene : Fra konkurransen, gaa til Poenggivning > Kriterier. Velg en mal eller opprett dine egne kriterier.',
                    'Definere kriteriene : Legg til vurderingskriterier: Teknikk (posisjoner, overganger), Kraft (kime, dynamikk), Rytme (tempo, flyt), Uttrykk (zanshin, aand).',
                    'Tildele vektinger : Definer vektingen av hvert kriterium: f.eks. Teknikk 40%, Kraft 25%, Rytme 20%, Uttrykk 15%. Totalen maa vaere 100%.',
                    'Definere skalaen : Velg poengskalaen: 1-5, 1-10, 5.0-10.0 eller tilpasset. Definer intervallet (0.1, 0.5 eller 1).',
                ],
                'tip_no': 'WKF- og WTF-malene er forhaaandskonfigurert. Tilpass dem etter dine spesifikke behov.',
            },
            2: {
                'title_no': 'Tilordne dommere til kategorier',
                'steps_no': [
                    'Aapne tilordningspanelet : Fra Poenggivning > Dommere, se listen over registrerte dommere og kategoriene som skal dekkes.',
                    'Tilordne per kategori : Dra dommerne til kategoriene. Definer antall dommere per kategori (vanligvis 5 eller 7).',
                    'Noytraalitetskontroll : MartialComp kontrollerer automatisk interessekonflikter: en dommer kan ikke vurdere en utover fra sin egen klubb.',
                    'Haandtere rotasjoner : Planlegg dommerrotasjoner mellom kategorier for aa forebygge tretthet og opprettholde rettferdighet.',
                ],
                'tip_no': 'Systemet for skjevhetsdeteksjon analyserer poengforskjeller mellom dommere og varsler hvis en dommer systematisk gir for hoye eller lave poeng.',
            },
            3: {
                'title_no': 'Bruke det tekniske poenggivningsarket',
                'steps_no': [
                    'Logge inn som dommer : Paa nettbrettet ditt, logg inn med dommerkontoen din. Velg den tildelte kategorien.',
                    'Poenggivningsgrensesnitt : Skjermen viser den naavaerende utoveren, vurderingskriteriene og det numeriske tastaturet. Hvert kriterium har sin egen glider eller tastatur.',
                    'Vurdere tur for tur : For hver utover, skriv inn poengsummen din for hvert kriterium. Valider vurderingen din for du gaar videre til neste.',
                    'Lagre : Vurderingen din lagres umiddelbart. Du kan endre poengene dine saa lenge turen ikke er laast av arrangoren.',
                ],
                'tip_no': 'Det digitale grensesnittet er optimalisert for rask inntasting paa nettbrett. Ett trykk for hver poengsum.',
            },
            4: {
                'title_no': 'Teknisk lagpoenggivning (Synkro)',
                'steps_no': [
                    'Forstaa lagmodus : I Synkro-poenggivning vises tilleggskriterier: Synkronisering, Romlig oppstilling, Felles uttrykk.',
                    'Vurdere laget samlet : Hvis konfigurert slik, vurder laget samlet for hvert kriterium, inkludert synkronisering.',
                    'Vurdere individuelt + lag : Hvis konfigurert for blandet vurdering, vurder hvert medlem individuelt OG legg deretter til en lagpoengsum for synkronisering.',
                ],
                'tip_no': 'I Synkro-modus representerer synkroniseringskriteriet typisk 20-30% av totalpoengene.',
            },
            5: {
                'title_no': 'Laase og publisere poengene',
                'steps_no': [
                    'Kontrollere poengene : Fra arrangorpanelet, se poengene fra alle dommere for hver utover. Identifiser mistenkelige avvik.',
                    'Laase en runde : Klikk paa \'Laas\' for aa forhindre eventuelle endringer. Den endelige beregningen (fjerne hoyeste/laveste poengsum, gjennomsnitt) utfores.',
                    'Publisere resultatene : Publiser rangeringene. Detaljerte poeng per dommer kan skjules eller vises etter din konfigurasjon.',
                    'Testmodus / tilbakestilling : For konkurransen, bruk testmodus for aa kontrollere systemet. Tilbakestillingen sletter alle testpoeng.',
                ],
                'tip_no': 'Laasing runde for runde gjor det mulig aa publisere resultater runde for runde mens konkurransen fortsetter.',
            },
            6: {
                'title_no': 'Se provisoriske rangeringer',
                'steps_no': [
                    'Gaa til rangeringene : Fra fanen Rangeringer, se sanntidsrangeringer med poeng per kriterium og totalpoeng.',
                    'Sortere og filtrere : Sorter etter totalpoeng eller etter spesifikt kriterium. Filtrer etter pulje eller alle utovere.',
                    'Dommerstatistikk : Se statistikk: gjennomsnitt per dommer, standardavvik, skjevhetsdeteksjon. Et viktig verktoy for rettferdighet.',
                ],
                'tip_no': 'Den provisoriske rangeringen er kun synlig for arrangorer og dommere. Den publiseres til utoverne forst etter laasing.',
            },
        },
    },

    # =========================================================================
    # Seksjon 7: Resultater og merittliste (4 veiledninger)
    # =========================================================================
    7: {
        'title_no': 'Resultater og merittliste',
        'tutorials': {
            1: {
                'title_no': 'Se konkurranseresultatene',
                'steps_no': [
                    'Finne konkurransen : Fra Konkurranser-menyen eller den offentlige siden, velg onsket konkurranse.',
                    'Se resultatene : Resultatene er organisert etter kategori. For hver kategori: podium, fullstendig rangering og poengdetaljer.',
                    'Kampdetaljer : Klikk paa en kamp for aa se detaljene: poeng per runde, straffer, tidtaker og eventuelt kampvideo.',
                ],
                'tip_no': 'Offentlige resultater er tilgjengelige uten MartialComp-konto via konkurranselenken.',
            },
            2: {
                'title_no': 'Publisere og dele resultatene',
                'steps_no': [
                    'Validere resultatene : Fra arrangorpanelet, gjennomgaa resultatene for hver kategori. Klikk paa \'Valider og publiser\'.',
                    'Generere offentlig lenke : En permanent lenke til resultatsiden genereres. Kopier den for aa dele.',
                    'Dele paa sosiale medier : Bruk de innebygde deleknappene for aa publisere paa Facebook, Instagram, Twitter. Podiumene genererer automatisk et bilde.',
                    'Resultat-QR-kode : Generer en resultat-QR-kode for aa vise paa konkurransestedet for tilskuere.',
                ],
                'tip_no': 'Det automatiske podiebildet er formatert for Instagram Stories (9:16) og Facebook (16:9).',
            },
            3: {
                'title_no': 'Eksportere resultatene (CSV/PDF)',
                'steps_no': [
                    'Gaa til eksport : Fra Resultater > Eksporter, velg formatet: CSV (raaadata), PDF (formatert rapport) eller Excel.',
                    'Velge innholdet : Velg: Generell rangering, Kun podier, Detalj per kategori, Medaljefordeling per klubb eller Alt.',
                    'Tilpasse PDF-en : For PDF, velg malen: offisiell rapport (med forbundslogo), enkel rapport eller diplomer.',
                ],
                'tip_no': 'Medaljefordelingsrapporten per klubb er spesielt nyttig for forbund og sponsorer.',
            },
            4: {
                'title_no': 'Se din personlige merittliste',
                'steps_no': [
                    'Gaa til Min merittliste : Fra utoverprofilen din, klikk paa \'Merittliste\'. Konkurransehistorikken din vises.',
                    'Se statistikk : Se: antall konkurranser, medaljer (gull/solv/bronse), seiersprosent, utvikling over tid.',
                    'Dele merittlisten din : Generer en offentlig lenke til merittlisten din eller eksporter den i PDF for soknader eller sponsing.',
                ],
                'tip_no': 'Merittlisten din oppdateres automatisk etter hver konkurranse. Den er synlig paa din offentlige profil hvis du tillater det.',
            },
        },
    },

    # =========================================================================
    # Seksjon 8: Gradadministrasjon (5 veiledninger)
    # =========================================================================
    8: {
        'title_no': 'Gradadministrasjon',
        'tutorials': {
            1: {
                'title_no': 'Konfigurere gradsystemet',
                'steps_no': [
                    'Gaa til konfigurasjonen : Fra Innstillinger > Grader, velg disiplinen og definer gradsystemet ditt.',
                    'Opprette nivaane : Legg til nivaane i rekkefølge: Hvitt belte, Gult, Oransje, Gront, Blaatt, Brunt, Svart 1. Dan, 2. Dan osv.',
                    'Definere forutsetninger : For hver grad, definer: minimumstid i forrige grad, minimumsalder, minimumsantall timer, om eksamen kreves.',
                    'Tildele farger : Tildel beltefarger for visning i grensesnittet og profilene.',
                ],
                'tip_no': 'Standard gradsystemer (Judo, Karate, TKD, BJJ) er forhaaandskonfigurert. Du kan tilpasse dem eller opprette nye.',
            },
            2: {
                'title_no': 'Tildele en grad til en utover',
                'steps_no': [
                    'Gaa til profilen : Fra utoverens profil, klikk paa fanen Grader og deretter \'Tildel en ny grad\'.',
                    'Velge graden : Velg graden fra listen. Systemet kontrollerer automatisk forutsetningene (tid, alder, eksamener).',
                    'Skrive inn detaljer : Legg til tildelingsdato, sted, jury/eksaminator og merknader.',
                    'Massetildeling : Fra Grader > Massetildeling, velg flere utovere og tildel samme grad til alle.',
                ],
                'tip_no': 'En gratulasjons-e-post sendes automatisk til utoveren med den nye graden.',
            },
            3: {
                'title_no': 'Organisere en gradeksamen',
                'steps_no': [
                    'Opprette eksamen : Fra Grader > Eksamener, opprett en ny eksamen: dato, sted, disiplin, dekkede grader, jury.',
                    'Melde paa kandidater : Legg til kandidater manuelt eller tillat selvpaamelding. Systemet kontrollerer forutsetningene for hver enkelt.',
                    'Paa eksamensdagen : Bruk eksamensgrensesnittet for aa vurdere hver kandidat: paakrevde teknikker, kamp, teori.',
                    'Publisere resultatene : Valider bestaaatte og ikke bestaaatte. Gradene tildeles automatisk til kandidatene som bestod.',
                ],
                'tip_no': 'Gradeksamener kan kobles til en konkurranse (f.eks. gradforfremmelse under en turnering).',
            },
            4: {
                'title_no': 'Administrere historikk og gradprogresjon',
                'steps_no': [
                    'Se historikken : Profilen til hver utover viser fullstendig gradhistorikk: dato, sted, jury, merknader.',
                    'Visualisere progresjonen : Et diagram viser progresjonen over tid. Sammenlign med klubbens gjennomsnitt.',
                    'Tilbakekalle en grad : Ved feil, tilbakekall en grad med en begrunnelse. Historikken bevarer tilbakekallingsoppforingen.',
                ],
                'tip_no': 'Gradhistorikken er overforbar hvis utoveren bytter klubb.',
            },
            5: {
                'title_no': 'Generere gradsertifikater',
                'steps_no': [
                    'Gaa til sertifikatene : Fra Grader > Sertifikater, velg utoveren og graden det skal genereres sertifikat for.',
                    'Velge malen : Velg en sertifikatmal: offisiell (med forbundslogo), klubb eller tilpasset.',
                    'Tilpasse : Legg til signaturer, klubbstempel og spesielle omtaler. QR-koden for verifisering legges til automatisk.',
                    'Generere og distribuere : Generer PDF-en. Skriv ut eller send paa e-post. QR-koden lar hvem som helst verifisere sertifikatets ekthet.',
                ],
                'tip_no': 'Verifiserings-QR-koden lenker til en offentlig MartialComp-side som bekrefter gradens gyldighet.',
            },
        },
    },

    # =========================================================================
    # Seksjon 9: Forbundsadministrasjon (8 veiledninger)
    # =========================================================================
    9: {
        'title_no': 'Forbundsadministrasjon',
        'tutorials': {
            1: {
                'title_no': 'Administrere tilknyttede klubber',
                'steps_no': [
                    'Oversikt : Forbundets dashbord viser kartet over tilknyttede klubber, deres status (aktiv, ventende, utlopt) og statistikk.',
                    'Behandle soknader : Nye tilknytningssoknader vises under Klubber > Ventende. Gjennomgaa dokumentene og godkjenn eller avslaa.',
                    'Overvake fornyelser : Se tilknytninger som snart utloper. Send automatiske paaminnelser 30, 15 og 7 dager for.',
                ],
                'tip_no': 'Forbundets dashbord gir en sanntidsoversikt over det totale antallet lisensierte utovere i alle klubber.',
            },
            2: {
                'title_no': 'Administrere sesonger og avgifter',
                'steps_no': [
                    'Opprette en sesong : Fra Sesonger > Ny, definer start- og sluttdatoer og avgiftssatser etter type (klubb, individuell, junior, senior).',
                    'Konfigurere avgiftene : Definer belopene per kategori: klubbtilknytning (fast), individuell lisens (per utover), forsikring (valgfritt).',
                    'Overvake betalinger : Se mottatte, ventende og forfallne avgifter i sanntid. Send automatiske paaminnelser.',
                    'Lukke sesongen : Ved sesongslutt, lukk den for aa generere den okonomiske rapporten og forberede neste sesong.',
                ],
                'tip_no': 'Avgifter kan betales paa nett via Stripe eller ved bankoverføring. Oppfolgingen er automatisk i begge tilfeller.',
            },
            3: {
                'title_no': 'Overvake konkurranser',
                'steps_no': [
                    'Helhetsoversikt : Forbundskalenderen viser alle konkurranser fra tilknyttede klubber, med status og antall deltakere.',
                    'Godkjenne en konkurranse : Klubber sender inn konkurranser for godkjenning. Kontroller reglene, dommerne og valider.',
                    'Se resultatene : Faa tilgang til resultatene fra alle godkjente konkurranser. Nasjonale rangeringer oppdateres automatisk.',
                ],
                'tip_no': 'Forbundsgodkjente konkurranser fremheves i katalogen og den offentlige kalenderen.',
            },
            4: {
                'title_no': 'Administrere dommere og deres kvalifikasjoner',
                'steps_no': [
                    'Dommerdatabase : Se databasen over tilknyttede dommere med kvalifikasjoner, spesialiteter og aktivitetshistorikk.',
                    'Administrere nivaaer : Tildel kvalifikasjonsnivaaer: regionalt, nasjonalt, internasjonalt. Definer kriterier for forfremmelse.',
                    'Noytraalitetsoppfolging : MartialComp analyserer poengstatistikken til hver dommer og oppdager mulige skjevheter.',
                ],
                'tip_no': 'Dommere med en balansert poenghistorikk fremheves for viktige konkurranser.',
            },
            5: {
                'title_no': 'Administrere sertifiseringer',
                'steps_no': [
                    'Opprette en mal : Design sertifikatmalene dine med forbundslogo, juridiske merknader og dynamiske felt.',
                    'Utstede sertifikater : Generer sertifikater for: grader, dommerkvalifikasjoner, undervisningsdiplomer, diverse attester.',
                    'Offentlig verifisering : Hvert sertifikat har en unik QR-kode. Hvem som helst kan skanne den for aa verifisere ektheten paa martialcomp.com.',
                ],
                'tip_no': 'Digitale sertifikater er manipulasjonssikre takket vaere QR-koden for verifisering koblet til MartialComp.',
            },
            6: {
                'title_no': 'Tilpasse forbundets offentlige nettsted',
                'steps_no': [
                    'Gaa til nettstedbyggeren : Fra Innstillinger > Offentlig nettsted, aapne sideredigereren. Forbundet ditt har en URL: forbund.martialcomp.com.',
                    'Tilpasse utseendet : Velg farger, tema, banner og logo. Legg til en beskrivelse og lenker til sosiale medier.',
                    'Legge til innhold : Publiser nyheter, bildegallerier, videoer, konkurransekalender og nedlastbare dokumenter.',
                    'Administrere sidene : Opprett ekstra sider: Historie, Ledelse, Reglement, Kontakt.',
                ],
                'tip_no': 'Det offentlige nettstedet er optimalisert for SEO. Jo mer komplett det er, desto bedre rangeres det i Google.',
            },
            7: {
                'title_no': 'Se statistikk og rapporter',
                'steps_no': [
                    'Analysepanel : Panelet viser nøkkeltall: antall klubber, utovere, konkurranser, aktive lisenser, vekst.',
                    'Rapporter per klubb : Generer detaljerte rapporter per klubb: antall medlemmer, avgifter, konkurransedeltakelse, tildelte grader.',
                    'Rapporter per disiplin : Analyser fordelingen etter disiplin, alder, kjonn. Identifiser veksttrender.',
                    'Eksportere og dele : Eksporter rapportene i PDF, Excel eller CSV for generalforsamlinger og offisielle rapporter.',
                ],
                'tip_no': 'Rapportene oppdateres i sanntid. Planlegg automatiske maanedlige eller kvartalsvise utsendelser.',
            },
            8: {
                'title_no': 'Administrere opplaeringsprogrammer',
                'steps_no': [
                    'Opprette et program : Fra Opplaering > Nytt, definer programmet: tittel, disiplin, nivaa, varighet, forutsetninger.',
                    'Planlegge oktene : Legg til opplaeringsokter: datoer, steder, instruktorer, antall plasser.',
                    'Administrere paameldinger : Trenere og dommere melder seg paa paa nett. Valider paameldingene og send innkallelsene.',
                    'Oppfolging og sertifisering : Overvak oppmote paa oktene. Utsted sertifiseringer til deltakerne som fullforte programmet.',
                ],
                'tip_no': 'Fullforte opplaeringsprogrammer vises automatisk paa profilene til trenere og dommere.',
            },
        },
    },

    # =========================================================================
    # Seksjon 10: Okonomi (5 veiledninger)
    # =========================================================================
    10: {
        'title_no': 'Okonomi',
        'tutorials': {
            1: {
                'title_no': 'Overvake klubbens transaksjoner',
                'steps_no': [
                    'Oversikt : Det okonomiske dashbordet viser: saldo, maanedens inntekter, utgifter og trenddiagram.',
                    'Registrere en transaksjon : Legg til en inntekt eller utgift: belop, dato, kategori (avgifter, utstyr, leie), beskrivelse.',
                    'Automatisk kategorisering : MartialComp kategoriserer automatisk tilbakevendende transaksjoner. Tilpass kategoriene etter dine behov.',
                ],
                'tip_no': 'Koble til bankkontoen din for automatisk aa importere transaksjoner og forenkle avstemming.',
            },
            2: {
                'title_no': 'Opprette og sende fakturaer',
                'steps_no': [
                    'Opprette en faktura : Fra Okonomi > Fakturaer > Ny, velg mottakeren (utover, klubb, sponsor) og fakturalinjene.',
                    'Tilpasse : Legg til logoen din, juridiske merknader og betalingsvilkaar. Velg valuta og MVA-sats.',
                    'Sende : Send fakturaen paa e-post. Mottakeren faar en lenke til nettbetaling (Stripe) og fakturaen i PDF.',
                    'Overvake betalinger : Se betalte, ventende og forfallne fakturaer. Send automatiske paaminnelser.',
                ],
                'tip_no': 'Utoveravgifter genererer automatisk fakturaer hvis du aktiverer dette alternativet.',
            },
            3: {
                'title_no': 'Administrere nettbetalinger (Stripe)',
                'steps_no': [
                    'Koble til Stripe : Fra Innstillinger > Betalinger, klikk paa \'Koble til Stripe\'. Folg trinnene for aa koble til Stripe-kontoen din.',
                    'Konfigurere kassen : Angi priser for: avgifter, konkurransepaameldinger, butikk. Aktiver gjentakende betalinger om nodvendig.',
                    'Teste betalingen : Bruk Stripes testmodus for aa kontrollere at alt fungerer for du aktiverer ekte betalinger.',
                    'Overvake inntekter : Stripe-panelet i MartialComp viser mottatte betalinger, refusjoner og overforinger til bankkontoen din.',
                ],
                'tip_no': 'Stripe tar en provisjon paa 1,4% + 0,25 EUR per transaksjon i Europa. Midlene overføres innen 2-7 dager.',
            },
            4: {
                'title_no': 'Importere kontoutdrag',
                'steps_no': [
                    'Laste ned kontoutdraget : Fra banken din, eksporter kontoutdraget i CSV-, OFX- eller QIF-format.',
                    'Importere i MartialComp : Fra Okonomi > Importer, last opp filen. MartialComp oppdager formatet og kartlegger kolonnene.',
                    'Avstemme : Systemet kobler automatisk importerte transaksjoner med eksisterende fakturaer og avgifter.',
                    'Validere : Kontroller koblingene, korriger feil og valider. Transaksjoner uten kobling legges til som ventende.',
                ],
                'tip_no': 'Maanedlige bankimporter holder regnskapet oppdatert uten manuell inntasting.',
            },
            5: {
                'title_no': 'Administrere utoveravgifter',
                'steps_no': [
                    'Konfigurere prisene : Fra Okonomi > Avgifter, angi aarlige priser per kategori: barn, ungdom, voksen, familie.',
                    'Utstede betalingsoppfordringer : Ved sesongstart, generer betalingsoppfordringer for alle medlemmer. Hver mottar en e-post med en betalingslenke.',
                    'Overvake betalinger : Se betalte, ventende og forfallne avgifter. Statusen vises paa hver utovers profil.',
                    'Sende paaminnelser : Planlegg automatiske paaminnelser: 1 uke, 2 uker, 1 maaned etter forfallsdato.',
                ],
                'tip_no': 'Utovere med forfallne avgifter kan blokkeres fra paamelding til konkurranser.',
            },
        },
    },

    # =========================================================================
    # Seksjon 11: Hendelser og kalender (3 veiledninger)
    # =========================================================================
    11: {
        'title_no': 'Hendelser og kalender',
        'tutorials': {
            1: {
                'title_no': 'Opprette en hendelse (seminar, galla, forsamling)',
                'steps_no': [
                    'Opprette hendelsen : Fra Kalender > Ny hendelse, skriv inn: type (seminar, galla, forsamling, aapen dag), tittel, datoer, sted og beskrivelse.',
                    'Konfigurere paameldinger : Aktiver nettpaamelding. Angi antall plasser, pris (gratis eller betalt) og paameldingsfrist.',
                    'Publisere : Publiser hendelsen. Den vises i klubbens kalender og kan deles paa sosiale medier.',
                ],
                'tip_no': 'Seminarer med gjestemestere er utmerkede markedsforingsverktoy. Legg til bilde og biografi for aa tiltrekke flere.',
            },
            2: {
                'title_no': 'Administrere gjentakende hendelser',
                'steps_no': [
                    'Opprette gjentakelse : Under opprettelsen, kryss av for \'Gjentakende hendelse\'. Angi frekvensen: daglig, ukentlig, maanedlig.',
                    'Haandtere unntak : Avlys eller endre en enkelt forekomst uten aa paavirke de andre (f.eks. time avlyst paa grunn av helligdag).',
                    'Endre serien : Endre hele serien (f.eks. permanent endring av tidspunkt) eller bare en enkelt forekomst.',
                ],
                'tip_no': 'Ukentlige timer bor opprettes som gjentakende hendelser for aa automatisk vises i kalenderen.',
            },
            3: {
                'title_no': 'Overvake paameldinger og oppmote',
                'steps_no': [
                    'Se de pameldte : Fra hendelsen, se listen over pameldte med status: paameldt, bekreftet, avlyst.',
                    'Registrere oppmote : Paa dagen for hendelsen, registrer oppmote via liste eller QR-kode.',
                    'Eksportere : Eksporter deltakerlisten i CSV eller PDF for arkivene dine.',
                ],
                'tip_no': 'Deltakelsesprosenten paa hendelser er en viktig indikator paa medlemmenes engasjement.',
            },
        },
    },

    # =========================================================================
    # Seksjon 12: Familieadministrasjon (3 veiledninger)
    # =========================================================================
    12: {
        'title_no': 'Familieadministrasjon',
        'tutorials': {
            1: {
                'title_no': 'Opprette en familiegruppe',
                'steps_no': [
                    'Gaa til familiegrupper : Fra profilen din, gaa til Innstillinger > Familiegruppe > Opprett.',
                    'Legge til medlemmer : Legg til hvert familiemedlem: ektefelle, barn. Koble deres eksisterende MartialComp-kontoer eller opprett nye.',
                    'Angi den ansvarlige : Den ansvarlige for familiegruppen mottar alle varsler og administrerer betalinger for hele familien.',
                ],
                'tip_no': 'Noen klubber tilbyr familiepriser (rabatt fra og med 3. medlem). Familiegruppen aktiverer automatisk disse rabattene.',
            },
            2: {
                'title_no': 'Melde paa hele familien til en konkurranse',
                'steps_no': [
                    'Gruppepaamelding : Fra konkurransen, klikk paa \'Meld paa familien min\'. De kvalifiserte medlemmene av familiegruppen din vises.',
                    'Velge og bekrefte : Velg medlemmene som skal meldes paa. Kategoriene foreslaas automatisk for hver enkelt.',
                    'Enkelt betaling : Betal alle paameldinger i en enkelt transaksjon.',
                ],
                'tip_no': 'Gruppepaamelding sparer verdifull tid naar flere barn deltar i samme konkurranse.',
            },
            3: {
                'title_no': 'Familiens betalingssenter',
                'steps_no': [
                    'Oversikt : Familiesenteret viser alle avgifter, paameldinger og fakturaer for familien paa en enkelt skjerm.',
                    'Samlet betaling : Grupper flere ventende betalinger og betal i en enkelt transaksjon.',
                    'Historikk : Se familiens fullstendige betalingshistorikk med nedlastbare kvitteringer.',
                ],
                'tip_no': 'Aktiver automatisk avtalegiro for aldri aa glemme en avgift.',
            },
        },
    },

    # =========================================================================
    # Seksjon 13: Oppgavehaandtering (Kanban) (2 veiledninger)
    # =========================================================================
    13: {
        'title_no': 'Oppgavehaandtering (Kanban)',
        'tutorials': {
            1: {
                'title_no': 'Bruke Kanban-tavlen',
                'steps_no': [
                    'Opprette en tavle : Fra Verktoy > Kanban, opprett en ny tavle: navn, beskrivelse og inviterte medlemmer.',
                    'Legge til kolonner : Opprett kolonnene i arbeidsflyten din: Aa gjore, Paagaar, Venter, Ferdig. Tilpass navn og farger.',
                    'Opprette oppgaver : Legg til oppgaver med: tittel, beskrivelse, frist, ansvarlig, prioritet (hoy/middels/lav) og etiketter.',
                    'Administrere med dra-og-slipp : Flytt oppgaver mellom kolonner ved aa dra dem. Bevegelseshistorikken bevares.',
                ],
                'tip_no': 'Opprett en dedikert tavle for hver konkurranse som skal arrangeres. Standardoppgaver (bestille lokale, bestille medaljer osv.) kan importeres fra en mal.',
            },
            2: {
                'title_no': 'Administrere organisatoriske oppgaver',
                'steps_no': [
                    'Konkurransemal : Bruk malen \'Konkurranseorganisering\' som inneholder standardoppgaver: logistikk, kommunikasjon, dommere, medaljer osv.',
                    'Tilordne til medlemmer : Tilordne hver oppgave til et medlem av organisasjonskomiteen. Angi frister.',
                    'Overvake fremdriften : Den totale fremgangsprosenten vises overst paa tavlen. Forfallne oppgaver fremheves i rodt.',
                ],
                'tip_no': 'Kanban-tavlen er tilgjengelig fra mobilappen for aa oppdatere oppgaver paa farten.',
            },
        },
    },

    # =========================================================================
    # Seksjon 14: Nettbutikk (2 veiledninger)
    # =========================================================================
    14: {
        'title_no': 'Nettbutikk',
        'tutorials': {
            1: {
                'title_no': 'Konfigurere klubbens butikk',
                'steps_no': [
                    'Aktivere butikken : Fra Innstillinger > Butikk, aktiver e-handelsfunksjonen. Koble til Stripe-kontoen din hvis du ikke allerede har gjort det.',
                    'Legge til produkter : Opprett produktene dine: navn, beskrivelse, bilder, pris, storrelser/varianter tilgjengelig, lager.',
                    'Organisere etter kategorier : Klassifiser produktene dine: Uniformer (kimono, dobok, hansker), Utstyr (beskyttelse, bager), Tilbehor (belter, merker), Merchandise.',
                    'Publisere butikken : Butikken din er tilgjengelig fra klubbens offentlige side. Del lenken eller QR-koden.',
                ],
                'tip_no': 'Tilby pakker (kimono + belte + bag) med rabatt for aa oke gjennomsnittlig bestillingsverdi.',
            },
            2: {
                'title_no': 'Legge inn en bestilling',
                'steps_no': [
                    'Bla i butikken : Fra klubbens side, gaa til butikken. Bla gjennom produktene etter kategori.',
                    'Legge i handlekurven : Velg storrelse/variant og legg i handlekurven. Handlekurven bevares mellom okter.',
                    'Bestille og betale : Bekreft handlekurven, velg leveringsmetode (henting i dojoet eller postforsendelse) og betal paa nett.',
                    'Folge bestillingen : Motta varsler for hvert trinn: bestilling bekreftet, under klargjoring, klar for henting / sendt.',
                ],
                'tip_no': 'Modusen \'Henting i dojoet\' unngaar fraktkostnader. Treneren vil levere bestillingen din paa neste time.',
            },
        },
    },

    # =========================================================================
    # Seksjon 15: Avanserte funksjoner (5 veiledninger)
    # =========================================================================
    15: {
        'title_no': 'Avanserte funksjoner',
        'tutorials': {
            1: {
                'title_no': 'Konfigurere konkurranse-strømming',
                'steps_no': [
                    'Forberede strømmingen : Opprett en direktesending paa YouTube, Twitch eller Facebook. Kopier strømme-URL-en og strøkkenøkkelen.',
                    'Konfigurere i MartialComp : Fra konkurransen, gaa til Innstillinger > Strømming. Lim inn URL-en og aktiver visningen paa den offentlige siden.',
                    'Poeng-overlay : Aktiver MartialComp-overlayet som viser live poengstilling i videostrømmen. Tilpass posisjon og stil.',
                    'Starte og teste : Start strømmingen og kontroller at overlayet fungerer. Seerne vil se live poengstilling i strømmen.',
                ],
                'tip_no': 'Strømming med MartialComps poeng-overlay gir et profesjonelt utseende selv for smaa konkurranser.',
            },
            2: {
                'title_no': 'Bruke mobilappen',
                'steps_no': [
                    'Laste ned appen : Sok etter \'MartialComp\' i Play Store (Android) eller App Store (iOS). Installer og aapne.',
                    'Logge inn : Logg inn med din eksisterende MartialComp-konto. Du kan ogsaa bruke Google-, Facebook- eller Apple-innlogging.',
                    'Utforske mobilgrensesnittet : Appen tilbyr: profil, resultater, kalender, push-varsler, personlig QR-kode og konkurransepaamelding.',
                    'Offline-modus : Viktige data (profil, grad, lisens) er tilgjengelige uten tilkobling. Automatisk synkronisering ved ny tilkobling.',
                ],
                'tip_no': 'Aktiver push-varsler for aa motta sanntidsvarsler om resultater under konkurranser.',
            },
            3: {
                'title_no': 'Bytte rolle i appen',
                'steps_no': [
                    'Gaa til rollevelgeren : Trykk paa avataren din overst paa skjermen eller sveip fra venstre for aa aapne sidemenyen.',
                    'Velge en rolle : Listen over rollene dine vises: Trener, Utover, Dommer, Klubbansvarlig. Trykk paa onsket rolle.',
                    'Tilpasset grensesnitt : Dashbordet og menyen oppdateres umiddelbart for aa gjenspeile den valgte rollen.',
                ],
                'tip_no': 'Du kan vaere trener i en klubb og utover i en annen. Hver rolle er koblet til sin organisasjon.',
            },
            4: {
                'title_no': 'Avansert import/eksport av data',
                'steps_no': [
                    'Stottede formater : MartialComp stotter import og eksport i CSV, Excel (XLSX), JSON og PDF. Hver modul har sine egne alternativer.',
                    'Import med kartlegging : Kartleggingsgrensesnittet lar deg koble enhver filstruktur til feltene i MartialComp.',
                    'Tilpasset eksport : Velg feltene som skal eksporteres, filtrene og formatet. Planlegg automatiske gjentakende eksporter.',
                    'Masseoperasjoner : Masseoperasjoner tillater masseendring av: grad, gruppe, paameldingsstatus osv.',
                ],
                'tip_no': 'JSON-eksporten er ideell for integrasjoner med tredjepartssystemer (nettsted, ekstern applikasjon, CRM).',
            },
            5: {
                'title_no': 'Administrere ad hoc-dommere (frivillige)',
                'steps_no': [
                    'Opprette en midlertidig dommer : Paa konkurransedagen, fra Dommere > Legg til frivillig, opprett en midlertidig profil: navn, klubb og spesialitet.',
                    'Tildele en PIN-kode : En unik PIN-kode genereres automatisk. Den frivillige bruker denne PIN-koden for aa faa tilgang til poenggivningsgrensesnittet.',
                    'Tilordne til kategorier : Tilordne den frivillige dommeren til kategorier som en vanlig dommer. Vedkommende kan begynne aa vurdere umiddelbart.',
                    'Etter konkurransen : Den midlertidige profilen arkiveres etter konkurransen. Poengene bevares i historikken.',
                ],
                'tip_no': 'Ad hoc-dommere er viktige for smaa konkurranser der antallet offisielle dommere er begrenset.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to Norwegian (hardcoded translations)'

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

            section.title_no = sec_data['title_no']
            if not dry_run:
                section.save(update_fields=['title_no'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_no"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_no = tut_data['title_no']
                tutorial.steps_no = json.dumps(tut_data['steps_no'], ensure_ascii=False)
                tutorial.tip_no = tut_data.get('tip_no', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_no', 'steps_no', 'tip_no'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_no"]}')

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
