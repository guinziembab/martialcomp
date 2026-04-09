# Uchambuzi wa Kutokupendelea kwa Majaji

## Lengo

Moduli ya uchambuzi wa kutokupendelea inaruhusu kutathmini kwa usawa hali ya kutoegemea upande wowote ya kila jaji wakati wa mashindano. Inagundua kiotomatiki upendeleo unaowezekana kwa kulinganisha alama zilizotolewa kulingana na vigezo kadhaa vya kitakwimu.

Moduli hii ni zana ya **mafunzo na uboreshaji endelevu** kwa majaji, si zana ya kinidhamu. Inaruhusu kila jaji kutambua mwelekeo wao usio wa makusudi ili kuboresha.

---

## Alama ya Kutokupendelea (0-100)

Kila jaji hupokea **alama ya jumla ya kutokupendelea** iliyokokotolewa kati ya pointi 100. Alama ikiwa juu zaidi, ndivyo jaji anavyochukuliwa kuwa na usawa zaidi.

Alama inakokotolewa kwa kutoa adhabu kutoka kwa alama kamili ya 100, kulingana na vigezo 4 vilivyopimwa:

| Kigezo | Uzito | Adhabu ya Juu |
|--------|-------|---------------|
| Upendeleo wa klabu | 30% | -30 pointi |
| Upendeleo wa utaifa | 25% | -25 pointi |
| Upendeleo wa nafasi | 20% | -20 pointi |
| Ulinganifu na wenzake | 25% | -25 pointi |

### Viwango vya Hatari

| Alama | Kiwango | Maana |
|-------|---------|-------|
| **80-100** | Hatari ndogo (kijani) | Jaji anatoa alama kwa uthabiti na usawa |
| **60-79** | Hatari wastani (machungwa) | Mwelekeo umegundulika, unahitaji ufuatiliaji |
| **0-59** | Hatari kubwa (nyekundu) | Upendeleo mkubwa umegundulika, mafunzo yanapendekezwa |

---

## Kigezo cha 1: Upendeleo wa Klabu

### Kanuni

Kigezo hiki kinalinganisha wastani wa alama ambazo jaji anatoa kwa wanafunzi kutoka **klabu yake mwenyewe** dhidi ya wanafunzi kutoka **klabu nyingine**.

### Ukokotoaji
```
Tofauti = Wastani(alama za wanafunzi wa klabu moja) - Wastani(alama za wanafunzi wengine)
```

### Vizingiti vya Ugunduzaji

| Tofauti (thamani kamili) | Ukali | Tafsiri |
|--------------------------|-------|---------|
| < pointi 0.3 | Sawa | Hakuna upendeleo uliogunduliwa |
| Pointi 0.3 hadi 0.5 | Ndogo | Upendeleo kidogo au ukali kidogo |
| Pointi 0.5 hadi 0.8 | Wastani | Mwelekeo mkubwa wa kufuatilia |
| > pointi 0.8 | Kubwa | Upendeleo dhahiri, hatua ya kurekebisha inapendekezwa |

### Jinsi ya Kutafsiri
- **Thamani chanya** (+): jaji ana mwelekeo wa kutoa alama nzuri zaidi kwa wanafunzi wa klabu yake
- **Thamani hasi** (-): jaji ana mwelekeo wa kuwa mkali zaidi na wanafunzi wa klabu yake (fidia kupita kiasi)
- Hali zote mbili ni upendeleo unaohitaji kurekebishwa

### Adhabu kwa Alama ya Jumla

| Ukali | Adhabu |
|-------|--------|
| Sawa | Pointi 0 |
| Ndogo | -10 pointi |
| Wastani | -20 pointi |
| Kubwa | -30 pointi |

---

## Kigezo cha 2: Upendeleo wa Utaifa

### Kanuni

Kigezo hiki kinalinganisha wastani wa alama zilizotolewa kwa wanafunzi wa **utaifa sawa** na jaji dhidi ya wanafunzi wa **mataifa mengine**.

