"""
Management command to translate all 81 tutorials from French to Yoruba.
Updates title_yo, steps_yo, and tip_yo fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_yo
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Abala 1: Iforukosile ati Igbese Akoko (awon ikoni 7)
    # =========================================================================
    1: {
        'title_yo': 'Iforukosile ati Igbese Akoko',
        'tutorials': {
            1: {
                'title_yo': 'Se akounti re ki o yan ipa re',
                'steps_yo': [
                    'Wole si MartialComp : Lo si martialcomp.com ki o te \'Forukosile lofee\'. O tun le se igbawo app alagbeka lati Play Store tabi App Store.',
                    'Kun foomu iforukosile : Fi oruko-idile re, oruko re, imeeli re ati oro-aabo re sii. O tun le forukosile pelu Google, Facebook tabi Apple ID fun iraye ti o roun.',
                    'Yan ipa akoko re : Yan ipa re: Olori Egbe, Olukoni, Adajo/Olulana, Olukopa tabi Olori Ajosepo. Yiyan yii ni yoo pinnu dasibodu re ati awon ise ti o le se, sugbon o le fi awon ipa miran kun nigbamii.',
                    'Jeri imeeli re : Wo apoti ifiranse re ki o te ase ijeri naa. Akounti re ti n sise, o si le wole si dasibodu ti a se ni pataki fun o.',
                ],
                'tip_yo': 'O le ni awon ipa puposi (b.a. olukoni ATI olukopa). Yi pada laarin awon ipa re lati awo osi ni igbakugba.',
            },
            2: {
                'title_yo': 'Se egbe re',
                'steps_yo': [
                    'Bere oluranlowo iseda : Lati dasibodu re, te \'Se egbe kan\'. Oluranlowo iseto ni igbese 4 yoo bere laifowoi.',
                    'Alaye gbogbogbo : Fi oruko egbe, akole kukuru, adiresi kikun ati alaye ibasoro (foonu, imeeli, aaye ayelujara) sii. Fi aami re kun ni iru PNG tabi JPG (iwon ti a daba: 500x500px).',
                    'Yan awon eko-ija : Yan eko-ija kan tabi ju bee lo lati inu 14+ ti o wa: Karate, Judo, BJJ, Taekwondo, MMA, Kung Fu, Aikido, Kendo, Muay Thai, Ija-afeseju, Capoeira, ati bee bee lo.',
                    'Se subdomaini re ni adani : Yan adiresi alailegbe re: egbe-re.martialcomp.com. Eyi ni yoo je adiresi gbangba ti egbe re, ti gbogbo eniyan le wole si.',
                    'Seto awon asayan : Seto awon wakati sisii, fi apejuwe ati awon aworan dojo re kun. Mu tabi da iforukosile ori ayelujara ti awon olukopa duro.',
                ],
                'tip_yo': 'Egbe re ni a da pelu eto Ofe (to awon omo egbe 10). Gbogbo awon ise n sise lati ibere. Se igbesoke si Premium nigba ti o ba koja awon omo egbe 10.',
            },
            3: {
                'title_yo': 'Se ajosepo re',
                'steps_yo': [
                    'Beere iseda : Yan ipa \'Olori Ajosepo\' lakoko iforukosile tabi fi kun lati Awon eto. Kun foomu iseda pelu alaye osise ti ajosepo re.',
                    'Alaye osise : Fi oruko kikun, akole kukuru, orilede, awon eko-ija ti o bo, nomba iforukosile osise ati alaye ibasoro sii.',
                    'Seto aaye ayelujara gbangba : Se aaye gbangba re ni adani: asia, aami, awon awu, apejuwe, ile-aworan aworan ati awon asepo si awon neetiwoki awujo re.',
                    'Seto eto ile-ise : Seto awon ajumose agbegbe re ti o ba ye, so awon eka idapomo fun awon egbe ati awon iye owo-ose.',
                ],
                'tip_yo': 'Awon ajosepo ni agbegbe isakoso ti o gbooro lati bojuto gbogbo awon egbe ti o darapo, awon idije ati awon ipele.',
            },
            4: {
                'title_yo': 'Seto profaili olukoni re',
                'steps_yo': [
                    'Wole si profaili olukoni : Lati awo osi, te \'Profaili olukoni mi\'. Ti o ko ba ti ni ipa olukoni, fi kun lati Awon eto > Awon ipa mi.',
                    'Fi awon iwe-eri re sii : Fi awon iwe-ase re (BPJEPS, DEJEPS, CQP, ati bee bee lo), awon ipele re ninu eko-ija kookan ati awon odun iriri re kun.',
                    'So awon eko-ija re : Yan awon eko-ija ti o n ko ati ipele amojuto re ninu okosooto (awon olubere, awon ti o ti tesiwaju, idije).',
                    'Seto wiwawa re : Fihan awon aaye wakati ikoni osoose re. Alaye yii yoo han fun awon egbe ti n wa awon olukoni.',
                ],
                'tip_yo': 'Profaili olukoni ti o pe pelu aworan ati awon iwe-eri n mu iranwo re posi gan-an fun awon egbe.',
            },
            5: {
                'title_yo': 'Seto profaili adajo re',
                'steps_yo': [
                    'Mu ipa adajo sise : Lati Awon eto > Awon ipa mi, mu ipa \'Adajo / Olulana\' sise. Fi nomba iwe-ase adajo re sii ti o ba ye.',
                    'Fi awon iwe-eri re kun : Fihan ipele adajo re (agbegbe, orilede, agbaye), awon eko-ija ti o ni iwe-eri fun ati awon iwe-eri re.',
                    'So awon amojuto re : Kata/awon ilana, ija, ikun-ami ise-ono... Amojuto kookan ni o fun o laaye fun awon idije ti o bamu.',
                    'Fi wiwawa re sii : Fihan awon agbegbe ati awon akoko wiwawa re fun awon idije.',
                ],
                'tip_yo': 'Awon oluṣeto idije le wa o ki o pe o taara gege bi awon iwe-eri ati wiwawa re.',
            },
            6: {
                'title_yo': 'Seto profaili olukopa re',
                'steps_yo': [
                    'Kun alaye ti ara eni : Fi ojo-ibi re, abo, iwuwo (fun eka idije), giga ati aworan profaili sii.',
                    'Fi ipele lowe re kun : Fihan eko-ija akoko re, ipele lowe re (igbanu), ojo ti o gba ati ajose ti o fun.',
                    'Fi iwe-ase re sii : Fi nomba iwe-ase ajosepo re, ojo ipari ati iwe-eri dokita lowe kun.',
                    'Awon eniyan lati pe ni pajawiri : Fi o kere ju eniyan kan lati pe ni pajawiri (o je dandan fun awon idije): oruko, foonu, ibasepo.',
                ],
                'tip_yo': 'Profaili ti o pe ni o nilo lati forukosile fun awon idije. Iwuwo ati ipele ni yoo pinnu eka re laifowoi.',
            },
            7: {
                'title_yo': 'Loye dasibodu ati lilokiri',
                'steps_yo': [
                    'Dasibodu naa : Dasibodu re n fihan akopupo ti a se ni adani: awon isele ti n bo, awon ifiranse aipupo, awon iṣiro iyara ati awon asepo si awon ise ti o n se nigbagbogbo.',
                    'Igi osi : Awo osi n fun o ni iraye si gbogbo awon abala: Awon omo egbe, Awon idije, Awon ipele, Inawo, Kalenda, Awon eto. O bamu pelu ipa lowo re.',
                    'Yi ipa pada : Ti o ba ni awon ipa puposi (b.a. olukoni + olukopa), te aworan re ni oke apa otun lati yi pada. Dasibodu ati awo yoo bamu laifowoi.',
                    'Awon iwifunni ati ifiranse : Aami agogo ni oke apa otun n fihan awon iwifunni re: iforukosile, awon abajade, awon ifiranse. Seto awon ayanfe iwifunni re ni awon eto.',
                    'Wiwa gbogbogbo : Lo igi wiwa lati wa olukopa, egbe, idije tabi isele ni kiakia.',
                ],
                'tip_yo': 'Se dasibodu re ni adani nipa fifi awon widjeti ayanfe re mu. Asepo keyboard Ctrl+K n si wiwa iyara.',
            },
        },
    },

    # =========================================================================
    # Abala 2: Isakoso Egbe (awon ikoni 10)
    # =========================================================================
    2: {
        'title_yo': 'Isakoso Egbe',
        'tutorials': {
            1: {
                'title_yo': 'Fi awon olukopa kun pelu owo',
                'steps_yo': [
                    'Si foomu fifikun : Lati Awon omo egbe > Fi olukopa kun, kun foomu naa: oruko-idile, oruko, ojo-ibi, abo, imeeli ati foonu.',
                    'Alaye afikun : Fi ipele lowe, nomba iwe-ase, aworan idanimo (yan) ati iwe-eri dokita kun.',
                    'Fi si ẹgbẹ kan : Fi olukopa naa si ẹgbẹ ikẹkọọ kan tabi ju bee lo (b.a. Karate Agbalagba Ti Tesiwaju, Judo Omode Olubere).',
                    'Fi ipe-owo ranṣẹ : Samisi \'Fi imeeli ipe-owo ranṣẹ\' ki olukopa naa le ṣẹda akounti tirẹ ki o si wọle si profaili rẹ lori ayelujara.',
                ],
                'tip_yo': 'Olukopa naa yoo gba imeeli pẹlu asepo lati pari iforukosile rẹ ati lati ṣe igbawo app alagbeka.',
            },
            2: {
                'title_yo': 'Agbekale pupo ti awon olukopa (CSV/Excel)',
                'steps_yo': [
                    'Se igbawo awoṣe naa : Lati Awon omo egbe > Gbe wole, se igbawo awoṣe CSV tabi Excel naa. Faili naa ni awon ila dandan: Oruko-idile, Oruko, Ojo_ibi, Imeeli, ati awon ila yan: Ipele, Iwe-ase, Foonu.',
                    'Kun faili naa : Kun faili naa pelu data awon olukopa re. Bowo fun awon ọna: awon ojo ni DD/MM/ỌDUN, awon ipele bi ọrọ (b.a. \'Igbanu alawọ ewe\', \'Dan keji\').',
                    'Gbe soke ki o ṣe mapu awon ila : Gbe faili naa wole. Atọka mapu n jẹ ki o sopọ ila kookan ti faili re pelu awon aaye MartialComp. Ṣayẹwo mapu naa.',
                    'Fidi mu ati ṣatunṣe : MartialComp n wa awon aṣiṣe (awon meji, awon ọna ti ko tọ). Ṣatunṣe awon ori ti o ni aṣiṣe tabi fo wọn. Jeri agbekale naa.',
                ],
                'tip_yo': 'O le gbe wole to awon olukopa 500 ni iṣiṣe kan. Agbekale naa n wa awon meji laifowoi nipa imeeli tabi oruko-idile + oruko + ojo-ibi.',
            },
            3: {
                'title_yo': 'Ṣakoso awon kaadi olukopa',
                'steps_yo': [
                    'Wole si kaadi naa : Lati atokọ awon omo egbe, te oruko olukopa kan lati si kaadi kikun rẹ.',
                    'Wo awon alaye : Kaadi naa n fihan: alaye ti ara eni, itan ipele, awon idije ti o ti ṣe, wiwa ati awon owo-oṣe.',
                    'Ṣatunṣe alaye naa : Te \'Ṣatunṣe\' lati mu data ṣe. Awon ayipada ni a kọ sinu itan.',
                    'Awon iṣe iyara : Lati kaadi naa o le: forukosile fun idije, fi ipele kan, fi ifiranṣe ranṣẹ, ṣe iwe-eri kan.',
                ],
                'tip_yo': 'Lo awon asẹ ilọsiwaju (ipele, ojo ori, iwe-ase lowo, owo-oṣe ti a san) lati wa olukopa kan ni kiakia.',
            },
            4: {
                'title_yo': 'Se akounti olumulo fun olukopa kan',
                'steps_yo': [
                    'Wole si kaadi olukopa naa : Si kaadi olukopa ti o bamu lati atokọ awon omo egbe.',
                    'So mọ akounti kan : Te \'Ṣe akounti olumulo\'. A o fi imeeli ipe-owo ranṣẹ si olukopa naa pelu asepo lati ṣe oro-aabo rẹ.',
                    'Seto awon aṣẹ : Yan ohun ti olukopa le ṣe: wo awon abajade rẹ, forukosile fun awon idije, wo kalenda, san lori ayelujara.',
                ],
                'tip_yo': 'Awon olukopa ti o kere le ni akounti ti o sopọ si ti obi nipasẹ iṣẹ Ẹgbẹ Ebi.',
            },
            5: {
                'title_yo': 'Ṣakoso awon ipa ati aṣẹ egbe',
                'steps_yo': [
                    'Wole si iṣakoso awon ipa : Lati Awon eto > Awon ipa ati aṣẹ, wo awon ipa ti o wa: Alakoso, Akowe, Olutọju-owo, Olukoni, Omo egbe.',
                    'Fi ipa kan : Yan omo egbe kan ki o fi ipa kan fun. Ipa kookan n fun ni iraye si awon iṣẹ pataki.',
                    'Ṣe aṣẹ ni adani : Fun ipa kookan, ṣalaye awon ẹtọ: kika nikan, ṣiṣatunṣe, piparẹ, iraye si inawo, iṣakoso iforukosile.',
                    'Ṣayẹwo iraye : Wo igbasilẹ iṣẹ lati ri tani ṣe kini ati nigbawo ninu iṣakoso egbe naa.',
                ],
                'tip_yo': 'Ipa Alakoso ni gbogbo ẹtọ. Ṣe ipa Akowe pelu iraye si awon omo egbe ati kalenda sugbon kii ṣe inawo.',
            },
            6: {
                'title_yo': 'Ipasẹ wiwa / Iforukosile dede',
                'steps_yo': [
                    'Ṣe igba kan : Lati Wiwa > Igba tuntun, yan ẹgbẹ ikẹkọọ, ojo ati akoko kilasi naa.',
                    'Forukosile nipasẹ atokọ : Ṣe afihan atokọ awon omo egbe ẹgbẹ naa ki o ṣe aami awon ti o wa. Iforukosile naa n ṣe pelu itẹ kan lori alagbeka.',
                    'Forukosile nipasẹ koodu QR : Ṣe afihan koodu QR igba naa. Awon olukopa n ṣayẹwo rẹ pelu foonu won nigba ti won de dojo.',
                    'Wo awon iṣiro : Wo awon oṣuwọn wiwa fun olukopa, ẹgbẹ ati akoko. Ṣe idanimọ awon aiwa ti o n tun ṣe.',
                ],
                'tip_yo': 'Iforukosile nipasẹ koodu QR ni ọna ti o yara julo fun awon ẹgbẹ nla. Koodu naa n yipada ni igba kookan lati yago fun ẹtan.',
            },
            7: {
                'title_yo': 'Ṣakoso awon eto ikẹkọọ',
                'steps_yo': [
                    'Ṣe eto kan : Lati Awon eto > Tuntun, ṣalaye oruko, eko-ija, ipele (olubere, aarin, ilọsiwaju) ati iye akoko naa.',
                    'Gbero awon igba : Fi awon aaye wakati oṣooṣe kun: ojo, akoko ibere, akoko ipari, yara/tatami, olukoni ti o ni ojuṣe.',
                    'Ṣalaye awon akoonu : Fun igba kookan, fi eto kun: igbona ara, iṣẹ ilana, sparring/randori, itura pada. Fi awon faili tabi fidio kun.',
                    'Gbejade ati firanṣẹ iwifunni : Gbejade eto naa. Awon olukopa ẹgbẹ naa n gba iwifunni pelu eto kikun.',
                ],
                'tip_yo': 'Ṣe adaako eto ti o wa tẹlẹ lati ṣe akoko tuntun ni kiakia pelu awon iyatọ.',
            },
            8: {
                'title_yo': 'Ṣe ati lo awon koodu QR egbe',
                'steps_yo': [
                    'Ṣe koodu QR egbe : Lati Awon eto > Awon koodu QR, ṣe koodu QR egbe re. O n jẹ ki awon alejo wole taara si oju-iwe gbangba re.',
                    'Awon koodu QR pataki : Ṣe awon koodu QR fun: iforukosile lori ayelujara, iforukosile igba, oju-iwe iṣẹlẹ tabi asepo si app alagbeka.',
                    'Tẹ sita ki o han : Ṣe igbawo awon koodu QR ni didara giga lati tẹ sita. Awon ọna ti o wa: PNG, SVG, PDF (A4 tabi kaadi iṣowo).',
                    'Tẹle awon iṣiro : Wo nọmba awon ayẹwo fun koodu QR kookan, fun ojo kookan ati fun iru kookan. Ṣe idanimọ awon koodu QR ti o munadoko julo.',
                ],
                'tip_yo': 'Fi koodu QR iforukosile han ni ẹnu-bode dojo re. Ayẹwo kookan jẹ onibara ti o le jẹ!',
            },
            9: {
                'title_yo': 'Beere fun idapọ si ajosepo',
                'steps_yo': [
                    'Wa ajosepo re : Lati Egbe > Idapọ, wa ajosepo re nipa oruko, eko-ija tabi orilẹ-ede.',
                    'Fi ibeere ranṣẹ : Kun foomu idapọ: alaye egbe, nomba iforukosile, awon iwe-eri (ofin, iṣeduro, ati bee bee lo).',
                    'Tẹle ipo naa : Ibeere re n kọja nipasẹ awon igbese: Ti a ranṣẹ > Ni ayẹwo > Ti a fọwọsi/Ti a kọ. O n gba iwifunni ni igbese kookan.',
                    'Tunṣe ni akoko kookan : Idapọ jẹ fun akoko kan. Iranti aifowoi ni a ranṣẹ ọjọ 30 ṣaaju ki o to pari.',
                ],
                'tip_yo': 'Idapọ n fun o ni iraye si awon idije osise ti ajosepo ati iṣakoso aarin ti awon iwe-ase.',
            },
            10: {
                'title_yo': 'Ṣakoso gbigbe awon olukopa',
                'steps_yo': [
                    'Bere gbigbe : Lati kaadi olukopa kan, te \'Beere fun gbigbe\'. Yan egbe ti o n lo si ati idi gbigbe naa.',
                    'Ilana ifọwọsi : Egbe ti o n lo si gba ibeere naa ati pe o le gba tabi kọ. Ti ajosepo ba wa ninu, o gbọdọ fọwọsi pelu.',
                    'Gbigbe gangan : Ti a ba fọwọsi, olukopa naa n gbe lọ laifowoi pelu ipele ati itan idije rẹ.',
                    'Wo itan naa : Itan gbigbe ni a le ri ninu kaadi olukopa ati ninu awon ijabọ egbe.',
                ],
                'tip_yo': 'Awon ajosepo kan n fi awon akoko gbigbe kalẹ (awon ferese gbigbe). MartialComp n bọwọ fun awon ofin wọnyi laifowoi.',
            },
        },
    },

    # =========================================================================
    # Abala 3: Awon Idije - Iseda ati Iseto (awon ikoni 6)
    # =========================================================================
    3: {
        'title_yo': 'Awon Idije - Iseda ati Iseto',
        'tutorials': {
            1: {
                'title_yo': 'Se idije olukopa kan',
                'steps_yo': [
                    'Bere iseda : Lati Awon idije > Ṣe, yan iru \'Olukopa\'. Fi oruko, eko-ija, awon ojo ati ibi sii.',
                    'Ṣalaye ọna : Yan ọna naa: Ija (kumite, randori, sparring), Ilana (kata, poomsae, awon fọọmu) tabi Adapọ (mejeeji).',
                    'Seto awon eka : Ṣalaye awon eka nipa abo, ibiti ojo ori, iwuwo ati/tabi ipele. MartialComp n funni ni awon awoṣe eka boṣewa fun eko-ija kookan.',
                    'Awon asayan ati atẹjade : Mu awon asayan ti o fẹ sise: iforukosile lori ayelujara, isanwo, igbohunsafefe ni igba gidi, awon abajade gbangba. Gbejade idije naa.',
                ],
                'tip_yo': 'Lo awon awoṣe eka (WKF, IJF, ITF...) lati fi akoko pamọ. O le ṣe wọn ni adani lẹhin iseda.',
            },
            2: {
                'title_yo': 'Se idije ẹgbẹ kan (Amuṣiṣẹpọ/Song Luyen)',
                'steps_yo': [
                    'Yan ipo ẹgbẹ : Lakoko iseda, yan iru \'Ẹgbẹ\'. Ṣalaye nọmba to kere julọ ati ti o pọ julọ ti awon omo egbe fun ẹgbẹ kookan.',
                    'Seto ọna ẹgbẹ : Yan ọna naa: Amuṣiṣẹpọ (kata/poomsae ẹgbẹ), Song Luyen (ija ti a ti ṣeto fun meji) tabi Ija ẹgbẹ (yiyi pada).',
                    'Ṣalaye akojọpọ : Ṣalaye awon ipa ninu ẹgbẹ: nọmba awon akoko, nọmba awon aropo, boya a gba adapọ tabi rara.',
                    'Awon ilana ikun-ami ẹgbẹ : Fun ikun-ami ilana, ṣalaye boya awon adajo n ṣe ayẹwo ẹgbẹ naa papọ tabi omo egbe kookan lọtọ.',
                ],
                'tip_yo': 'Ipo Amuṣiṣẹpọ n gba ikun-ami pelu awon ilana imuṣiṣẹpọ pataki (akoko, ititọ, ikosile apapọ).',
            },
            3: {
                'title_yo': 'Seto awon eka idije',
                'steps_yo': [
                    'Wole si iṣakoso eka : Lati idije ti a ṣe, lọ si taabu Awon eka. Te \'Fi eka kan kun\'.',
                    'Ṣalaye awon ilana : Fun eka kookan, ṣalaye: abo (O/A/Adapọ), ibiti ojo ori (b.a. ọdun 12-14), ibiti iwuwo (b.a. -60kg), ipele to kere/to pọ julọ.',
                    'Fun eka naa ni oruko : Fun ni oruko ti o ye: \'Ọdọmọde Okunrin -52kg\' tabi \'Kata Agbalagba Obinrin Ti Tesiwaju\'. MartialComp n ṣe awon oruko laifowoi ti o ba fẹ.',
                    'Ṣeto awon eka : Tun awon eka ṣeto nipa fifa-si-ati-jiju lati fi idi aṣẹ ifihan mulẹ ni ojo idije naa.',
                ],
                'tip_yo': 'Gbe awon eka wole lati idije ti o ti kọja lati fi akoko pamọ. Lo asayan \'Adaako Ologbon\' lati ṣe awon iyatọ.',
            },
            4: {
                'title_yo': 'Ṣe adaako idije ti o wa tẹlẹ',
                'steps_yo': [
                    'Wa idije orisun : Lati Awon idije > Itan, wa idije ti o fẹ ṣe adaako.',
                    'Bere adaako : Te awon aami 3 > Ṣe adaako. Yan ohun ti o fẹ daako: awon eka, ofin, iseto, awon owo.',
                    'Ṣatunṣe iseto : Yi awon ojo, ibi ati awon ohun ti o nilo pada. Awon eka ati ofin ni a daako gangan.',
                ],
                'tip_yo': 'O dara julọ fun awon idije ọdọọdun ti o n tun ṣe. Ṣe adaako ẹda ti o kọja ki o kan mu awon ojo ṣe.',
            },
            5: {
                'title_yo': 'Seto awon asayan ifihan',
                'steps_yo': [
                    'Wole si iseto ifihan : Lati idije naa, lọ si Iseto > Ifihan ati pinpin.',
                    'Iforukosile lori ayelujara : Mu/da awon iforukosile gbangba duro. Seto awon ojo ṣiṣi ati pipadé iforukosile.',
                    'Awon abajade ati ipo : Yan boya awon abajade jẹ gbangba ni igba gidi, ti a gbejade lẹhin ifọwọsi tabi ikọkọ (oluṣeto nikan).',
                    'Igbohunsafefe ni igba gidi : Mu ipo igbohunsafefe sise ki o fi asepo YouTube/Twitch/Facebook Live kun lati han lori oju-iwe gbangba.',
                ],
                'tip_yo': 'Awon abajade ni igba gidi n fa awon oluwo si oju-iwe re ati mu iranwo egbe tabi ajosepo re posi.',
            },
            6: {
                'title_yo': 'Seto awon ofin ija',
                'steps_yo': [
                    'Yan ofin kan : Yan ofin ti a ti seto tẹlẹ (WKF, IJF, ITF, IBJJF, ati bee bee lo) tabi ṣe tirẹ.',
                    'Ṣalaye ikun-ami : Seto awon iṣe ati awon aami wọn: Yuko (1pt), Waza-ari (2pts), Ippon (3pts), ati bee bee lo. Fi awon ijiya kun (Shido, Hansoku, ati bee bee lo).',
                    'Seto awon iyipo : Ṣalaye iye akoko awon iyipo, nọmba awon iyipo, awon isinmi ati awon ipo iṣẹgun (awon aami, Ippon, fifunni).',
                    'Awon ofin pataki : Seto awon ofin pato: Golden Score (akoko afikun), Hantei (ipinnu awon adajo), ipari ni kutukutu nipa iyatọ aami.',
                ],
                'tip_yo': 'Fi awon ofin adani re pamọ bi awon awoṣe lati tun lo ninu awon idije ọjọ iwaju.',
            },
        },
    },

    # =========================================================================
    # Abala 4: Iforukosile ati Awon Ẹgbẹ (awon ikoni 7)
    # =========================================================================
    4: {
        'title_yo': 'Iforukosile ati Awon Ẹgbẹ',
        'tutorials': {
            1: {
                'title_yo': 'Forukosile awon olukopa fun idije kan',
                'steps_yo': [
                    'Wa idije naa : Lati Awon idije > Ti ṣii fun iforukosile, wa idije ti o fẹ ki o te \'Forukosile\'.',
                    'Yan awon olukopa : Atokọ awon omo egbe re n han. Yan olukopa kan tabi ju bee lo. MartialComp n fihan awon eka ti o yẹ fun okosooto laifowoi.',
                    'Jeri awon eka : Fun olukopa kookan, jeri tabi yi eka ti a daba pada. Eto naa n ṣayẹwo pe iwuwo, ojo ori ati ipele bamu.',
                    'Fidi mu ki o san : Jeri awon iforukosile. Ti idije naa ba nilo isanwo, san fun gbogbo awon iforukosile.',
                ],
                'tip_yo': 'Awon olukopa ti o ni profaili ti ko pe (iwuwo ti ko si, iwe-ase ti pari) ni a o fi aami itaniji pupa si.',
            },
            2: {
                'title_yo': 'Iforukosile pupọ nipasẹ foomu',
                'steps_yo': [
                    'Wole si ipo pupọ : Lati iboju iforukosile, te \'Iforukosile pupọ\'. Yan eka ibi-afẹde naa.',
                    'Yan ẹgbẹ naa : Sẹ nipasẹ ẹgbẹ ikẹkọọ, ipele tabi ojo ori. Yan awon olukopa ti o yẹ pelu itẹ kan.',
                    'Ṣayẹwo ki o ṣatunṣe : Iboju ayẹwo n fihan olukopa kookan pelu eka rẹ. Ṣatunṣe awon aṣiṣe ti o ba wa.',
                    'Jeri akojọ naa : Fidi gbogbo awon iforukosile mulẹ ni iṣiṣe kan. Akopupo ni a fi ranṣẹ nipasẹ imeeli.',
                ],
                'tip_yo': 'Iforukosile pupọ dara julọ fun awon egbe ti o forukosile awon olukopa 10+ fun idije kanna.',
            },
            3: {
                'title_yo': 'Ṣe ati ṣakoso awon ẹgbẹ',
                'steps_yo': [
                    'Ṣe ẹgbẹ kan : Lati idije naa, te \'Forukosile ẹgbẹ kan\'. Fun ẹgbẹ naa ni oruko ki o yan eka naa.',
                    'Fi awon omo egbe kun : Fi awon omo egbe ẹgbẹ kun lati atokọ awon olukopa re. Bọwọ fun awon nọmba to kere ati to pọ julọ ti a ṣalaye.',
                    'Seto awon akoko ati aropo : Yan awon akoko ati awon aropo nipa fifa-si-ati-jiju. Aṣẹ ifihan le ṣe nibi.',
                    'Fidi ẹgbẹ naa mulẹ : Ṣayẹwo ibamu ẹgbẹ naa (nọmba awon omo egbe, awon eka olukopa) ki o jeri iforukosile naa.',
                ],
                'tip_yo': 'Ninu awon idije ẹgbẹ, oruko ẹgbẹ naa n han lori awon iwe-aami ati ninu awon abajade osise.',
            },
            4: {
                'title_yo': 'Yi eka ẹgbẹ kan pada',
                'steps_yo': [
                    'Wole si ẹgbẹ naa : Lati awon iforukosile re, wa ẹgbẹ ti o fẹ yi pada ki o te \'Ṣatunṣe\'.',
                    'Yi eka pada : Yan eka tuntun lati awo yiyan. Eto naa n ṣayẹwo pe ẹgbẹ naa bamu pelu awon ilana.',
                    'Jeri iyipada : Fidi rẹ mulẹ. Ti idije naa ba ni awon owo iforukosile ti o yatọ fun eka kookan, atunṣe jẹ laifowoi.',
                ],
                'tip_yo': 'Yiyipada eka nikan ṣee ṣe nigba ti awon iforukosile ba ṣi ṣii.',
            },
            5: {
                'title_yo': 'Beere fun adehun (idapọ laarin awon egbe)',
                'steps_yo': [
                    'Ṣe idanimọ iwulo : Egbe re ko ni awon omo egbe to lati ṣe ẹgbẹ kikun? Adehun n gba laaye lati dapọ awon ẹgbẹ lati awon egbe oriṣiriṣi.',
                    'Ṣe ibeere adehun : Lati ẹgbẹ ti ko pe, te \'Dabaa adehun kan\'. Yan egbe alabaṣepọ ati awon ipo ti o fẹ kun.',
                    'Fi ibeere ranṣẹ : Egbe alabaṣepọ gba ibeere naa pelu awon alaye: idije, eka, awon ipo ti o wa, awon ipo.',
                    'Pari adehun : Ti a ba gba, ẹgbẹ ti a dapọ n han pelu awon omo egbe lati awon egbe mejeeji. Ẹgbẹ naa n jẹ oruko ti o papọ awon egbe mejeeji.',
                ],
                'tip_yo': 'Adehun naa wa labẹ ifọwọsi oluṣeto idije ati, ti o ba ye, ajosepo naa.',
            },
            6: {
                'title_yo': 'Gba/kọ ibeere adehun kan',
                'steps_yo': [
                    'Gba iwifunni : O gba iwifunni ibeere adehun. Te lati wo awon alaye.',
                    'Ṣayẹwo ibeere naa : Ṣayẹwo: egbe ti o beere, idije, eka, awon ipo ti o fẹ kun ati awon ipo ti a dabaa.',
                    'Gba tabi kọ : Te \'Gba\' lati fọwọsi adehun naa ki o yan awon omo egbe re, tabi \'Kọ\' pelu ifiranṣẹ alaye.',
                ],
                'tip_yo': 'O le dabaa ibeere omiiran nipa yiyipada awon ipo ṣaaju ki o to gba.',
            },
            7: {
                'title_yo': 'Ṣakoso awon iforukosile ti a gba (ifọwọsi)',
                'steps_yo': [
                    'Wole si paneeli iforukosile : Lati idije naa, lọ si taabu Iforukosile. Wo awon iforukosile nipa ipo: Nduro, Ti a fọwọsi, Ti a kọ.',
                    'Ṣayẹwo ki o fọwọsi : Te iforukosile kan lati ṣayẹwo alaye olukopa. Fọwọsi lọkọọkan tabi ni akojọ.',
                    'Kọ pelu idi : Ni ipo ikọ, yan idi kan: eka ti ko tọ, iwe-ase ti ko wulo, iforukosile ti pẹ, ati bee bee lo.',
                    'Gbe atokọ jade : Gbe atokọ awon olukopa ti o wulo jade ni CSV tabi PDF fun iwọn ati iṣakoso ni ojo idije naa.',
                ],
                'tip_yo': 'Mu ifọwọsi aifowoi sise ti o ko ba fẹ fọwọsi iforukosile kookan pelu owo.',
            },
        },
    },

    # =========================================================================
    # Abala 5: Ojo Idije - Ija (awon ikoni 8)
    # =========================================================================
    5: {
        'title_yo': 'Ojo Idije - Ija',
        'tutorials': {
            1: {
                'title_yo': 'Ṣe awon ẹgbẹ idije laifowoi',
                'steps_yo': [
                    'Wole si iṣakoso ẹgbẹ idije : Lati idije naa, lọ si Awon ẹgbẹ idije > Ṣe laifowoi. Yan awon eka ti o fẹ ṣe.',
                    'Seto pinpin : Ṣalaye: nọmba awon abanidije fun ẹgbẹ idije kookan, iyapa awon omo egbe egbe kanna, awon olori pelu owo (yan).',
                    'Ṣe ki o ṣayẹwo : Te \'Ṣe\'. MartialComp n pin awon abanidije lati yago fun ija laarin egbe kanna ni iyipo akọkọ.',
                    'Ṣatunṣe pelu owo : Ti o ba nilo, gbe awon abanidije laarin awon ẹgbẹ idije nipa fifa-si-ati-jiju. Eto naa n ṣayẹwo awon rogbodiyan ni igba gidi.',
                ],
                'tip_yo': 'Alugoritima pinpin n ṣe idaniloju idogba nipa yiyapa awon egbe ati didọgba awon ipele agbara laarin awon ẹgbẹ idije.',
            },
            2: {
                'title_yo': 'Ṣeto ati tun awon ẹgbẹ idije ṣe',
                'steps_yo': [
                    'Iwoye gbogbogbo awon ẹgbẹ idije : Iboju awon ẹgbẹ idije n fihan gbogbo awon eka pelu nọmba awon abanidije, awon ẹgbẹ idije ati ipo (akọkọ, ti a fọwọsi, ti n lọ).',
                    'Ṣatunṣe ẹgbẹ idije kan : Te ẹgbẹ idije kan lati wo awon abanidije. Lo fifa-si-ati-jiju lati gbe abanidije kan si ẹgbẹ idije miran.',
                    'Ṣakoso aiwa : Ṣe aami abanidije kan bi aibesi tabi ifasẹhin. Eto naa n tun ṣe iṣiro awon ija ati awon ipo laifowoi.',
                    'Fidi awon ẹgbẹ idije mulẹ : Ti o ba tẹ lọrun, fidi awon ẹgbẹ idije mulẹ. Iṣe yii n ṣe tabili awon ija laifowoi.',
                ],
                'tip_yo': 'Fidi awon ẹgbẹ idije mulẹ eka nipasẹ eka lati bere awon ija ti awon eka akọkọ nigba ti o n pari awon miiran.',
            },
            3: {
                'title_yo': 'Gbero aago awon ija',
                'steps_yo': [
                    'Ṣalaye awon agbegbe ija : Lati Eto > Awon agbegbe, ṣalaye nọmba awon tatami/ring ti o wa ati awon oruko wọn (Tatami 1, Ring A, ati bee bee lo).',
                    'Fi awon aaye wakati sii : Fa awon eka sori awon agbegbe ati awon aaye wakati. MartialComp n ṣe iṣiro iye akoko ti a foju bu laifowoi.',
                    'Ṣe awari awon rogbodiyan : Eto naa n ṣe awari awon rogbodiyan: abanidije kan ti o forukosile fun awon eka 2 ni akoko kanna. Lo awon itaniji lati ṣatunṣe.',
                    'Gbejade eto naa : Gbejade eto naa. Awon abanidije, awon olukoni ati awon adajo n gba iwifunni pelu awon aago ikopa wọn.',
                ],
                'tip_yo': 'Gbero akoko afikun 20% fun eka kookan lati ṣakoso awon idaduro ti ko ṣee yago fun.',
            },
            4: {
                'title_yo': 'Lo atọka ija (ikun-ami ni igba gidi)',
                'steps_yo': [
                    'Wole si agbegbe : Lori tabulẹti tabi foonu re, ṣi MartialComp ki o yan agbegbe ija ti a fi le ọ lọwọ. Fi PIN adajo re sii.',
                    'Atọka ikun-ami : Iboju n fihan: awon abanidije 2 (pupa/bulu), awon bọtini iṣe (awon aami, awon ijiya), asiko ati ikun-ami lowe.',
                    'Fun aami : Te awon bọtini ikun-ami: Yuko (+1), Waza-ari (+2), Ippon (+3) fun abanidije pupa tabi bulu. Awon aami n ṣe imudojuiwọn ni igba gidi.',
                    'Ṣakoso awon ijiya : Te Ijiya lati fun ikilọ (Shido) tabi iyọkuro (Hansoku). Awon ijiya n ṣajọpọ.',
                    'Pari ija naa : Asiko n duro laifowoi. Fidi abajade mulẹ (iṣẹgun nipasẹ aami, Ippon, fifunni). Ipo n ṣe imudojuiwọn lesekese.',
                ],
                'tip_yo': 'Atọka naa ti ni ilọsiwaju fun awon tabulẹti ni ipo yikaka. Awon bọtini jẹ nla ni imomose fun lilo iyara ati aisi aṣiṣe.',
            },
            5: {
                'title_yo': 'Ipo Kiosiki pupọ-tatami',
                'steps_yo': [
                    'Mu ipo Kiosiki sise : Lati Iseto > Ipo Kiosiki, mu ipo naa sise ki o seto koodu PIN fun agbegbe ija kookan.',
                    'Seto tabulẹti kookan : Lori tabulẹti agbegbe kookan, wole ki o yan agbegbe ti o bamu. Fi PIN sii lati tiipa iboju lori agbegbe yii.',
                    'Iṣakoso olominira : Agbegbe kookan n ṣiṣẹ ni olominira: ikun-ami, asiko, ifihan. Iwe-aami aarin n ṣe imudojuiwọn ni igba gidi.',
                    'Iboju awon oluwoye : So iboju afikun ni ipo \'Oluwoye\' lati fihan ikun-ami ni iwọn nla, ti o han lati awon ijoko.',
                ],
                'tip_yo': 'Ipo Kiosiki n dena awon adajo lati lilọ kuro ninu atọka ikun-ami lairotẹlẹ.',
            },
            6: {
                'title_yo': 'Tẹle awon ipo ni igba gidi',
                'steps_yo': [
                    'Paneeli ni igba gidi : Iboju itẹle n fihan ni igba gidi: awon ija ti n lọ fun agbegbe kookan, awon ipo ẹgbẹ idije, ilọsiwaju si awon ipele ikẹhin.',
                    'Sẹ nipasẹ eka : Yan eka kan lati wo awon alaye: awon ẹgbẹ idije ti o ti pari, ti n lọ ati ti o ku, pelu awon ipo igba die.',
                    'Awon iwifunni aifowoi : Eto naa n firanṣẹ iwifunni si awon olukoni laifowoi nigba ti awon abanidije wọn gbọdọ wa si agbegbe ija.',
                ],
                'tip_yo': 'Ṣe afihan paneeli naa lori iboju nla ni agbegbe igbawọle ki gbogbo awon olukopa le tẹle ilọsiwaju naa.',
            },
            7: {
                'title_yo': 'Ṣe awon ipele ikẹhin (idaji-ikẹhin/ikẹhin)',
                'steps_yo': [
                    'Awon ẹgbẹ idije ti o ti pari : Ti gbogbo awon ẹgbẹ idije ti eka kan ba ti pari, eto naa n ṣe iṣiro awon ti o yẹ gege bi awon ofin ti a ṣalaye (akọkọ ati ekeji fun ẹgbẹ idije kookan, ati bee bee lo).',
                    'Ṣe tabili naa : Te \'Ṣe awon ipele ikẹhin\'. Tabili imukuro (idamẹrin, idaji-ikẹhin, ikẹhin, ikẹhin fun idẹ) ni a ṣe laifowoi.',
                    'Ṣakoso pada-yẹwo : Ti awon ofin ba ṣalaye rẹ, awon pada-yẹwo ni a ṣe laifowoi pelu awon ti o padanu ni idaji-ikẹhin.',
                    'Bere awon ikẹhin : Awon ija ti awon ipele ikẹhin n han ninu eto naa. Ikun-ami n ṣiṣẹ bakanna bi fun awon ẹgbẹ idije.',
                ],
                'tip_yo': 'Tabili imukuro ni a ṣe laifowoi ti o n yago fun, ti o ba ṣee ṣe, awon ija laarin awon abanidije lati egbe kanna.',
            },
            8: {
                'title_yo': 'Ṣakoso ayẹyẹ podium',
                'steps_yo': [
                    'Wole si podium : Lati eka ti o ti pari, te \'Podium\'. Ipo ikẹhin n han: Wura, Fadaka, Idẹ (ati o ṣee ṣe Idẹ meji).',
                    'Ifihan diẹdiẹ : Lo ipo \'Ayẹyẹ\' fun ifihan diẹdiẹ: ipo kẹta, lẹhinna ekeji, lẹhinna akọkọ, pelu awon iṣẹgun ati awon ohun.',
                    'Ṣe afihan lori iboju nla : So ipo Afihan si projẹkito fun ifihan iyalẹnu lakoko fifun awon ami-eye.',
                    'Pin awon abajade : Awon podium ni a gbejade laifowoi lori oju-iwe idije ati pe a le pin si awon neetiwoki awujo.',
                ],
                'tip_yo': 'Ya aworan podium naa ki o fi kun si idije naa lati ṣe oke ile-aworan ati awon neetiwoki awujo.',
            },
        },
    },

    # =========================================================================
    # Abala 6: Ikun-ami Ilana (awon ikoni 6)
    # =========================================================================
    6: {
        'title_yo': 'Ikun-ami Ilana',
        'tutorials': {
            1: {
                'title_yo': 'Seto awon ilana ikun-ami',
                'steps_yo': [
                    'Wole si awon ilana : Lati idije naa, lọ si Ikun-ami > Awon ilana. Yan awoṣe kan tabi ṣe awon ilana tirẹ.',
                    'Ṣalaye awon ilana : Fi awon ilana iṣayẹwo kun: Ilana (awon ipo, awon iyipada), Agbara (kime, agbara), Lu-ṣiṣe (akoko, ṣiṣan), Ikosile (zanshin, ẹmi).',
                    'Fi awon iwuwo sii : Ṣalaye iwuwo ilana kookan: b.a. Ilana 40%, Agbara 25%, Lu-ṣiṣe 20%, Ikosile 15%. Apapọ gbọdọ jẹ 100%.',
                    'Ṣalaye iwọn naa : Yan iwọn ikun-ami: 1-5, 1-10, 5.0-10.0 tabi ti adani. Ṣalaye igbesoke (0.1, 0.5 tabi 1).',
                ],
                'tip_yo': 'Awon awoṣe WKF ati WTF ti ṣeto tẹlẹ. Ṣe wọn ni adani gege bi awon iwulo pataki re.',
            },
            2: {
                'title_yo': 'Fi awon adajo si awon eka',
                'steps_yo': [
                    'Si paneeli ifiṣi : Lati Ikun-ami > Awon adajo, wo atokọ awon adajo ti a forukosile ati awon eka ti o nilo.',
                    'Fi sii nipasẹ eka : Fa awon adajo si awon eka. Ṣalaye nọmba awon adajo fun eka kookan (nigbagbogbo 5 tabi 7).',
                    'Ayẹwo didoju : MartialComp n ṣayẹwo awon rogbodiyan anfani laifowoi: adajo kan ko le ṣe ayẹwo abanidije lati egbe tirẹ.',
                    'Ṣakoso awon yiyi-pada : Gbero awon yiyi-pada adajo laarin awon eka lati dena aarẹ ati daabobo idogba.',
                ],
                'tip_yo': 'Eto wiwa aibikita n ṣe itupalẹ awon iyatọ ikun-ami laarin awon adajo ati n kilọ ti adajo kan ba n fun ni ikun-ami giga tabi kekere ju nigbagbogbo.',
            },
            3: {
                'title_yo': 'Lo iwe ikun-ami ilana',
                'steps_yo': [
                    'Wole bi adajo : Lori tabulẹti re, wole pelu akounti adajo re. Yan eka ti a fi le ọ lọwọ.',
                    'Atọka ikun-ami : Iboju n fihan abanidije lowe, awon ilana iṣayẹwo ati pada nọmba. Ilana kookan ni isunmi tirẹ tabi pada.',
                    'Ṣe ayẹwo ni ipa kookan : Fun abanidije kookan, fi ikun-ami re sii fun ilana kookan. Fidi ayẹwo re mulẹ ṣaaju ki o to kọja si ti o tẹle.',
                    'Fipamọ : Ayẹwo re ti wa ni fipamọ lesekese. O le yi awon ikun-ami re pada nigba ti oluṣeto ko ba ti tiipa ipa naa.',
                ],
                'tip_yo': 'Atọka oni-nọmba ti ni ilọsiwaju fun titẹ sii iyara lori awon tabulẹti. Itẹ kan fun ikun-ami kookan.',
            },
            4: {
                'title_yo': 'Ikun-ami ilana ẹgbẹ (Amuṣiṣẹpọ)',
                'steps_yo': [
                    'Loye ipo ẹgbẹ : Ninu ikun-ami Amuṣiṣẹpọ, awon ilana afikun n han: Imuṣiṣẹpọ, Ititọ Aaye, Ikosile Apapọ.',
                    'Ṣe ayẹwo ẹgbẹ naa papọ : Ti o ba ṣeto bẹ, ṣe ayẹwo ẹgbẹ naa papọ fun ilana kookan, pẹlu imuṣiṣẹpọ.',
                    'Ṣe ayẹwo lọkọọkan + ẹgbẹ : Ti o ba ṣeto fun ayẹwo adapọ, ṣe ayẹwo omo egbe kookan lọkọọkan ati LẸHINNA fi ikun-ami ẹgbẹ kan fun imuṣiṣẹpọ.',
                ],
                'tip_yo': 'Ni ipo Amuṣiṣẹpọ, ilana imuṣiṣẹpọ maa n jẹ 20-30% ti ikun-ami lapapọ.',
            },
            5: {
                'title_yo': 'Tiipa ati gbejade awon ikun-ami',
                'steps_yo': [
                    'Ṣayẹwo awon ikun-ami : Lati paneeli oluṣeto, wo awon ikun-ami gbogbo awon adajo fun abanidije kookan. Ṣe idanimọ awon iyatọ ifura.',
                    'Tiipa ipa kan : Te \'Tiipa\' lati dena ayipada eyikeyi. Iṣiro ikẹhin (yọ ikun-ami ti o ga julọ/ti o kere julọ, aropin) ni a ṣe.',
                    'Gbejade awon abajade : Gbejade awon ipo. Awon ikun-ami alaye nipasẹ adajo le pamọ tabi han gege bi iseto re.',
                    'Ipo idanwo / tun bere : Ṣaaju idije naa, lo ipo idanwo lati ṣayẹwo eto naa. Titun-bere n pa gbogbo awon ikun-ami idanwo rẹ.',
                ],
                'tip_yo': 'Tiipa ipa nipasẹ ipa n gba ọ laaye lati gbejade awon abajade ipa nipasẹ ipa nigba ti idije n tẹsiwaju.',
            },
            6: {
                'title_yo': 'Wo awon ipo igba die',
                'steps_yo': [
                    'Wole si awon ipo : Lati taabu Awon ipo, wo awon ipo ni igba gidi pelu awon ikun-ami nipasẹ ilana ati ikun-ami ikẹhin.',
                    'Ṣeto ati sẹ : Ṣeto nipasẹ ikun-ami lapapọ tabi nipasẹ ilana pato. Sẹ nipasẹ ẹgbẹ idije tabi gbogbo awon abanidije.',
                    'Awon iṣiro awon adajo : Wo awon iṣiro: aropin fun adajo kookan, iyatọ boṣewa, wiwa aibikita. Irinṣe pataki fun idogba.',
                ],
                'tip_yo': 'Ipo igba die nikan han fun awon oluṣeto ati awon adajo. A gbejade rẹ si awon abanidije nikan lẹhin tiipa.',
            },
        },
    },

    # =========================================================================
    # Abala 7: Awon Abajade ati Itan Aṣeyọri (awon ikoni 4)
    # =========================================================================
    7: {
        'title_yo': 'Awon Abajade ati Itan Aṣeyọri',
        'tutorials': {
            1: {
                'title_yo': 'Wo awon abajade idije',
                'steps_yo': [
                    'Wa idije naa : Lati awo Awon idije tabi oju-iwe gbangba, yan idije ti o fẹ.',
                    'Ṣayẹwo awon abajade : Awon abajade ti ṣeto nipasẹ eka. Fun eka kookan: podium, ipo kikun ati awon alaye ikun-ami.',
                    'Awon alaye ija : Te ija kan lati wo awon alaye: ikun-ami fun iyipo kookan, awon ijiya, asiko ati boya fidio ija naa.',
                ],
                'tip_yo': 'Awon abajade gbangba le wọle si laisi akounti MartialComp nipasẹ asepo idije naa.',
            },
            2: {
                'title_yo': 'Gbejade ati pin awon abajade',
                'steps_yo': [
                    'Fidi awon abajade mulẹ : Lati paneeli oluṣeto, ṣayẹwo awon abajade eka kookan. Te \'Fidi mulẹ ki o gbejade\'.',
                    'Ṣe asepo gbangba : A ṣe asepo ayeraye si oju-iwe awon abajade. Daako rẹ lati pin.',
                    'Pin si awon neetiwoki awujo : Lo awon bọtini pinpin ti o wa ninu lati fi si Facebook, Instagram, Twitter. Awon podium n ṣe aworan laifowoi.',
                    'Koodu QR awon abajade : Ṣe koodu QR awon abajade lati fi han ni ibi idije fun awon oluwoye.',
                ],
                'tip_yo': 'Aworan podium aifowoi ti ṣeto fun Instagram Stories (9:16) ati Facebook (16:9).',
            },
            3: {
                'title_yo': 'Gbe awon abajade jade (CSV/PDF)',
                'steps_yo': [
                    'Wole si gbigbe jade : Lati Awon abajade > Gbe jade, yan ọna: CSV (data aise), PDF (ijabọ ti a ṣeto) tabi Excel.',
                    'Yan akoonu : Yan: Ipo gbogbogbo, Awon podium nikan, Alaye nipasẹ eka, Ijabọ ami-eye nipasẹ egbe tabi Gbogbo.',
                    'Ṣe PDF ni adani : Fun PDF, yan awoṣe: ijabọ osise (pelu aami ajosepo), ijabọ irọrun tabi awon iwe-ẹri.',
                ],
                'tip_yo': 'Ijabọ ami-eye nipasẹ egbe wulo pupọ fun awon ajosepo ati awon onigbọwọ.',
            },
            4: {
                'title_yo': 'Ṣayẹwo itan aṣeyọri tirẹ',
                'steps_yo': [
                    'Wole si Itan aṣeyọri mi : Lati profaili olukopa re, te \'Itan aṣeyọri\'. Itan awon idije re n han.',
                    'Wo awon iṣiro : Ṣayẹwo: nọmba awon idije, awon ami-eye (wura/fadaka/idẹ), ida-ogorun iṣẹgun, ilọsiwaju ni akoko.',
                    'Pin itan aṣeyọri re : Ṣe asepo gbangba si itan aṣeyọri re tabi gbe jade ni PDF fun awon foomu ibeere tabi igbọwọ.',
                ],
                'tip_yo': 'Itan aṣeyọri re n ṣe imudojuiwọn laifowoi lẹhin idije kookan. O han lori profaili gbangba re ti o ba gba laaye.',
            },
        },
    },

    # =========================================================================
    # Abala 8: Iṣakoso Awon Ipele (awon ikoni 5)
    # =========================================================================
    8: {
        'title_yo': 'Iṣakoso Awon Ipele',
        'tutorials': {
            1: {
                'title_yo': 'Seto eto awon ipele',
                'steps_yo': [
                    'Wole si iseto : Lati Iseto > Awon ipele, yan eko-ija ki o ṣalaye eto awon ipele re.',
                    'Ṣe awon ipele : Fi awon ipele kun ni aṣẹ: Igbanu funfun, Ofeefee, Ọsan, Alawọ ewe, Bulu, Awo-dudu, Dudu Dan akọkọ, Dan keji, ati bee bee lo.',
                    'Ṣalaye awon iwulo ṣaaju : Fun ipele kookan, ṣalaye: akoko to kere ni ipele ṣaaju, ojo ori to kere, nọmba kilasi to kere, boya a nilo idanwo.',
                    'Fi awon awọ sii : Fi awon awọ igbanu sii fun ifihan ninu atọka ati awon profaili.',
                ],
                'tip_yo': 'Awon eto ipele boṣewa (Judo, Karate, TKD, BJJ) ti ṣeto tẹlẹ. O le ṣe wọn ni adani tabi ṣe tuntun.',
            },
            2: {
                'title_yo': 'Fi ipele kan fun olukopa kan',
                'steps_yo': [
                    'Wole si kaadi naa : Lati kaadi olukopa naa, te taabu Awon ipele lẹhinna \'Fi ipele tuntun kan\'.',
                    'Yan ipele naa : Yan ipele naa lati atokọ. Eto naa n ṣayẹwo awon iwulo ṣaaju laifowoi (akoko, ojo ori, awon idanwo).',
                    'Fi awon alaye sii : Fi ojo ifiṣi, ibi, adajọ/oluyẹwo ati awon akiyesi sii.',
                    'Ifiṣi pupọ : Lati Awon ipele > Ifiṣi pupọ, yan awon olukopa pupọ ki o fi ipele kanna fun gbogbo wọn.',
                ],
                'tip_yo': 'Imeeli ikini ni a fi ranṣẹ si olukopa laifowoi pelu ipele tuntun rẹ.',
            },
            3: {
                'title_yo': 'Ṣeto idanwo ipele',
                'steps_yo': [
                    'Ṣe idanwo naa : Lati Awon ipele > Awon idanwo, ṣe idanwo tuntun: ojo, ibi, eko-ija, awon ipele ti o bo, awon adajọ.',
                    'Forukosile awon oludije : Fi awon oludije kun pelu owo tabi gba iforukosile ara-eni. Eto naa n ṣayẹwo awon iwulo ṣaaju olukuluku.',
                    'Ni ojo idanwo : Lo atọka idanwo lati ṣe ayẹwo oludije kookan: awon ilana ti a nilo, ija, eko.',
                    'Gbejade awon abajade : Fidi awon ti o kọja ati awon ti ko kọja. Awon ipele ni a fi fun awon oludije ti o kọja laifowoi.',
                ],
                'tip_yo': 'Awon idanwo ipele le sopọ si idije kan (b.a. igbesoke ipele lakoko idannamọ).',
            },
            4: {
                'title_yo': 'Ṣakoso itan ati ilọsiwaju awon ipele',
                'steps_yo': [
                    'Wo itan naa : Kaadi olukopa kookan n fihan itan ipele kikun: ojo, ibi, adajọ, awon akiyesi.',
                    'Ṣe afihan ilọsiwaju : Aworan n fihan ilọsiwaju ni akoko. Ṣe afiwe pelu aropin egbe naa.',
                    'Fagile ipele kan : Ninu ipo aṣiṣe, fagile ipele kan pelu idi. Itan naa n pa igbasilẹ ti fagile naa mọ.',
                ],
                'tip_yo': 'Itan awon ipele le gbe lọ ti olukopa ba yi egbe pada.',
            },
            5: {
                'title_yo': 'Ṣe awon iwe-ẹri ipele',
                'steps_yo': [
                    'Wole si awon iwe-ẹri : Lati Awon ipele > Awon iwe-ẹri, yan olukopa ati ipele fun eyiti o fẹ ṣe iwe-ẹri.',
                    'Yan awoṣe : Yan awoṣe iwe-ẹri: osise (pelu aami ajosepo), egbe tabi ti adani.',
                    'Ṣe ni adani : Fi awon ibuwọlu, edidi egbe ati awon alaye pataki kun. Koodu QR ayẹwo ni a fi kun laifowoi.',
                    'Ṣe ki o pin : Ṣe PDF naa. Tẹ sita tabi fi ranṣẹ nipasẹ imeeli. Koodu QR n gba ẹnikẹni laaye lati ṣayẹwo ododo iwe-ẹri naa.',
                ],
                'tip_yo': 'Koodu QR ayẹwo n darí si oju-iwe gbangba MartialComp ti o jeri ododo ipele naa.',
            },
        },
    },

    # =========================================================================
    # Abala 9: Iṣakoso Ajosepo (awon ikoni 8)
    # =========================================================================
    9: {
        'title_yo': 'Iṣakoso Ajosepo',
        'tutorials': {
            1: {
                'title_yo': 'Ṣakoso awon egbe ti o darapo',
                'steps_yo': [
                    'Iwoye gbogbogbo : Paneeli ajosepo n fihan maapu awon egbe ti o darapo, ipo wọn (lowo, nduro, ti pari) ati awon iṣiro.',
                    'Ṣe awon ibeere : Awon ibeere idapọ tuntun n han ni Awon egbe > Nduro. Ṣayẹwo awon iwe-ẹri ki o fọwọsi tabi kọ.',
                    'Tẹle awon atunṣe : Wo awon idapọ ti o fẹrẹ pari. Fi awon iranti aifowoi ranṣẹ ni ọjọ 30, 15 ati 7 ṣaaju.',
                ],
                'tip_yo': 'Paneeli ajosepo n pese iwoye ni igba gidi ti nọmba lapapọ awon olukopa ti o ni iwe-ase ni gbogbo awon egbe.',
            },
            2: {
                'title_yo': 'Ṣakoso awon akoko ati awon owo-oṣe',
                'steps_yo': [
                    'Ṣe akoko kan : Lati Awon akoko > Tuntun, ṣalaye awon ojo ibere ati ipari ati awon owo owo-oṣe fun iru kookan (egbe, olukopa, ọdọ, agbalagba).',
                    'Seto awon owo-oṣe : Ṣalaye awon iye fun eka kookan: idapọ egbe (titi), iwe-ase olukopa (fun olukopa kookan), iṣeduro (yan).',
                    'Tẹle awon isanwo : Wo awon owo-oṣe ti a gba, ti o ku ati ti o pẹ ni igba gidi. Fi awon iranti aifowoi ranṣẹ.',
                    'Tiipa akoko naa : Ni opin akoko, tiipa rẹ lati ṣe ijabọ inawo ki o mura fun akoko ti o tẹle.',
                ],
                'tip_yo': 'Awon owo-oṣe le san lori ayelujara nipasẹ Stripe tabi nipasẹ gbigbe owo. Itẹle jẹ laifowoi ninu awon ipo mejeeji.',
            },
            3: {
                'title_yo': 'Ṣe abojuto awon idije',
                'steps_yo': [
                    'Iwoye gbogbogbo : Kalenda ajosepo n fihan gbogbo awon idije ti awon egbe ti o darapo, pelu ipo ati nọmba awon olukopa.',
                    'Fọwọsi idije kan : Awon egbe n fi awon idije wọn ranṣẹ fun ifọwọsi. Ṣayẹwo awon ofin, awon adajo ki o fidi rẹ mulẹ.',
                    'Wo awon abajade : Wole si awon abajade gbogbo awon idije ti a fọwọsi. Awon ipo orilẹ-ede n ṣe imudojuiwọn laifowoi.',
                ],
                'tip_yo': 'Awon idije ti ajosepo fọwọsi ni a ṣe afihan ninu iwe-itọsọna ati kalenda gbangba.',
            },
            4: {
                'title_yo': 'Ṣakoso awon adajo ati awon iwe-eri wọn',
                'steps_yo': [
                    'Ipilẹ data awon adajo : Wo ipilẹ data awon adajo ti o darapo pelu awon iwe-eri wọn, awon amojuto ati itan iṣẹ wọn.',
                    'Ṣakoso awon ipele : Fi awon ipele iwe-eri sii: agbegbe, orilẹ-ede, agbaye. Ṣalaye awon ilana igbesoke.',
                    'Itẹle didoju : MartialComp n ṣe itupalẹ awon iṣiro ikun-ami adajo kookan ati n ṣe awari awon aibikita ti o le jẹ.',
                ],
                'tip_yo': 'Awon adajo ti o ni itan ikun-ami ti o dogba ni a ṣe afihan fun awon idije pataki.',
            },
            5: {
                'title_yo': 'Ṣakoso awon iwe-eri',
                'steps_yo': [
                    'Ṣe awoṣe kan : Ṣe apẹrẹ awon awoṣe iwe-eri re pelu aami ajosepo, awon alaye ofin ati awon aaye agbara.',
                    'Fun awon iwe-eri jade : Ṣe awon iwe-eri fun: awon ipele, awon iwe-eri adajo, awon iwe-ẹri ikẹkọọ, awon ijeri oriṣiriṣi.',
                    'Ayẹwo gbangba : Iwe-eri kookan ni koodu QR alailẹgbẹ kan. Ẹnikẹni le ṣayẹwo rẹ lati jeri ododo lori martialcomp.com.',
                ],
                'tip_yo': 'Awon iwe-eri oni-nọmba ko le yi pada nitori koodu QR ayẹwo ti o sopọ si MartialComp.',
            },
            6: {
                'title_yo': 'Ṣe aaye ayelujara gbangba ajosepo ni adani',
                'steps_yo': [
                    'Wole si olukọ aaye : Lati Iseto > Aaye gbangba, ṣi olutunṣe oju-iwe. Ajosepo re ni URL: ajosepo.martialcomp.com.',
                    'Ṣe irisi ni adani : Yan awon awọ, akori, asia ati aami. Fi apejuwe ati awon asepo si awon neetiwoki awujo re kun.',
                    'Fi akoonu kun : Gbejade awon iroyin, awon ile-aworan aworan, awon fidio, kalenda awon idije ati awon iwe ti a le se igbawo.',
                    'Ṣakoso awon oju-iwe : Ṣe awon oju-iwe afikun: Itan, Awon Olori, Ofin, Ibasoro.',
                ],
                'tip_yo': 'Aaye ayelujara gbangba ti ni ilọsiwaju fun SEO. Bi o ṣe pe to, bẹẹ ni o ṣe dara si lori Google.',
            },
            7: {
                'title_yo': 'Wo awon iṣiro ati awon ijabọ',
                'steps_yo': [
                    'Paneeli itupalẹ : Paneeli naa n fihan awon KPI: nọmba awon egbe, awon olukopa, awon idije, awon iwe-ase lowo, idagba.',
                    'Awon ijabọ nipasẹ egbe : Ṣe awon ijabọ alaye nipasẹ egbe: nọmba awon omo egbe, awon owo-oṣe, ikopa ninu awon idije, awon ipele ti a fun.',
                    'Awon ijabọ nipasẹ eko-ija : Ṣe itupalẹ pinpin nipasẹ eko-ija, ojo ori, abo. Ṣe idanimọ awon aṣa idagba.',
                    'Gbe jade ki o pin : Gbe awon ijabọ jade ni PDF, Excel tabi CSV fun awon apejọ gbogbogbo ati awon ijabọ osise re.',
                ],
                'tip_yo': 'Awon ijabọ n ṣe imudojuiwọn ni igba gidi. Ṣeto fifiranṣẹ aifowoi oṣooṣu tabi ni oṣu mẹta.',
            },
            8: {
                'title_yo': 'Ṣakoso awon eto ikẹkọọ',
                'steps_yo': [
                    'Ṣe eto kan : Lati Ikẹkọọ > Tuntun, ṣalaye eto naa: akole, eko-ija, ipele, iye akoko, awon iwulo ṣaaju.',
                    'Gbero awon igba : Fi awon igba ikẹkọọ kun: awon ojo, awon ibi, awon olukọ, nọmba awon aye.',
                    'Ṣakoso awon iforukosile : Awon olukoni ati awon adajo n forukosile lori ayelujara. Fidi awon iforukosile mulẹ ki o fi awon ipe-ijo ranṣẹ.',
                    'Itẹle ati iwe-eri : Tẹle wiwa si awon igba. Fun awon iwe-eri jade si awon olukopa ti o pari eto naa.',
                ],
                'tip_yo': 'Awon eto ikẹkọọ ti o pari n han laifowoi ninu awon profaili awon olukoni ati awon adajo.',
            },
        },
    },

    # =========================================================================
    # Abala 10: Inawo (awon ikoni 5)
    # =========================================================================
    10: {
        'title_yo': 'Inawo',
        'tutorials': {
            1: {
                'title_yo': 'Tẹle awon idunadura egbe',
                'steps_yo': [
                    'Iwoye gbogbogbo : Paneeli inawo n fihan: iye owo, owo-wole oṣu, inawo ati aworan aṣa.',
                    'Forukosile idunadura kan : Fi owo-wole tabi inawo kun: iye, ojo, eka (awon owo-oṣe, ohun elo, iyalo), apejuwe.',
                    'Ṣiṣeto aifowoi : MartialComp n ṣeto awon idunadura ti o n tun ṣe laifowoi. Ṣe awon eka ni adani gege bi awon iwulo re.',
                ],
                'tip_yo': 'So akounti banki re lati gbe awon idunadura wole laifowoi ki o mu ilaja rọrun.',
            },
            2: {
                'title_yo': 'Ṣe ati fi awon iwe-owo ranṣẹ',
                'steps_yo': [
                    'Ṣe iwe-owo kan : Lati Inawo > Awon iwe-owo > Tuntun, yan olugba (olukopa, egbe, onigbọwọ) ati awon ila owo.',
                    'Ṣe ni adani : Fi aami re, awon akiyesi ofin, awon ipo isanwo kun. Yan owo ati oṣuwọn owo-ori.',
                    'Fi ranṣẹ : Fi iwe-owo ranṣẹ nipasẹ imeeli. Olugba n gba asepo isanwo lori ayelujara (Stripe) ati iwe-owo ni PDF.',
                    'Tẹle awon isanwo : Wo awon iwe-owo ti a san, ti o ku ati ti o pẹ. Fi awon iranti aifowoi ranṣẹ.',
                ],
                'tip_yo': 'Awon owo-oṣe awon olukopa n ṣe awon iwe-owo laifowoi ti o ba mu asayan yii sise.',
            },
            3: {
                'title_yo': 'Ṣakoso awon isanwo lori ayelujara (Stripe)',
                'steps_yo': [
                    'So Stripe po : Lati Iseto > Awon isanwo, te \'So Stripe po\'. Tẹle awon igbese lati so akounti Stripe re po.',
                    'Seto aye isanwo : Seto awon owo fun: awon owo-oṣe, awon iforukosile idije, ile-itaja. Mu awon isanwo atetete sise ti o ba nilo.',
                    'Dan isanwo wo : Lo ipo idanwo Stripe lati ṣayẹwo pe ohun gbogbo n ṣiṣẹ ṣaaju ki o to mu awon isanwo gidi sise.',
                    'Tẹle awon owo-wole : Paneeli Stripe ninu MartialComp n fihan awon isanwo ti a gba, awon isanpadabọ ati awon gbigbe si akounti banki re.',
                ],
                'tip_yo': 'Stripe n gba owo-iṣẹ 1.4% + \u20ac0.25 fun idunadura kookan ni Yuroopu. Awon owo ni a gbe lọ ni ọjọ 2-7.',
            },
            4: {
                'title_yo': 'Gbe alaye banki wole',
                'steps_yo': [
                    'Se igbawo alaye naa : Lati banki re, gbe alaye jade ni ọna CSV, OFX tabi QIF.',
                    'Gbe wole si MartialComp : Lati Inawo > Gbe wole, gbe faili naa soke. MartialComp n ṣe awari ọna naa ati ṣe mapu awon ila.',
                    'Ṣe ilaja : Eto naa n baraamu awon idunadura ti a gbe wole pelu awon iwe-owo ati awon owo-oṣe ti o wa tẹlẹ laifowoi.',
                    'Fidi rẹ mulẹ : Ṣayẹwo awon ibaamu, ṣatunṣe awon aṣiṣe ki o fidi rẹ mulẹ. Awon idunadura ti ko ni ibaamu ni a fi kun bi nduro.',
                ],
                'tip_yo': 'Gbigbe wole banki oṣooṣu n pa iwe-isiro re ni imudojuiwọn laisi titẹ sii pelu owo.',
            },
            5: {
                'title_yo': 'Ṣakoso awon owo-oṣe awon olukopa',
                'steps_yo': [
                    'Seto awon owo : Lati Inawo > Awon owo-oṣe, seto awon owo ọdọọdun fun eka kookan: ọmọde, ọdọ, agbalagba, ebi.',
                    'Fun awon ibeere isanwo jade : Ni ibere akoko, ṣe awon ibeere isanwo fun gbogbo awon omo egbe. Olukuluku n gba imeeli pelu asepo isanwo.',
                    'Tẹle awon isanwo : Wo awon owo-oṣe ti a san, ti o ku ati ti o pẹ. Ipo naa n han ninu kaadi olukopa kookan.',
                    'Fi awon iranti ranṣẹ : Ṣeto awon iranti aifowoi: ọṣẹ 1, ọṣẹ 2, oṣu 1 lẹhin ojo ipari.',
                ],
                'tip_yo': 'Awon olukopa ti o ni owo-oṣe ti o pẹ le di dina lati forukosile fun awon idije.',
            },
        },
    },

    # =========================================================================
    # Abala 11: Awon Iṣẹlẹ ati Kalenda (awon ikoni 3)
    # =========================================================================
    11: {
        'title_yo': 'Awon Iṣẹlẹ ati Kalenda',
        'tutorials': {
            1: {
                'title_yo': 'Ṣe iṣẹlẹ kan (iṣẹ ikẹkọọ, ayẹyẹ, apejọ)',
                'steps_yo': [
                    'Ṣe iṣẹlẹ naa : Lati Kalenda > Iṣẹlẹ tuntun, fi sii: iru (iṣẹ ikẹkọọ, ayẹyẹ, apejọ, ẹnu-ode ṣiṣi), akole, awon ojo, ibi ati apejuwe.',
                    'Seto awon iforukosile : Mu awon iforukosile lori ayelujara sise. Seto nọmba awon aye, owo (ọfẹ tabi isanwo) ati ojo ipari iforukosile.',
                    'Gbejade : Gbejade iṣẹlẹ naa. O n han ninu kalenda egbe ati pe a le pin si awon neetiwoki awujo.',
                ],
                'tip_yo': 'Awon iṣẹ ikẹkọọ pelu awon olukọ alejo jẹ awon irinṣe titaja ti o dara julọ. Fi aworan ati itan-akọọlẹ wọn kun lati fa awon eniyan diẹ sii.',
            },
            2: {
                'title_yo': 'Ṣakoso awon iṣẹlẹ atetete',
                'steps_yo': [
                    'Ṣe atetete : Lakoko iseda, ṣe aami \'Iṣẹlẹ atetete\'. Seto igbohunsafefe: lojoojumọ, ni ọṣẹ kookan, ni oṣu kookan.',
                    'Ṣakoso awon iyato : Fagile tabi yi apa kan pada laisi lati ni ipa lori awon miran (b.a. kilasi ti a fagile fun ojo-isinmi).',
                    'Yi jara pada : Yi gbogbo jara pada (b.a. iyipada akoko titilai) tabi apa kan nikan.',
                ],
                'tip_yo': 'Awon kilasi oṣooṣe gbọdọ ṣe bi awon iṣẹlẹ atetete lati han ninu kalenda laifowoi.',
            },
            3: {
                'title_yo': 'Tẹle awon iforukosile ati wiwa',
                'steps_yo': [
                    'Wo awon ti o forukosile : Lati iṣẹlẹ naa, wo atokọ awon ti o forukosile pelu ipo wọn: forukosile, jeri, fagile.',
                    'Forukosile wiwa : Ni ojo iṣẹlẹ naa, forukosile wiwa nipasẹ atokọ tabi koodu QR.',
                    'Gbe jade : Gbe atokọ awon olukopa jade ni CSV tabi PDF fun awon igbasilẹ re.',
                ],
                'tip_yo': 'Oṣuwọn ikopa ninu awon iṣẹlẹ jẹ afihan pataki ti ifiṣootọ awon omo egbe re.',
            },
        },
    },

    # =========================================================================
    # Abala 12: Iṣakoso Ebi (awon ikoni 3)
    # =========================================================================
    12: {
        'title_yo': 'Iṣakoso Ebi',
        'tutorials': {
            1: {
                'title_yo': 'Ṣe ẹgbẹ ebi kan',
                'steps_yo': [
                    'Wole si awon ẹgbẹ ebi : Lati profaili re, lọ si Iseto > Ẹgbẹ Ebi > Ṣe.',
                    'Fi awon omo egbe kun : Fi omo ebi kookan kun: iyawo/oko, awon ọmọ. So awon akounti MartialComp wọn ti o wa tẹlẹ po tabi ṣe tuntun.',
                    'Seto olori : Olori ẹgbẹ ebi n gba gbogbo awon iwifunni ati n ṣakoso awon isanwo fun gbogbo ebi.',
                ],
                'tip_yo': 'Awon egbe kan n funni ni awon owo ebi (ẹdinwo lati omo egbe kẹta). Ẹgbẹ ebi n mu awon ẹdinwo wọnyi sise laifowoi.',
            },
            2: {
                'title_yo': 'Forukosile gbogbo ebi fun idije kan',
                'steps_yo': [
                    'Iforukosile ẹgbẹ : Lati idije naa, te \'Forukosile ebi mi\'. Awon omo egbe ti o yẹ ninu ẹgbẹ ebi re n han.',
                    'Yan ki o jeri : Yan awon omo egbe ti o fẹ forukosile. Awon eka ni a daba laifowoi fun olukuluku.',
                    'Isanwo ẹyọkan : San fun gbogbo awon iforukosile ni idunadura kan.',
                ],
                'tip_yo': 'Iforukosile ẹgbẹ n fi akoko iyebiye pamọ nigba ti awon ọmọ pupọ ba n kopa ninu idije kanna.',
            },
            3: {
                'title_yo': 'Ile-iṣẹ isanwo ebi',
                'steps_yo': [
                    'Iwoye gbogbogbo : Ile-iṣẹ ebi n fihan gbogbo awon owo-oṣe, awon iforukosile ati awon iwe-owo ebi lori iboju kan.',
                    'Isanwo papọ : Ṣajọ awon isanwo pupọ ti o ku ki o san ni idunadura kan.',
                    'Itan : Wo itan isanwo kikun ti ebi pelu awon iwe-ẹri ti a le se igbawo.',
                ],
                'tip_yo': 'Mu gbigba owo taara aifowoi sise lati ma gbagbe owo-oṣe rara.',
            },
        },
    },

    # =========================================================================
    # Abala 13: Iṣakoso Iṣẹ (Kanban) (awon ikoni 2)
    # =========================================================================
    13: {
        'title_yo': 'Iṣakoso Iṣẹ (Kanban)',
        'tutorials': {
            1: {
                'title_yo': 'Lo paneeli Kanban',
                'steps_yo': [
                    'Ṣe paneeli kan : Lati Awon irinṣe > Kanban, ṣe paneeli tuntun: oruko, apejuwe ati awon omo egbe ti a pe.',
                    'Fi awon ila kun : Ṣe awon ila iṣe re: Lati ṣe, N ṣe, Nduro, Ti pari. Ṣe awon oruko ati awon awọ ni adani.',
                    'Ṣe awon iṣẹ : Fi awon iṣẹ kun pelu: akole, apejuwe, ojo ipari, eni ti o ni ojuṣe, pataki (giga/aarin/kekere) ati awon aami.',
                    'Ṣakoso nipa fifa-si-ati-jiju : Gbe awon iṣẹ laarin awon ila nipa fifa wọn. Itan awon gbigbe ni a pamọ.',
                ],
                'tip_yo': 'Ṣe paneeli ti a ṣe ni adani fun idije kookan ti o fẹ ṣeto. Awon iṣẹ boṣewa (yago fun ibi, beere fun awon ami-eye, ati bee bee lo) le gbe wole lati awoṣe.',
            },
            2: {
                'title_yo': 'Ṣakoso awon iṣẹ iṣeto',
                'steps_yo': [
                    'Awoṣe idije : Lo awoṣe \'Iṣeto Idije\' ti o ni awon iṣẹ boṣewa: ohun elo, ibaraẹnisọrọ, awon adajo, awon ami-eye, ati bee bee lo.',
                    'Fi sii fun awon omo egbe : Fi iṣẹ kookan fun omo egbe ẹgbẹ iṣeto. Seto awon ojo ipari.',
                    'Tẹle ilọsiwaju : Ida-ogorun ilọsiwaju gbogbogbo n han ni oke paneeli naa. Awon iṣẹ ti o pẹ ni a ṣe afihan ni pupa.',
                ],
                'tip_yo': 'Paneeli Kanban le wole si lati app alagbeka lati mu awon iṣẹ ṣe ni irin-ajo.',
            },
        },
    },

    # =========================================================================
    # Abala 14: Ile-itaja Lori Ayelujara (awon ikoni 2)
    # =========================================================================
    14: {
        'title_yo': 'Ile-itaja Lori Ayelujara',
        'tutorials': {
            1: {
                'title_yo': 'Seto ile-itaja egbe naa',
                'steps_yo': [
                    'Mu ile-itaja sise : Lati Iseto > Ile-itaja, mu iṣẹ iṣowo ori ayelujara sise. So akounti Stripe re po ti o ko ba ti ṣe tẹlẹ.',
                    'Fi awon oja kun : Ṣe awon oja re: oruko, apejuwe, awon aworan, owo, awon iwọn/iyatọ ti o wa, oja ti o ku.',
                    'Ṣeto nipasẹ eka : Pin awon oja re: Awon aṣọ (kimono, dobok, ibọwọ), Ohun elo (aabo, apo), Awon nkan (awon igbanu, awon ami), Oja titaja.',
                    'Gbejade ile-itaja : Ile-itaja re le wole si lati oju-iwe gbangba ti egbe re. Pin asepo tabi koodu QR.',
                ],
                'tip_yo': 'Funni ni awon akojọ (kimono + igbanu + apo) pelu ẹdinwo lati mu iye owo ti a ra lọ soke.',
            },
            2: {
                'title_yo': 'Ṣe aṣẹ kan',
                'steps_yo': [
                    'Wo ile-itaja naa : Lati oju-iwe egbe re, wole si ile-itaja. Wo awon oja nipasẹ eka.',
                    'Fi si agbọn : Yan iwọn/iyatọ ki o fi si agbọn. Agbọn naa n duro laarin awon igba.',
                    'Ṣe aṣẹ ki o san : Jeri agbọn re, yan ọna ifijiṣẹ (gbigba ni dojo tabi fifiranṣẹ nipasẹ ifiweranṣẹ) ki o san lori ayelujara.',
                    'Tẹle aṣẹ naa : Gba awon iwifunni ni igbese kookan: aṣẹ ti a jeri, n mura, ṣetan fun gbigba / ti a firanṣẹ.',
                ],
                'tip_yo': 'Ipo \'Gbigba ni Dojo\' n yago fun awon owo ifijiṣẹ. Olukoni yoo fun o ni aṣẹ re ni kilasi ti o tẹle.',
            },
        },
    },

    # =========================================================================
    # Abala 15: Awon Iṣẹ Ilọsiwaju (awon ikoni 5)
    # =========================================================================
    15: {
        'title_yo': 'Awon Iṣẹ Ilọsiwaju',
        'tutorials': {
            1: {
                'title_yo': 'Seto igbohunsafefe idije',
                'steps_yo': [
                    'Mura igbohunsafefe : Ṣe iṣẹlẹ ni igba gidi lori YouTube, Twitch tabi Facebook. Daako URL igbohunsafefe ati bọtini igbohunsafefe.',
                    'Seto ni MartialComp : Lati idije naa, lọ si Iseto > Igbohunsafefe. Lẹ URL ki o mu ifihan sise lori oju-iwe gbangba.',
                    'Ifihan ikun-ami : Mu ifihan MartialComp sise ti o n fihan ikun-ami ni igba gidi lori igbohunsafefe fidio. Ṣe ipo ati iru ni adani.',
                    'Bere ki o dan wo : Bere igbohunsafefe ki o ṣayẹwo pe ifihan naa n ṣiṣẹ. Awon oluwoye yoo ri ikun-ami ni igba gidi lori igbohunsafefe naa.',
                ],
                'tip_yo': 'Igbohunsafefe pelu ifihan ikun-ami MartialComp n fun irisi ọjọgbọn paapaa fun awon idije kekere.',
            },
            2: {
                'title_yo': 'Lo app alagbeka',
                'steps_yo': [
                    'Se igbawo app naa : Wa \'MartialComp\' lori Play Store (Android) tabi App Store (iOS). Fi sii ki o ṣi.',
                    'Wole : Wole pelu akounti MartialComp re ti o wa tẹlẹ. O tun le lo iraye pelu Google, Facebook tabi Apple.',
                    'Ṣe awari atọka alagbeka : App naa n funni ni: profaili, awon abajade, kalenda, awon iwifunni titari, koodu QR ti ara eni ati iforukosile fun awon idije.',
                    'Ipo laisi asopọ : Awon data pataki (profaili, ipele, iwe-ase) wa laisi asopọ. Imuṣiṣẹpọ aifowoi nigba ti o ba pada si asopọ.',
                ],
                'tip_yo': 'Mu awon iwifunni titari sise lati gba awon itaniji abajade ni igba gidi lakoko awon idije.',
            },
            3: {
                'title_yo': 'Yi ipa pada ninu app',
                'steps_yo': [
                    'Wole si ayaworan ipa : Te aworan re ni oke iboju tabi fa lati osi lati si awo osi.',
                    'Yan ipa kan : Atokọ awon ipa re n han: Olukoni, Olukopa, Adajo, Olori Egbe. Te ipa ti o fẹ.',
                    'Atọka ti a mu ṣe : Dasibodu ati awo n ṣe imudojuiwọn lesekese lati ṣe afihan ipa ti a yan.',
                ],
                'tip_yo': 'O le jẹ olukoni ni egbe kan ati olukopa ni ekeji. Ipa kookan sopọ si ajọ tirẹ.',
            },
            4: {
                'title_yo': 'Agbekale/Gbigbe jade data ilọsiwaju',
                'steps_yo': [
                    'Awon ọna ti a ṣe atilẹyin : MartialComp n ṣe atilẹyin agbekale ati gbigbe jade ni CSV, Excel (XLSX), JSON ati PDF. Modulu kookan ni awon asayan tirẹ.',
                    'Agbekale pelu mapu : Atọka mapu n gba ọ laaye lati so eto faili eyikeyi po pelu awon aaye MartialComp.',
                    'Gbigbe jade ti adani : Yan awon aaye ti o fẹ gbe jade, awon asẹ ati ọna naa. Ṣeto awon gbigbe jade atetete aifowoi.',
                    'Awon iṣiṣe pupọ : Awon iṣiṣe pupọ n gba iyipada pupọ laaye ti: ipele, ẹgbẹ, ipo iforukosile, ati bee bee lo.',
                ],
                'tip_yo': 'Gbigbe jade JSON dara julọ fun isopọ pelu awon eto ẹlomiran (aaye ayelujara, app ode, CRM).',
            },
            5: {
                'title_yo': 'Ṣakoso awon adajo ad hoc (awon oluyọọda)',
                'steps_yo': [
                    'Ṣe adajo igba die : Ni ojo idije naa, lati Awon adajo > Fi oluyọọda kun, ṣe profaili igba die: oruko, egbe ati amojuto.',
                    'Fi PIN kan : PIN alailẹgbẹ ni a ṣe laifowoi. Oluyọọda naa lo PIN yii lati wole si atọka ikun-ami.',
                    'Fi si awon eka : Fi adajo oluyọọda naa si awon eka bi adajo deede. O le bere ṣiṣe ayẹwo lesekese.',
                    'Lẹhin idije : Profaili igba die ni a pamọ si ibi-ipamọ lẹhin idije. Awon ikun-ami wa ninu itan.',
                ],
                'tip_yo': 'Awon adajo ad hoc ṣe pataki fun awon idije kekere nibi ti nọmba awon adajo osise ko to.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to Yoruba (hardcoded translations)'

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

            section.title_yo = sec_data['title_yo']
            if not dry_run:
                section.save(update_fields=['title_yo'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_yo"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_yo = tut_data['title_yo']
                tutorial.steps_yo = json.dumps(tut_data['steps_yo'], ensure_ascii=False)
                tutorial.tip_yo = tut_data.get('tip_yo', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_yo', 'steps_yo', 'tip_yo'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_yo"]}')

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
