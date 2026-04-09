# Ukuhlaziya Ukungachemi Kwabammeli

## Injongo

Imoduli yokuhlaziya ukungachemi ivumela ukuhlola ngokuhluzekile ukungachemi kommeli ngamunye phakathi nomqhudelwano. Ibona ngokuzenzakalelayo ukuchema okungenzeka ngokuqhathanisa amaphuzu anikeziwe ngokwezindinganiso eziningana zezibalo.

Le moduli iyithuluzi **lokuqeqesha nokuthuthuka okuqhubekayo** kwabammeli, hhayi ithuluzi lokujezisa. Ivumela ummeli ngamunye ukuba aqaphele imikhuba yakhe engaqondakali ukuze athuthuke.

---

## Amaphuzu Okungachemi (0-100)

Ummeli ngamunye uthola **amaphuzu onke okungachemi** abalwe ku-100. Uma amaphuzu ephakeme, ummeli uthathwa njengongachemi.

Amaphuzu abalwa ngokususa izijeziso kumaphuzu aphelele angu-100, ngokwezindinganiso ezine-4 ezilinganisiwe:

| Indinganiso | Isisindo | Isijeziso esiphezulu |
|-------------|----------|---------------------|
| Ukuchema kwekilabhu | 30% | -30 amaphuzu |
| Ukuchema kobuzwe | 25% | -25 amaphuzu |
| Ukuchema kokubekwa | 20% | -20 amaphuzu |
| Ukuhambisana nabalingani | 25% | -25 amaphuzu |

### Amazinga Engozi

| Amaphuzu | Izinga | Incazelo |
|----------|--------|----------|
| **80-100** | Ingozi ephansi (oluhlaza) | Ummeli uhlola ngokuhambisana nangokungachemi |
| **60-79** | Ingozi emaphakathi (okunsundu) | Imikhuba ihlonziwe, kufanele iqashwe |
| **0-59** | Ingozi ephezulu (okubomvu) | Ukuchema okubalulekile kuhlonziwe, ukuqeqeshwa kunconywa |

---

## Indinganiso 1: Ukuchema Kwekilabhu

### Umgomo
Le ndinganiso iqhathanisa isilinganiso samaphuzu ummeli awanikeza abahlanganyeli **bekilabhu yakhe** nabahlanganyeli **bezinye izikhungo**.

### Ukubalwa
```
Umehluko = Isilinganiso(amaphuzu kubahlanganyeli bekilabhu efanayo) - Isilinganiso(amaphuzu kwabanye abahlanganyeli)
```

### Imikhawulo Yokuthola

| Umehluko (inani eliphelele) | Ubunzima | Incazelo |
|---------------------------|----------|----------|
| < 0.3 amaphuzu | Okungachemi | Akukho ukuchema okuhlonziwe |
| 0.3 kuya ku-0.5 amaphuzu | Okuncane | Ukuthanda kancane noma ukungathandi |
| 0.5 kuya ku-0.8 amaphuzu | Okumaphakathi | Umkhuba obalulekile okufanele uqashwe |
| > 0.8 amaphuzu | Okuphezulu | Ukuchema okubonakalayo, izinyathelo zokulungisa zinconywa |

### Indlela Yokuchaza
- **Inani elinhle** (+): ummeli uvame ukunikeza amaphuzu amahle kubahlanganyeli bekilabhu yakhe
- **Inani elibi** (-): ummeli uvame ukuba nzima kubahlanganyeli bekilabhu yakhe (ukuphakamisa ngokweqile)
- Zombili izimo zingukuchema okufanele kulungiswe

### Isijeziso kumaphuzu onke

| Ubunzima | Isijeziso |
|----------|-----------|
| Okungachemi | 0 amaphuzu |
| Okuncane | -10 amaphuzu |
| Okumaphakathi | -20 amaphuzu |
| Okuphezulu | -30 amaphuzu |

---

## Indinganiso 2: Ukuchema Kobuzwe

### Umgomo
Le ndinganiso iqhathanisa isilinganiso samaphuzu anikezwe abahlanganyeli **bobuzwe obufanayo** nommeli nabahlanganyeli **bobuzwe obunye**.

### Ukubalwa
```
Umehluko = Isilinganiso(amaphuzu kubuzwe obufanayo) - Isilinganiso(amaphuzu kobunye ubuzwe)
```

