# Itupalẹ Aidọgba Awọn Adajo

## Ibi-afẹde

Apa itupalẹ aidọgba jẹ ki a le ṣe igbelewọn alainiṣe lori aibikita adajo kọọkan lakoko idije. O n ṣe wiwa awọn ojuṣe ti o ṣee ṣe laifọwọyi nipa ṣiṣe afiwe awọn aaye ti a fun gẹgẹ bi ọpọlọpọ awọn ilana iṣiro.

Apa yii jẹ irinṣẹ **ikẹkọ ati ilọsiwaju lemọlemọ** fun awọn adajo, kii ṣe irinṣẹ ibawi. O jẹ ki adajo kọọkan mọ awọn aṣa aiṣe-mọọmọ rẹ lati le ni ilọsiwaju.

---

## Aaye Aidọgba (0-100)

Adajo kọọkan gba **aaye aidọgba gbogbogbo** ti a ṣe iṣiro lori 100. Bi aaye naa ṣe ga to, bẹẹ ni a ka adajo naa si alaibikita.

A ṣe iṣiro aaye naa nipa yọ awọn ijiya kuro lati aaye pipe 100, gẹgẹ bi awọn ilana 4 ti a ṣe iwọn:

| Ilana | Iwuwo | Ijiya ti o pọ julọ |
|-------|-------|---------------------|
| Ojuṣe ẹgbẹ | 30% | -30 aaye |
| Ojuṣe orilẹ-ede | 25% | -25 aaye |
| Ojuṣe ipo | 20% | -20 aaye |
| Ibamu pẹlu awọn ẹlẹgbẹ | 25% | -25 aaye |

### Awọn Ipele Ewu

| Aaye | Ipele | Itumọ |
|------|-------|-------|
| **80-100** | Ewu kekere (alawọ ewe) | Adajo n ṣe isiro ni ibamu ati laibikita |
| **60-79** | Ewu agbedemeji (osan) | Awọn aṣa ti a ṣe wiwa, lati tẹle |
| **0-59** | Ewu giga (pupa) | Awọn ojuṣe pataki ti a ṣe wiwa, a ṣe igbaniyanju ikẹkọ |

---

## Ilana 1: Ojuṣe Ẹgbẹ

### Ilana

Ilana yii ṣe afiwe aarin awọn aaye ti adajo fun awọn olukose ti **ẹgbẹ tirẹ** pẹlu awọn olukose **ti awọn ẹgbẹ miiran**.

### Iṣiro
```
Iyatọ = Aarin(awọn aaye si awọn olukose ẹgbẹ kanna) - Aarin(awọn aaye si awọn olukose miiran)
```

### Awọn Ala Wiwa

| Iyatọ (iye alainiṣe) | Biba | Itumọ |
|----------------------|------|-------|
| < 0.3 aaye | Alaidọgba | Ko si ojuṣe ti a ṣe wiwa |
| 0.3 si 0.5 aaye | Kekere | Ojuṣe diẹ tabi ibinu diẹ |
| 0.5 si 0.8 aaye | Agbedemeji | Aṣa pataki lati tẹle |
| > 0.8 aaye | Giga | Ojuṣe ti o han gbangba, igbesẹ atunṣe a ṣe igbaniyanju |

### Bi O Ṣe Le Tumọ

- **Iye rere** (+): adajo naa ni aṣa lati fun awọn olukose ẹgbẹ rẹ ni aaye ti o ga julọ
- **Iye odi** (-): adajo naa ni aṣa lati le ju si awọn olukose ẹgbẹ rẹ (apọju atunṣe)
- Awọn ipo mejeeji jẹ ojuṣe lati ṣatunṣe

### Ijiya Lori Aaye Gbogbogbo

| Biba | Ijiya |
|------|-------|
| Alaidọgba | 0 aaye |
| Kekere | -10 aaye |
| Agbedemeji | -20 aaye |
| Giga | -30 aaye |

---

## Ilana 2: Ojuṣe Orilẹ-ede

### Ilana

Ilana yii ṣe afiwe aarin awọn aaye ti a fun awọn olukose ti **orilẹ-ede kanna** bi adajo pẹlu awọn olukose ti **awọn orilẹ-ede miiran**.