### Ukokotoaji
```
Tofauti = Wastani(alama za utaifa sawa) - Wastani(alama za mataifa mengine)
```

### Vizingiti vya Ugunduzaji

| Tofauti (thamani kamili) | Ukali | Tafsiri |
|--------------------------|-------|---------|
| < pointi 0.2 | Sawa | Hakuna upendeleo uliogunduliwa |
| Pointi 0.2 hadi 0.4 | Ndogo | Upendeleo kidogo au ukali kidogo |
| Pointi 0.4 hadi 0.6 | Wastani | Mwelekeo mkubwa |
| > pointi 0.6 | Kubwa | Upendeleo dhahiri |

### Jinsi ya Kutafsiri
- **Vizingiti vikali zaidi** kuliko upendeleo wa klabu, kwani utaifa haupaswi kuathiri utoaji wa alama za kitaalamu
- **Thamani chanya**: upendeleo kuelekea utaifa wake
- **Thamani hasi**: ukali kupita kiasi kuelekea utaifa wake

### Adhabu kwa Alama ya Jumla

| Ukali | Adhabu |
|-------|--------|
| Sawa | Pointi 0 |
| Ndogo | -8 pointi |
| Wastani | -16 pointi |
| Kubwa | -25 pointi |

---

## Kigezo cha 3: Upendeleo wa Nafasi

### Kanuni

Kigezo hiki kinalinganisha **wastani wa jumla wa alama** za jaji na **wastani wa majaji wote** katika mashindano. Kinagundua majaji ambao ni wakarimu kupita kiasi au wakali kupita kiasi kwa utaratibu.

### Ukokotoaji
```
Tofauti = Wastani(alama zote za jaji) - Wastani(alama zote za majaji wote)
```

### Vizingiti vya Ugunduzaji

| Tofauti (thamani kamili) | Ukali | Tafsiri |
|--------------------------|-------|---------|
| < pointi 0.2 | Sawa | Katika wastani, utoaji wa alama ulioratibiwa vizuri |
| Pointi 0.2 hadi 0.4 | Ndogo | Mkarimu kidogo au mkali kidogo |
| Pointi 0.4 hadi 0.6 | Wastani | Mkarimu au mkali kwa kiwango cha kuonekana |
| > pointi 0.6 | Kubwa | Mkarimu sana au mkali sana |

### Jinsi ya Kutafsiri
- **Thamani chanya** (+): jaji kwa utaratibu anatoa alama juu ya wastani (mkarimu)
- **Thamani hasi** (-): jaji kwa utaratibu anatoa alama chini ya wastani (mkali)
- Jaji mzuri yuko ndani ya kiwango cha usawa (tofauti < pointi 0.2)

### Adhabu kwa Alama ya Jumla

| Ukali | Adhabu |
|-------|--------|
| Sawa | Pointi 0 |
| Ndogo | -5 pointi |
| Wastani | -12 pointi |
| Kubwa | -20 pointi |

---

## Kigezo cha 4: Ulinganifu na Wenzake

### Kanuni

Kigezo hiki kinapima jinsi alama za jaji **zinavyolingana na zile za majaji wengine** kwa maonyesho yale yale. Jaji ambaye alama zake zinatofautiana mara kwa mara na za wenzake anaweza kuwa na tatizo la uratibu au upendeleo.

### Ukokotoaji
Kwa kila onyesho lililopimwa na jaji:
```
Wastani_wa_wengine = Wastani(alama za majaji wengine kwa onyesho hili)
Kupotoka = |Alama ya jaji - Wastani_wa_wengine|
Ulinganifu_binafsi = max(0, 100 - (Kupotoka x 20))
```

**Alama ya ulinganifu wa jumla** ni wastani wa ulinganifu wote binafsi.

### Tafsiri

| Ulinganifu | Maana |
|------------|-------|
| **90-100%** | Ulinganifu bora, utoaji wa alama uliolingana sana |
| **75-89%** | Ulinganifu mzuri |
| **60-74%** | Ulinganifu unaokubalika lakini unahitaji uboreshaji |
| **< 60%** | Ulinganifu mdogo, **tahadhari inatokezwa** |