### Imikhawulo Yokuthola

| Umehluko (inani eliphelele) | Ubunzima | Incazelo |
|---------------------------|----------|----------|
| < 0.2 amaphuzu | Okungachemi | Akukho ukuchema okuhlonziwe |
| 0.2 kuya ku-0.4 amaphuzu | Okuncane | Ukuthanda kancane noma ukungathandi |
| 0.4 kuya ku-0.6 amaphuzu | Okumaphakathi | Umkhuba obalulekile |
| > 0.6 amaphuzu | Okuphezulu | Ukuchema okubonakalayo |

### Indlela Yokuchaza
- **Imikhawulo enqabile** kunokuchema kwekilabhu, ngoba ubuzwe akufanele bube nomthelela ekuholeni kobuchwepheshe
- **Inani elinhle**: ukuthanda ubuzwe bakho
- **Inani elibi**: ukunzima ngokweqile kubuzwe bakho

### Isijeziso kumaphuzu onke

| Ubunzima | Isijeziso |
|----------|-----------|
| Okungachemi | 0 amaphuzu |
| Okuncane | -8 amaphuzu |
| Okumaphakathi | -16 amaphuzu |
| Okuphezulu | -25 amaphuzu |

---

## Indinganiso 3: Ukuchema Kokubekwa

### Umgomo
Le ndinganiso iqhathanisa **isilinganiso sonke samaphuzu** sommeli **nesilinganiso sabo bonke abammeli** emqhudelwaneni. Ibona abammeli abavame ukuba nomusa noma ukuba nzima ngokweqile.

### Ukubalwa
```
Umehluko = Isilinganiso(wonke amaphuzu ommeli) - Isilinganiso(wonke amaphuzu abo bonke abammeli)
```

### Imikhawulo Yokuthola

| Umehluko (inani eliphelele) | Ubunzima | Incazelo |
|---------------------------|----------|----------|
| < 0.2 amaphuzu | Okungachemi | Ephakathi kwesilinganiso, ukuhlola okulungiswe |
| 0.2 kuya ku-0.4 amaphuzu | Okuncane | Unomusa noma unzima kancane |
| 0.4 kuya ku-0.6 amaphuzu | Okumaphakathi | Unomusa noma unzima ngokubonakalayo |
| > 0.6 amaphuzu | Okuphezulu | Unomusa kakhulu noma unzima kakhulu |

### Indlela Yokuchaza
- **Inani elinhle** (+): ummeli uhlola ngokuvamile ngaphezulu kwesilinganiso (unomusa)
- **Inani elibi** (-): ummeli uhlola ngokuvamile ngaphansi kwesilinganiso (unzima)
- Ummeli omuhle usendaweni engachemi (< 0.2 amaphuzu umehluko)

### Isijeziso kumaphuzu onke

| Ubunzima | Isijeziso |
|----------|-----------|
| Okungachemi | 0 amaphuzu |
| Okuncane | -5 amaphuzu |
| Okumaphakathi | -12 amaphuzu |
| Okuphezulu | -20 amaphuzu |

---

## Indinganiso 4: Ukuhambisana Nabalingani

### Umgomo
Le ndinganiso ikala ukuthi amaphuzu ommeli **ahambisana kangakanani nawabanye abammeli** ngokusebenza okufanayo. Ummeli onamaphuzu avame ukuhluka kubalingani bakhe angaba nenkinga yokulungisa noma yokuchema.

### Ukubalwa
Ngokusebenza ngakunye okuhlolwe ngummeli:
```
Isilinganiso sabanye = Isilinganiso(amaphuzu abanye abammeli ngalokhu kusebenza)
Umehluko = |Amaphuzu ommeli - Isilinganiso sabanye|
Ukuhambisana komuntu = maks(0, 100 - (Umehluko × 20))
```

**Amaphuzu onke okuhambisana** ayisilinganiso sakho konke ukuhambisana komuntu.

### Incazelo

| Ukuhambisana | Incazelo |
|-------------|----------|
| **90-100%** | Ukuhambisana okuhle kakhulu, ukuhlola okuhambisanayo kakhulu |
| **75-89%** | Ukuhambisana okuhle |
| **60-74%** | Ukuhambisana okwamukelekayo kodwa kufanele kuthuthukiswe |
| **< 60%** | Ukuhambisana okuncane, **isexwayiso sidalwe** |