### Iṣiro
```
Iyatọ = Aarin(awọn aaye orilẹ-ede kanna) - Aarin(awọn aaye orilẹ-ede miiran)
```

### Awọn Ala Wiwa

| Iyatọ (iye alainiṣe) | Biba | Itumọ |
|----------------------|------|-------|
| < 0.2 aaye | Alaidọgba | Ko si ojuṣe ti a ṣe wiwa |
| 0.2 si 0.4 aaye | Kekere | Ojuṣe diẹ tabi ibinu diẹ |
| 0.4 si 0.6 aaye | Agbedemeji | Aṣa pataki |
| > 0.6 aaye | Giga | Ojuṣe ti o han gbangba |

### Bi O Ṣe Le Tumọ

- **Awọn ala ti o le ju** ju ti ojuṣe ẹgbẹ, nitori orilẹ-ede ko gbọdọ ni ipa kankan lori isiro imọ-ẹrọ
- **Iye rere**: ojuṣe si orilẹ-ede tirẹ
- **Iye odi**: ibinu ti o pọju si orilẹ-ede tirẹ

### Ijiya Lori Aaye Gbogbogbo

| Biba | Ijiya |
|------|-------|
| Alaidọgba | 0 aaye |
| Kekere | -8 aaye |
| Agbedemeji | -16 aaye |
| Giga | -25 aaye |

---

## Ilana 3: Ojuṣe Ipo

### Ilana

Ilana yii ṣe afiwe **aarin gbogbogbo awọn aaye** adajo kan pẹlu **aarin gbogbo awọn adajo** ni idije naa. O n ṣe wiwa awọn adajo ti wọn n ṣe ọlọla tabi wọn le ju leralera.

### Iṣiro
```
Iyatọ = Aarin(gbogbo awọn aaye adajo) - Aarin(gbogbo awọn aaye gbogbo awọn adajo)
```

### Awọn Ala Wiwa

| Iyatọ (iye alainiṣe) | Biba | Itumọ |
|----------------------|------|-------|
| < 0.2 aaye | Alaidọgba | Ninu aarin, isiro ti a ṣe deede |
| 0.2 si 0.4 aaye | Kekere | Ọlọla diẹ tabi lile diẹ |
| 0.4 si 0.6 aaye | Agbedemeji | Ọlọla tabi lile ni ọna ti o han |
| > 0.6 aaye | Giga | Ọlọla pupọ tabi lile pupọ |

### Bi O Ṣe Le Tumọ

- **Iye rere** (+): adajo n fun aaye ni oke aarin leralera (ọlọla)
- **Iye odi** (-): adajo n fun aaye ni isalẹ aarin leralera (lile)
- Adajo to dara wa ninu iwọn alaidọgba (< 0.2 iyatọ aaye)

### Ijiya Lori Aaye Gbogbogbo

| Biba | Ijiya |
|------|-------|
| Alaidọgba | 0 aaye |
| Kekere | -5 aaye |
| Agbedemeji | -12 aaye |
| Giga | -20 aaye |

---

## Ilana 4: Ibamu Pẹlu Awọn Ẹlẹgbẹ

### Ilana

Ilana yii ṣe iwọn bi awọn aaye adajo kan ṣe **ni ibamu pẹlu ti awọn adajo miiran** fun awọn isise kanna. Adajo ti awọn aaye rẹ yatọ leralera si ti awọn ẹlẹgbẹ rẹ le ni iṣoro deede tabi ojuṣe.

### Iṣiro
Fun isise kọọkan ti adajo ṣe isiro:
```
Aarin awọn miiran = Aarin(awọn aaye awọn adajo miiran fun isise yii)
Iyatọ = |Aaye adajo - Aarin awọn miiran|
Ibamu ẹni kọọkan = max(0, 100 - (Iyatọ × 20))
```

**Aaye ibamu gbogbogbo** jẹ aarin gbogbo awọn ibamu ẹni kọọkan.

### Itumọ

| Ibamu | Itumọ |
|-------|-------|
| **90-100%** | Ibamu ti o dara julọ, isiro ti o ni ibamu giga |
| **75-89%** | Ibamu to dara |
| **60-74%** | Ibamu ti o le gba ṣugbọn lati mu dara si |
| **< 60%** | Ibamu kekere, **itaniji ti a ṣẹda** |