### Athari kwa Alama ya Jumla
Ulinganifu unaathiri alama ya kutokupendelea kupitia bonasi/adhabu:
```
Marekebisho = (Ulinganifu - 50) / 2
```
- Ulinganifu wa 100%: bonasi ya pointi +25
- Ulinganifu wa 50%: hakuna bonasi wala adhabu
- Ulinganifu wa 0%: adhabu ya pointi -25

### Masharti
- Kiwango cha chini cha **maonyesho 3** yaliyopimwa kinahitajika ili ukokotoaji uwe wa maana
- Ni alama zinazotumika (zisizo za mazoezi) pekee zinazozingatiwa

---

## Mfumo wa Tahadhari

Tahadhari zinatolewa kiotomatiki katika hali zifuatazo:

| Hali | Tahadhari |
|------|-----------|
| Upendeleo wa klabu wa wastani au mkubwa | "Upendeleo wa klabu umegundulika" na thamani ya kupotoka |
| Upendeleo wa utaifa wa wastani au mkubwa | "Upendeleo wa utaifa umegundulika" na thamani ya kupotoka |
| Nafasi ya juu pekee | "Nafasi kali" na kupotoka kutoka wastani |
| Ulinganifu < 60% | "Ulinganifu mdogo na majaji wengine" |

Tahadhari zinaonekana kwenye wasifu wa kina wa kila jaji katika kiolesura cha uchambuzi.

---

## Jukwaa la Majaji Wasio na Upendeleo Zaidi

Mwishoni mwa uchambuzi, **jukwaa** linaonyesha majaji 3 waliopata alama bora zaidi za kutokupendelea:

- **Nafasi ya 1 (Dhahabu)**: Alama ya juu zaidi ya kutokupendelea
- **Nafasi ya 2 (Fedha)**: Alama ya pili bora
- **Nafasi ya 3 (Shaba)**: Alama ya tatu bora

Mpangilio huu unathawabu usawa na unahimiza majaji wote kuboresha.

---

## Mapendekezo kwa Majaji

### Jinsi ya Kuboresha Alama Yako ya Kutokupendelea

1. **Upendeleo wa klabu**: Kuwa makini hasa unapotoa alama kwa mwanafunzi kutoka klabu yako. Tumia vigezo sawa vya kitaalamu kama kwa wengine.

2. **Upendeleo wa utaifa**: Zingatia mbinu na utekelezaji pekee. Utaifa wa mwanafunzi haupaswi kuathiri tathmini yako.

3. **Nafasi**: Ratibisha alama zako kwa kulingana na vigezo vilivyoainishwa. Si mkarimu sana wala mkali sana. Ukiwa na wasiwasi, rejea kipimo rasmi cha utoaji alama.

4. **Ulinganifu**: Ikiwa alama zako mara nyingi zinatofautiana na za wenzako, inaweza kuashiria kutoelewa vigezo. Shiriki katika vikao vya uratibu.

### Mazoea Bora

- Pima kila onyesho kwa kujitegemea, bila kuangalia alama za majaji wengine
- Tumia anuwai kamili ya kipimo cha utoaji alama
- Usibadilishe alama zako baada ya kuona za wengine
- Chukua muda kutathmini kila kigezo kando
- Inapokuwa na uchovu, pumzika ili kudumisha umakini wako

---

## Ufikiaji na Usiri

- Uchambuzi wa kutokupendelea unapatikana kwa **waandaaji wa mashindano** na **wasimamizi wa shirikisho**
- Kila jaji anaweza kuona **matokeo yake mwenyewe**
- Data inakokotolewa kwa **wakati halisi** kutoka kwa alama zilizopo (hakuna data ya kutokupendelea inayohifadhiwa kwa kudumu)
- Uchambuzi unahitaji idadi ya kutosha ya alama ili kuwa wa kuaminika (kiwango cha chini cha maonyesho 3 kwa ulinganifu)