### Umthelela kumaphuzu onke
Ukuhambisana kuthinta amaphuzu okungachemi ngebhonasi/isijeziso:
```
Ukulungisa = (Ukuhambisana - 50) / 2
```
- Ukuhambisana kwe-100%: ibhonasi yamaphuzu angu-+25
- Ukuhambisana kwe-50%: ayikho ibhonasi noma isijeziso
- Ukuhambisana kwe-0%: isijeziso samaphuzu angu--25

### Imibandela
- Ubuncane **bokusebenza oku-3** okuhlolwe kudingeka ukuze ukubalwa kube nokubaluleka
- Amaphuzu asebenzayo kuphela (hhayi okuqeqeshwa) athathwa

---

## Uhlelo Lwezexwayiso

Izexwayiso zidalwa ngokuzenzakalelayo kulezi zimo ezilandelayo:

| Isimo | Isexwayiso |
|-------|-----------|
| Ukuchema kwekilabhu okumaphakathi noma okuphezulu | "Ukuchema kwekilabhu kuhlonziwe" nenani lomuhluko |
| Ukuchema kobuzwe okumaphakathi noma okuphezulu | "Ukuchema kobuzwe kuhlonziwe" nenani lomuhluko |
| Ukubekwa okuphezulu kuphela | "Ukubekwa okweqile" nomuhluko kusuka esilinganisweni |
| Ukuhambisana < 60% | "Ukuhambisana okuncane nabanye abammeli" |

Izexwayiso zibonakala ekhadini elinemininingwane lommeli ngamunye esixhumini sokuhlaziya.

---

## Iphodiyamu Labammeli Abangachemi Kakhulu

Ekugcineni kokuhlaziya, **iphodiyamu** ligqamisa abammeli aba-3 abanamaphuzu angcono kakhulu okungachemi:

- **Indawo yoku-1 (Igolide)**: Amaphuzu aphezulu kakhulu okungachemi
- **Indawo yesi-2 (Isiliva)**: Amaphuzu esibili angcono
- **Indawo yesi-3 (Ibronzi)**: Amaphuzu esithathu angcono

Loku kuhlela kuqhakambisa ukungachemi futhi kukhuthaza bonke abammeli ukuba bathuthuke.

---

## Izincomo Zabammeli

### Ukuze kuthuthukiswe amaphuzu akho okungachemi

1. **Ukuchema kwekilabhu**: Qaphela ngokukhethekile uma uhlola umhlanganyeli wekilabhu yakho. Sebenzisa izindinganiso ezifanayo zobuchwepheshe njengazo zonke ezinye.

2. **Ukuchema kobuzwe**: Gxila kubuchwepheshe nokwenziwa kuphela. Ubuzwe bomhlanganyeli akufanele buthinte ukuhlola kwakho.

3. **Ukubekwa**: Lungisa amaphuzu akho ngokulandela izindinganiso ezichaziwe. Ungabi nomusa noma ube nzima ngokweqile. Uma ungaqinisekile, bheka ithebula lamaphuzu elisemthethweni.

4. **Ukuhambisana**: Uma amaphuzu akho evame ukuhluka kuwabalingani bakho, lokhu kungabonisa inkinga yokuqonda izindinganiso. Hlanganyela ezikhathini zokulungisa.

### Imikhuba emihle

- Hlola ukusebenza ngakunye ngokuzimela, ngaphandle kokubheka amaphuzu abanye abammeli
- Sebenzisa ububanzi bonke besilinganiso samaphuzu
- Ungashintshi amaphuzu akho ngemva kokubona awabanye
- Thatha isikhathi sokuhlola indinganiso ngayinye ngokwahlukana
- Uma ukhathele, phumula ukuze ugcine ukugxila kwakho

---

## Ukufinyelela Nokugcina Imfihlo

- Ukuhlaziya kokungachemi kufinyelela **abahleleli bemiqhudelwano** **nabaphathi bezinhlangano**
- Ummeli ngamunye angabona **imiphumela yakhe**
- Idatha ibalwa **ngesikhathi sangempela** kusuka kumaphuzu akhona (akukho datha yokungachemi egcinwa isimile)
- Ukuhlaziya kudinga inombolo eyanele yamaphuzu ukuze kuthembekale (ubuncane bokusebenza oku-3 kokuhambisana)