### Ipa Lori Aaye Gbogbogbo
Ibamu ni ipa lori aaye aidọgba nipasẹ ẹbun/ijiya:
```
Atunṣe = (Ibamu - 50) / 2
```
- Ibamu 100%: ẹbun +25 aaye
- Ibamu 50%: ko si ẹbun bẹẹni ko si ijiya
- Ibamu 0%: ijiya -25 aaye

### Awọn Ipo

- O kere ju **isise 3** ti a ṣe isiro ni a nilo ki iṣiro naa le jẹ pataki
- Awọn aaye ti n ṣiṣẹ nikan (kii ṣe ikẹkọ) ni a ka sinu

---

## Eto Itaniji

A ṣẹda awọn itaniji laifọwọyi ninu awọn ipo wọnyi:

| Ipo | Itaniji |
|-----|---------|
| Ojuṣe ẹgbẹ agbedemeji tabi giga | "A ṣe wiwa ojuṣe ẹgbẹ" pẹlu iye iyatọ |
| Ojuṣe orilẹ-ede agbedemeji tabi giga | "A ṣe wiwa ojuṣe orilẹ-ede" pẹlu iye iyatọ |
| Ipo giga nikan | "Ipo iwọn" pẹlu iyatọ si aarin |
| Ibamu < 60% | "Ibamu kekere pẹlu awọn adajo miiran" |

Awọn itaniji han lori kaadi alaye adajo kọọkan ninu atọka itupalẹ.

---

## Podiomu Awọn Adajo Ti O Ni Aibikita Julọ

Ni opin itupalẹ, **podiomu** kan fi awọn adajo 3 ti o ni awọn aaye aidọgba ti o ga julọ han:

- **Ipo 1 (Goolu)**: Aaye aidọgba ti o ga julọ
- **Ipo 2 (Fadaka)**: Aaye keji ti o dara julọ
- **Ipo 3 (Idẹ)**: Aaye kẹta ti o dara julọ

Ipo yii ṣe ẹsan fun aibikita ati ṣe iwuri fun gbogbo awọn adajo lati ni ilọsiwaju.

---

## Awọn Igbaniyanju Fun Awọn Adajo

### Lati Mu Aaye Aidọgba Rẹ Dara Si

1. **Ojuṣe ẹgbẹ**: Ṣe akiyesi pataki nigbati o ba n fun olukose ẹgbẹ tirẹ ni aaye. Lo awọn ilana imọ-ẹrọ kanna bi fun awọn miiran.

2. **Ojuṣe orilẹ-ede**: Fojusi nikan lori imọ-ẹrọ ati isise. Orilẹ-ede olukose ko gbọdọ ni ipa lori igbelewọn rẹ.

3. **Ipo**: Ṣe deede awọn aaye rẹ nipa ṣiṣe ibamu pẹlu awọn ilana ti a ṣe alaye. Kii ṣe ọlọla ju, kii ṣe lile ju. Ni ọran aiyedede, tọka si ọna isiro osise.

4. **Ibamu**: Ti awọn aaye rẹ ba yatọ nigbagbogbo si ti awọn ẹlẹgbẹ rẹ, eyi le tọka si iṣoro loye awọn ilana. Kopa ninu awọn akoko deede.

### Awọn Iṣe Ti O Dara

- Fun aaye fun isise kọọkan ni ominira, laisi wo awọn aaye awọn adajo miiran
- Lo gbogbo iwọn ọna isiro
- Maṣe yi awọn aaye rẹ pada lẹyin ti o ri ti awọn miiran
- Gba akoko lati ṣe igbelewọn ilana kọọkan lọtọ
- Ni ọran àárẹ, sinmi lati pa ifojusi rẹ mọ

---

## Wiwọle ati Aṣiri

- Itupalẹ aidọgba wa fun **awọn oluṣeto idije** ati **awọn alabojuto ajọ agbaye**
- Adajo kọọkan le wo **awọn abajade tirẹ**
- A ṣe iṣiro data ni **akoko gidi** lati awọn aaye ti o wa tẹlẹ (ko si data aidọgba ti a tọju lailai)
- Itupalẹ naa nilo nọmba awọn aaye to to lati jẹ igbẹkẹle (o kere ju isise 3 fun ibamu)
