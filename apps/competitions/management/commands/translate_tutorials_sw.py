"""
Management command to translate all 81 tutorials from French to Swahili (Kiswahili).
Updates title_sw, steps_sw, and tip_sw fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_sw
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Sehemu ya 1: Kujiandikisha na Hatua za Kwanza (mafunzo 7)
    # =========================================================================
    1: {
        'title_sw': 'Kujiandikisha na Hatua za Kwanza',
        'tutorials': {
            1: {
                'title_sw': 'Kuunda akaunti yako na kuchagua jukumu lako',
                'steps_sw': [
                    'Kufikia MartialComp : Nenda kwenye martialcomp.com na ubonyeze \'Jiandikishe bure\'. Unaweza pia kupakua programu ya simu kutoka Play Store au App Store.',
                    'Kujaza fomu ya usajili : Ingiza jina lako la ukoo, jina la kwanza, barua pepe na nenosiri. Unaweza pia kujiandikisha kupitia Google, Facebook au Apple ID kwa urahisi zaidi.',
                    'Kuchagua jukumu lako kuu : Chagua jukumu lako: Msimamizi wa Klabu, Kocha, Hakimu/Refa, Mwanafunzi au Msimamizi wa Shirikisho. Chaguo hili linaamua dashibodi yako na vipengele vyako, lakini unaweza kuongeza majukumu mengine baadaye.',
                    'Kuthibitisha barua pepe yako : Angalia kisanduku chako cha barua pepe na ubonyeze kiungo cha uthibitisho. Akaunti yako imeamilishwa na unaweza kufikia dashibodi yako iliyobinafsishwa.',
                ],
                'tip_sw': 'Unaweza kuwa na majukumu mengi (mfano kocha NA mwanafunzi). Badilisha kati ya majukumu yako kutoka menyu ya pembeni wakati wowote.',
            },
            2: {
                'title_sw': 'Kuunda klabu yako',
                'steps_sw': [
                    'Kuanza msaidizi wa uundaji : Kutoka kwenye dashibodi yako, bonyeza \'Unda klabu\'. Msaidizi wa usanidi wa hatua 4 unaanza kiotomatiki.',
                    'Taarifa za jumla : Ingiza jina la klabu, kifupi, anwani kamili na maelezo ya mawasiliano (simu, barua pepe, tovuti). Ongeza nembo yako katika muundo wa PNG au JPG (ukubwa unaopendekezwa: 500x500px).',
                    'Kuchagua taaluma : Chagua taaluma moja au zaidi kati ya 14+ zinazopatikana: Karate, Judo, BJJ, Taekwondo, MMA, Kung Fu, Aikido, Kendo, Muay Thai, Ndondi, Capoeira, n.k.',
                    'Kubinafsisha kikoa kidogo chako : Chagua anwani yako ya kipekee: klabu-yako.martialcomp.com. Hii itakuwa anwani ya umma ya klabu yako, inayopatikana kwa wote.',
                    'Kusanidi chaguo : Weka saa za kufungua, ongeza maelezo na picha za dojo yako. Wezesha au lemaza usajili wa mtandaoni wa wanafunzi.',
                ],
                'tip_sw': 'Klabu yako inaundwa na mpango wa Bure (hadi wanachama 10). Vipengele vyote vinapatikana tangu mwanzo. Panda daraja hadi Premium ukizidi wanachama 10.',
            },
            3: {
                'title_sw': 'Kuunda shirikisho lako',
                'steps_sw': [
                    'Kuomba uundaji : Chagua jukumu la \'Msimamizi wa Shirikisho\' wakati wa usajili au liongeze kutoka kwenye mipangilio. Jaza fomu ya uundaji na taarifa rasmi za shirikisho lako.',
                    'Taarifa rasmi : Ingiza jina kamili, kifupi, nchi, taaluma zinazoshughulikiwa, nambari ya usajili rasmi na maelezo ya mawasiliano.',
                    'Kusanidi tovuti ya umma : Binafsisha ukurasa wako wa umma: bango, nembo, rangi, maelezo, mkusanyiko wa picha na viungo vya mitandao yako ya kijamii.',
                    'Kufafanua muundo : Sanidi ligi zako za kikanda ikiwa inatumika, fafanua aina za ushirika kwa klabu na viwango vya ada.',
                ],
                'tip_sw': 'Mashirikisho yana eneo la utawala lililopanuliwa kusimamia klabu zote zilizoshirikishwa, mashindano na daraja.',
            },
            4: {
                'title_sw': 'Kusanidi wasifu wako wa kocha',
                'steps_sw': [
                    'Kufikia wasifu wa kocha : Kutoka kwenye menyu ya pembeni, bonyeza \'Wasifu wangu wa kocha\'. Ikiwa bado huna jukumu la kocha, liongeze kutoka Mipangilio > Majukumu yangu.',
                    'Kuingiza sifa zako : Ongeza diploma zako (BPJEPS, DEJEPS, CQP, n.k.), daraja zako katika kila taaluma na miaka yako ya uzoefu.',
                    'Kufafanua taaluma zako : Chagua taaluma unazofundisha na kiwango chako cha utaalamu katika kila moja (wanaoanza, wa juu, mashindano).',
                    'Kuweka upatikanaji wako : Onyesha vipindi vyako vya kufundisha kwa wiki. Taarifa hii itaonekana kwa klabu zinazotafuta makocha.',
                ],
                'tip_sw': 'Wasifu kamili wa kocha wenye picha na vyeti huongeza kwa kiasi kikubwa kuonekana kwako kwa klabu.',
            },
            5: {
                'title_sw': 'Kusanidi wasifu wako wa hakimu',
                'steps_sw': [
                    'Kuwezesha jukumu la hakimu : Kutoka Mipangilio > Majukumu yangu, wezesha jukumu la \'Hakimu / Refa\'. Ingiza nambari yako ya leseni ya hakimu ikihitajika.',
                    'Kuongeza sifa zako : Onyesha kiwango chako cha hakimu (kikanda, kitaifa, kimataifa), taaluma unazostahili nazo na vyeti vyako.',
                    'Kufafanua utaalamu wako : Kata/mbinu, mapigano, alama za kisanaa... Kila utaalamu unakuwezesha kwa mashindano husika.',
                    'Kuingiza upatikanaji wako : Onyesha maeneo yako ya kijiografia na vipindi vya upatikanaji kwa mashindano.',
                ],
                'tip_sw': 'Waandaaji wa mashindano wanaweza kukutafuta na kukualika moja kwa moja kulingana na sifa na upatikanaji wako.',
            },
            6: {
                'title_sw': 'Kusanidi wasifu wako wa mwanafunzi',
                'steps_sw': [
                    'Kukamilisha taarifa za kibinafsi : Ingiza tarehe yako ya kuzaliwa, jinsia, uzito (kwa aina za mashindano), urefu na picha ya wasifu.',
                    'Kuongeza daraja lako la sasa : Onyesha taaluma yako kuu, daraja lako la sasa (ukanda), tarehe ya kupata na shirika lililotoa.',
                    'Kuingiza leseni yako : Ongeza nambari yako ya leseni ya shirikisho, tarehe ya kumalizika na cheti cha matibabu cha sasa.',
                    'Mawasiliano ya dharura : Ongeza angalau mwasiliano mmoja wa dharura (lazima kwa mashindano): jina, simu, uhusiano.',
                ],
                'tip_sw': 'Wasifu kamili unahitajika kujiandikisha kwa mashindano. Uzito na daraja huamua aina yako kiotomatiki.',
            },
            7: {
                'title_sw': 'Kuelewa dashibodi na urambazaji',
                'steps_sw': [
                    'Dashibodi : Dashibodi yako inaonyesha muhtasari uliobonafsishwa: matukio yajayo, ujumbe wa hivi karibuni, takwimu za haraka na njia za mkato kwa vitendo vyako vya mara kwa mara.',
                    'Upau wa pembeni : Menyu ya pembeni inatoa ufikiaji kwa sehemu zote: Wanachama, Mashindano, Daraja, Fedha, Kalenda, Mipangilio. Inajibadilisha kulingana na jukumu lako linalotumika.',
                    'Kubadilisha jukumu : Ikiwa una majukumu mengi (mfano kocha + mwanafunzi), bonyeza picha yako ya wasifu juu kulia kubadilisha. Dashibodi na menyu zinajibadilisha kiotomatiki.',
                    'Arifa na ujumbe : Ikoni ya kengele juu kulia inaonyesha arifa zako: usajili, matokeo, ujumbe. Sanidi mapendeleo yako ya arifa katika mipangilio.',
                    'Utafutaji wa jumla : Tumia upau wa utafutaji kupata haraka mwanafunzi, klabu, mashindano au tukio.',
                ],
                'tip_sw': 'Binafsisha dashibodi yako kwa kubandika wijeti unazozipenda. Njia ya mkato ya kibodi Ctrl+K inafungua utafutaji wa haraka.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 2: Usimamizi wa Klabu (mafunzo 10)
    # =========================================================================
    2: {
        'title_sw': 'Usimamizi wa Klabu',
        'tutorials': {
            1: {
                'title_sw': 'Kuongeza wanafunzi kwa mikono',
                'steps_sw': [
                    'Kufungua fomu ya usajili : Kutoka Wanachama > Ongeza mwanafunzi, jaza fomu: jina la ukoo, jina la kwanza, tarehe ya kuzaliwa, jinsia, barua pepe na simu.',
                    'Taarifa za ziada : Ongeza daraja la sasa, nambari ya leseni, picha ya kitambulisho (hiari) na cheti cha matibabu.',
                    'Kugawa kwa kundi : Mgawie mwanafunzi kwenye kundi moja au zaidi la mafunzo (mfano Karate Watu wazima wa Juu, Judo Watoto Wanaoanza).',
                    'Kutuma mwaliko : Weka alama \'Tuma barua pepe ya mwaliko\' ili mwanafunzi aweze kuunda akaunti yake mwenyewe na kufikia wasifu wake mtandaoni.',
                ],
                'tip_sw': 'Mwanafunzi atapokea barua pepe yenye kiungo cha kukamilisha usajili wake na kupakua programu ya simu.',
            },
            2: {
                'title_sw': 'Kuingiza wanafunzi kwa wingi (CSV/Excel)',
                'steps_sw': [
                    'Kupakua kiolezo : Kutoka Wanachama > Ingiza, pakua kiolezo cha CSV au Excel. Faili ina safu wima za lazima: Jina_la_ukoo, Jina_la_kwanza, Tarehe_ya_kuzaliwa, Barua_pepe, na safu wima za hiari: Daraja, Leseni, Simu.',
                    'Kujaza faili : Jaza faili na data ya wanafunzi wako. Heshimu muundo: tarehe katika DD/MM/YYYY, daraja kama maandishi (mfano \'Ukanda wa kijani\', \'Dan ya 2\').',
                    'Kupakia na kuoanisha safu wima : Ingiza faili. Kiolesura cha kuoanisha kinakuruhusu kuunganisha kila safu wima ya faili yako na sehemu za MartialComp. Thibitisha kuoanisha.',
                    'Kuthibitisha na kusahihisha : MartialComp inagundua makosa (nakala, muundo batili). Sahihisha safu mlalo zenye makosa au ziruke. Thibitisha kuingiza.',
                ],
                'tip_sw': 'Unaweza kuingiza hadi wanafunzi 500 katika operesheni moja. Kuingiza kunagundua kiotomatiki nakala kwa barua pepe au jina la ukoo + jina la kwanza + tarehe ya kuzaliwa.',
            },
            3: {
                'title_sw': 'Kusimamia faili za wanafunzi',
                'steps_sw': [
                    'Kufikia faili : Kutoka kwenye orodha ya wanachama, bonyeza jina la mwanafunzi kufungua faili yake kamili.',
                    'Kuona maelezo : Faili inaonyesha: taarifa za kibinafsi, historia ya daraja, mashindano yaliyoshirikiwa, mahudhurio na ada.',
                    'Kuhariri taarifa : Bonyeza \'Hariri\' kusasisha data. Mabadiliko yanarekodiwa katika historia.',
                    'Vitendo vya haraka : Kutoka kwenye faili unaweza: kuandikisha kwa mashindano, kugawa daraja, kutuma ujumbe, kutengeneza cheti.',
                ],
                'tip_sw': 'Tumia vichujio vya kina (daraja, umri, leseni hai, ada iliyolipwa) kupata mwanafunzi haraka.',
            },
            4: {
                'title_sw': 'Kuunda akaunti ya mtumiaji kwa mwanafunzi',
                'steps_sw': [
                    'Kufikia faili ya mwanafunzi : Fungua faili ya mwanafunzi husika kutoka kwenye orodha ya wanachama.',
                    'Kuunganisha na akaunti : Bonyeza \'Unda akaunti ya mtumiaji\'. Barua pepe ya mwaliko itatumwa kwa mwanafunzi yenye kiungo cha kuunda nenosiri lake.',
                    'Kuweka ruhusa : Chagua mwanafunzi anaweza kufanya nini: kuona matokeo yake, kujiandikisha kwa mashindano, kuona kalenda, kulipa mtandaoni.',
                ],
                'tip_sw': 'Wanafunzi walio chini ya umri wanaweza kuwa na akaunti iliyounganishwa na ya mzazi kupitia kipengele cha Kundi la Familia.',
            },
            5: {
                'title_sw': 'Kusimamia majukumu na ruhusa za klabu',
                'steps_sw': [
                    'Kufikia usimamizi wa majukumu : Kutoka Mipangilio > Majukumu na ruhusa, angalia majukumu yanayopatikana: Msimamizi, Katibu, Mweka Hazina, Kocha, Mwanachama.',
                    'Kugawa jukumu : Chagua mwanachama na umgawie jukumu. Kila jukumu linatoa ufikiaji wa vipengele maalum.',
                    'Kubinafsisha ruhusa : Kwa kila jukumu, fafanua haki: kusoma tu, kuhariri, kufuta, ufikiaji wa fedha, usimamizi wa usajili.',
                    'Kukagua ufikiaji : Angalia kumbukumbu ya shughuli kuona ni nani alifanya nini na lini katika utawala wa klabu.',
                ],
                'tip_sw': 'Jukumu la Msimamizi lina haki zote. Unda jukumu la Katibu lenye ufikiaji wa wanachama na kalenda lakini si fedha.',
            },
            6: {
                'title_sw': 'Ufuatiliaji wa mahudhurio / Kuingia',
                'steps_sw': [
                    'Kuunda kipindi : Kutoka Mahudhurio > Kipindi kipya, chagua kundi la mafunzo, tarehe na ratiba ya darasa.',
                    'Kurekodi kwa orodha : Onyesha orodha ya wanachama wa kundi na uweke alama kwa waliohudhuria. Kurekodi kunafanywa kwa mguso mmoja kwenye simu.',
                    'Kurekodi kwa msimbo wa QR : Onyesha msimbo wa QR wa kipindi. Wanafunzi wanauskenni kwa simu zao wanapofika dojo.',
                    'Kuona takwimu : Angalia viwango vya mahudhurio kwa mwanafunzi, kundi na kipindi. Tambua kutokuwepo kwa mara kwa mara.',
                ],
                'tip_sw': 'Kuingia kwa msimbo wa QR ndiyo njia ya haraka zaidi kwa makundi makubwa. Msimbo unafanywa upya kwa kila kipindi ili kuzuia udanganyifu.',
            },
            7: {
                'title_sw': 'Kusimamia programu za mafunzo',
                'steps_sw': [
                    'Kuunda programu : Kutoka Programu > Mpya, fafanua jina, taaluma, kiwango (mwanaoanza, wa kati, wa juu) na muda wa mzunguko.',
                    'Kupanga vipindi : Ongeza vipindi vya kila wiki: siku, saa ya kuanza, saa ya kumaliza, ukumbi/tatami, kocha anayehusika.',
                    'Kufafanua maudhui : Kwa kila kipindi, ongeza mpango: joto la mwili, kazi ya kiufundi, sparring/randori, kupoa. Ambatisha faili au video.',
                    'Kuchapisha na kuarifu : Chapisha programu. Wanafunzi wa kundi wanapokea arifa yenye programu kamili.',
                ],
                'tip_sw': 'Nakili programu iliyopo ili kuunda mzunguko mpya haraka na tofauti.',
            },
            8: {
                'title_sw': 'Kutengeneza na kutumia misimbo ya QR ya klabu',
                'steps_sw': [
                    'Kutengeneza msimbo wa QR wa klabu : Kutoka Mipangilio > Misimbo ya QR, tengeneza msimbo wa QR wa klabu yako. Inaruhusu wageni kufikia moja kwa moja ukurasa wako wa umma.',
                    'Misimbo ya QR maalum : Tengeneza misimbo ya QR kwa: usajili mtandaoni, kuingia kwa kipindi, ukurasa wa tukio au kiungo cha programu ya simu.',
                    'Kuchapisha na kuonyesha : Pakua misimbo ya QR katika ubora wa juu kwa kuchapisha. Muundo unaopatikana: PNG, SVG, PDF (A4 au kadi ya biashara).',
                    'Kufuatilia takwimu : Angalia idadi ya uskeni kwa msimbo wa QR, kwa siku na kwa aina. Tambua misimbo ya QR yenye ufanisi zaidi.',
                ],
                'tip_sw': 'Onyesha msimbo wa QR wa usajili kwenye mlango wa dojo yako. Kila uskeni ni mteja anayewezekana!',
            },
            9: {
                'title_sw': 'Kuomba ushirika na shirikisho',
                'steps_sw': [
                    'Kutafuta shirikisho lako : Kutoka Klabu > Ushirika, tafuta shirikisho lako kwa jina, taaluma au nchi.',
                    'Kutuma ombi : Jaza fomu ya ushirika: taarifa za klabu, nambari ya usajili, nyaraka za kuhalalisha (sheria, bima, n.k.).',
                    'Kufuatilia hali : Ombi lako linapitia hatua: Limetumwa > Linakaguliwa > Limeidhinishwa/Limekataliwa. Unapokea arifa kwa kila hatua.',
                    'Kufanya upya kila msimu : Ushirika ni wa kila msimu. Ukumbusho wa kiotomatiki unatumwa siku 30 kabla ya kumalizika.',
                ],
                'tip_sw': 'Ushirika unakupa ufikiaji wa mashindano rasmi ya shirikisho na usimamizi wa kati wa leseni.',
            },
            10: {
                'title_sw': 'Kusimamia uhamisho wa wanafunzi',
                'steps_sw': [
                    'Kuanzisha uhamisho : Kutoka kwenye faili ya mwanafunzi, bonyeza \'Omba uhamisho\'. Chagua klabu ya marudio na sababu ya uhamisho.',
                    'Mchakato wa uthibitishaji : Klabu ya marudio inapokea ombi na inaweza kulikubali au kulikataa. Ikiwa shirikisho linahusika, lazima pia lithibitishe.',
                    'Uhamisho halisi : Mara baada ya kuthibitishwa, mwanafunzi anahamishwa kiotomatiki pamoja na daraja na historia yake ya mashindano.',
                    'Kuona historia : Historia ya uhamisho inaonekana katika faili ya mwanafunzi na katika ripoti za klabu.',
                ],
                'tip_sw': 'Mashirikisho mengine yanaweka vipindi vya uhamisho (madirisha ya uhamisho). MartialComp inaheshimu sheria hizi kiotomatiki.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 3: Mashindano - Uundaji na Usanidi (mafunzo 6)
    # =========================================================================
    3: {
        'title_sw': 'Mashindano - Uundaji na Usanidi',
        'tutorials': {
            1: {
                'title_sw': 'Kuunda mashindano ya mtu binafsi',
                'steps_sw': [
                    'Kuanza uundaji : Kutoka Mashindano > Unda, chagua aina ya \'Mtu Binafsi\'. Ingiza jina, taaluma, tarehe na mahali.',
                    'Kufafanua muundo : Chagua muundo: Mapigano (kumite, randori, sparring), Kiufundi (kata, poomsae, fomu) au Mchanganyiko (zote mbili).',
                    'Kusanidi aina : Fafanua aina kwa jinsia, kundi la umri, uzito na/au daraja. MartialComp inatoa violezo vya aina za kawaida kwa taaluma.',
                    'Chaguo na kuchapisha : Wezesha chaguo unazotaka: usajili mtandaoni, malipo, matangazo ya moja kwa moja, matokeo ya umma. Chapisha mashindano.',
                ],
                'tip_sw': 'Tumia violezo vya aina (WKF, IJF, ITF...) kuokoa muda. Unaweza kuvibinafsisha baada ya uundaji.',
            },
            2: {
                'title_sw': 'Kuunda mashindano ya timu (Sync/Song Luyen)',
                'steps_sw': [
                    'Kuchagua hali ya timu : Wakati wa uundaji, chagua aina ya \'Timu\'. Fafanua idadi ya chini na ya juu ya wanachama kwa timu.',
                    'Kusanidi muundo wa timu : Chagua muundo: Ulandanishi (kata/poomsae ya timu), Song Luyen (mapigano yaliyopangwa kwa wawili) au Mapigano ya timu (kubadilishana).',
                    'Kufafanua muundo : Eleza majukumu ndani ya timu: idadi ya wachezaji wakuu, idadi ya wabadala, kama muundo wa mchanganyiko unaruhusiwa au la.',
                    'Vigezo vya alama za timu : Kwa alama za kiufundi, fafanua kama hakimu wanatathmini timu kwa pamoja au kila mwanachama kibinafsi.',
                ],
                'tip_sw': 'Hali ya Ulandanishi inaruhusu alama zenye vigezo maalum vya ulandanishi (wakati, mpangilio, kujieleza pamoja).',
            },
            3: {
                'title_sw': 'Kusanidi aina za mashindano',
                'steps_sw': [
                    'Kufikia usimamizi wa aina : Kutoka kwenye mashindano yaliyoundwa, nenda kwenye kichupo cha Aina. Bonyeza \'Ongeza aina\'.',
                    'Kufafanua vigezo : Kwa kila aina, fafanua: jinsia (M/F/Mchanganyiko), kundi la umri (mfano miaka 12-14), kundi la uzito (mfano -60kg), daraja la chini/juu.',
                    'Kuipa aina jina : Ipe jina wazi: \'Kadeti Kiume -52kg\' au \'Kata Mtu Mzima Kike wa Juu\'. MartialComp inatengeneza majina ya kiotomatiki ukipendelea.',
                    'Kupanga aina : Panga upya aina kwa kuburuta na kudondosha ili kuweka mpangilio wa kuonekana siku ya mashindano.',
                ],
                'tip_sw': 'Ingiza aina kutoka mashindano ya awali kuokoa muda. Tumia chaguo la \'Nakala ya Akili\' kuunda tofauti.',
            },
            4: {
                'title_sw': 'Kunakili mashindano yaliyopo',
                'steps_sw': [
                    'Kupata mashindano ya chanzo : Kutoka Mashindano > Historia, pata mashindano unayotaka kunakili.',
                    'Kuanza kunakili : Bonyeza nukta 3 > Nakili. Chagua nini cha kunakili: aina, kanuni, usanidi, viwango.',
                    'Kurekebisha usanidi : Badilisha tarehe, mahali na vigezo vinavyohitajika. Aina na kanuni zinanakiliwa kwa usawa.',
                ],
                'tip_sw': 'Bora kwa mashindano ya kila mwaka yanayorudiwa. Nakili toleo la awali na usasishe tarehe tu.',
            },
            5: {
                'title_sw': 'Kusanidi chaguo za kuonekana',
                'steps_sw': [
                    'Kufikia usanidi wa kuonekana : Kutoka kwenye mashindano, nenda Usanidi > Kuonekana na kushiriki.',
                    'Usajili mtandaoni : Wezesha/lemaza usajili wa umma. Weka tarehe za kufungua na kufunga usajili.',
                    'Matokeo na nafasi : Chagua kama matokeo ni ya umma kwa wakati halisi, yanachapishwa baada ya uthibitishaji au ni ya faragha (mwandaaji peke yake).',
                    'Matangazo ya moja kwa moja : Wezesha hali ya matangazo na uongeze kiungo cha YouTube/Twitch/Facebook Live kuonyeshwa kwenye ukurasa wa umma.',
                ],
                'tip_sw': 'Matokeo ya moja kwa moja yanavutia watazamaji kwenye ukurasa wako na kuongeza kuonekana kwa klabu au shirikisho lako.',
            },
            6: {
                'title_sw': 'Kusanidi sheria za mapigano',
                'steps_sw': [
                    'Kuchagua kanuni : Chagua kanuni zilizosanidiwa mapema (WKF, IJF, ITF, IBJJF, n.k.) au uunde moja ya kawaida.',
                    'Kufafanua alama : Sanidi vitendo na alama zake: Yuko (alama 1), Waza-ari (alama 2), Ippon (alama 3), n.k. Ongeza adhabu (Shido, Hansoku, n.k.).',
                    'Kusanidi raundi : Fafanua muda wa raundi, idadi ya raundi, mapumziko na masharti ya ushindi (alama, Ippon, kuacha).',
                    'Sheria maalum : Sanidi sheria maalum: Golden Score (muda wa ziada), Hantei (uamuzi wa hakimu), kumalizika mapema kwa tofauti ya alama.',
                ],
                'tip_sw': 'Hifadhi kanuni zako za kawaida kama violezo ili kuzitumia tena katika mashindano ya baadaye.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 4: Usajili na Timu (mafunzo 7)
    # =========================================================================
    4: {
        'title_sw': 'Usajili na Timu',
        'tutorials': {
            1: {
                'title_sw': 'Kuandikisha wanafunzi kwa mashindano',
                'steps_sw': [
                    'Kupata mashindano : Kutoka Mashindano > Yaliyo wazi kwa usajili, pata mashindano unayotaka na ubonyeze \'Andikisha\'.',
                    'Kuchagua wanafunzi : Orodha ya wanachama wako inaonyeshwa. Chagua mwanafunzi mmoja au zaidi. MartialComp inaonyesha kiotomatiki aina zinazostahili kwa kila mmoja.',
                    'Kuthibitisha aina : Kwa kila mwanafunzi, thibitisha au ubadilishe aina iliyopendekezwa. Mfumo unathibitisha kuwa uzito, umri na daraja vinafanana.',
                    'Kuthibitisha na kulipa : Thibitisha usajili. Ikiwa mashindano yanahitaji malipo, endelea na malipo ya usajili wote.',
                ],
                'tip_sw': 'Wanafunzi wenye wasifu usio kamili (uzito haupo, leseni imemalizika) wataonyeshwa kwa tahadhari nyekundu.',
            },
            2: {
                'title_sw': 'Usajili wa wingi kupitia fomu',
                'steps_sw': [
                    'Kufikia hali ya wingi : Kutoka kwenye skrini ya usajili, bonyeza \'Usajili wa wingi\'. Chagua aina ya marudio.',
                    'Kuchagua kundi : Chuja kwa kundi la mafunzo, daraja au umri. Chagua wanafunzi wanaostahili kwa kubonyeza mara moja.',
                    'Kuthibitisha na kurekebisha : Skrini ya uthibitishaji inaonyesha kila mwanafunzi na aina yake. Sahihisha makosa ikiwa yapo.',
                    'Kuthibitisha kundi : Thibitisha usajili wote kwa operesheni moja. Muhtasari unatumwa kwa barua pepe.',
                ],
                'tip_sw': 'Usajili wa wingi ni bora kwa klabu zinazoandikisha wanafunzi 10+ katika mashindano sawa.',
            },
            3: {
                'title_sw': 'Kuunda na kusimamia timu',
                'steps_sw': [
                    'Kuunda timu : Kutoka kwenye mashindano, bonyeza \'Andikisha timu\'. Ipe timu jina na uchague aina.',
                    'Kuongeza wanachama : Ongeza wanachama wa timu kutoka kwenye orodha yako ya wanafunzi. Heshimu idadi ya chini na ya juu iliyofafanuliwa.',
                    'Kuweka wachezaji wakuu na wabadala : Teua wachezaji wakuu na wabadala kwa kuburuta na kudondosha. Mpangilio wa kuonekana unaweza kuwekwa hapa.',
                    'Kuthibitisha timu : Thibitisha ulinganifu wa timu (idadi ya wanachama, aina za mtu binafsi) na uthibitishe usajili.',
                ],
                'tip_sw': 'Katika mashindano ya timu, jina la timu linaonekana kwenye bao za alama na matokeo rasmi.',
            },
            4: {
                'title_sw': 'Kubadilisha aina ya timu',
                'steps_sw': [
                    'Kufikia timu : Kutoka kwenye usajili wako, pata timu ya kubadilisha na ubonyeze \'Hariri\'.',
                    'Kubadilisha aina : Chagua aina mpya kutoka kwenye menyu ya kushuka. Mfumo unathibitisha kuwa timu inakidhi vigezo.',
                    'Kuthibitisha mabadiliko : Thibitisha. Ikiwa mashindano yana viwango tofauti vya usajili kwa aina, marekebisho ni ya kiotomatiki.',
                ],
                'tip_sw': 'Kubadilisha aina kunawezekana tu wakati usajili bado umefunguliwa.',
            },
            5: {
                'title_sw': 'Kuomba muungano (muunganisho wa klabu tofauti)',
                'steps_sw': [
                    'Kutambua hitaji : Klabu yako haina wanachama wa kutosha kuunda timu kamili? Muungano unaruhusu kuunganisha timu za klabu tofauti.',
                    'Kuunda ombi la muungano : Kutoka kwenye timu isiyo kamili, bonyeza \'Pendekeza muungano\'. Chagua klabu mshirika na nafasi za kujazwa.',
                    'Kutuma pendekezo : Klabu mshirika inapokea ombi lenye maelezo: mashindano, aina, nafasi zinazopatikana, masharti.',
                    'Kukamilisha muungano : Mara baada ya kukubaliwa, timu iliyounganishwa inaonekana na wanachama wa klabu zote mbili. Timu inabeba jina linalochanganya klabu zote mbili.',
                ],
                'tip_sw': 'Muungano unategemea idhini ya mwandaaji wa mashindano na, ikihitajika, ya shirikisho.',
            },
            6: {
                'title_sw': 'Kukubali/kukataa ombi la muungano',
                'steps_sw': [
                    'Kupokea arifa : Unapokea arifa ya ombi la muungano. Bonyeza kuona maelezo.',
                    'Kukagua pendekezo : Thibitisha: klabu inayoomba, mashindano, aina, nafasi za kujazwa na masharti yaliyopendekezwa.',
                    'Kukubali au kukataa : Bonyeza \'Kubali\' kuthibitisha muungano na kuchagua wanachama wako, au \'Kataa\' na ujumbe wa maelezo.',
                ],
                'tip_sw': 'Unaweza kupendekeza mpango mbadala kwa kubadilisha masharti kabla ya kukubali.',
            },
            7: {
                'title_sw': 'Kusimamia usajili uliopokelewa (idhini)',
                'steps_sw': [
                    'Kufikia paneli ya usajili : Kutoka kwenye mashindano, nenda kwenye kichupo cha Usajili. Angalia usajili kwa hali: Inasubiri, Imeidhinishwa, Imekataliwa.',
                    'Kukagua na kuidhinisha : Bonyeza usajili kuangalia taarifa za mwanafunzi. Idhinisha kibinafsi au kwa kundi.',
                    'Kukataa na sababu : Katika hali ya kukataa, chagua sababu: aina isiyo sahihi, leseni batili, usajili wa kuchelewa, n.k.',
                    'Kusafirisha orodha : Safirisha orodha ya walioandikishwa halali katika CSV au PDF kwa kupima uzito na usimamizi siku ya mashindano.',
                ],
                'tip_sw': 'Wezesha idhini ya kiotomatiki ikiwa hutaki kuthibitisha kila usajili kwa mikono.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 5: Siku ya Mashindano - Mapigano (mafunzo 8)
    # =========================================================================
    5: {
        'title_sw': 'Siku ya Mashindano - Mapigano',
        'tutorials': {
            1: {
                'title_sw': 'Kutengeneza makundi kiotomatiki',
                'steps_sw': [
                    'Kufikia usimamizi wa makundi : Kutoka kwenye mashindano, nenda Makundi > Tengeneza kiotomatiki. Chagua aina za kushughulikia.',
                    'Kusanidi usambazaji : Fafanua: idadi ya washindani kwa kundi, kutenganisha wanachama wa klabu moja, vichwa vya mbegu kwa mikono (hiari).',
                    'Kutengeneza na kuthibitisha : Bonyeza \'Tengeneza\'. MartialComp inasambaza washindani ikizuia makabiliano ya ndani ya klabu katika raundi ya kwanza.',
                    'Kurekebisha kwa mikono : Ikihitajika, hamisha washindani kati ya makundi kwa kuburuta na kudondosha. Mfumo unathibitisha migogoro kwa wakati halisi.',
                ],
                'tip_sw': 'Algorithm ya usambazaji inahakikisha usawa kwa kutenganisha klabu na kusawazisha viwango vya ujuzi kati ya makundi.',
            },
            2: {
                'title_sw': 'Kupanga na kupanga upya makundi',
                'steps_sw': [
                    'Mtazamo wa jumla wa makundi : Skrini ya makundi inaonyesha aina zote na idadi ya washindani, makundi na hali (rasimu, imethibitishwa, inaendelea).',
                    'Kuhariri kundi : Bonyeza kundi kuona washindani. Tumia kuburuta na kudondosha kuhamisha mshindani kwenye kundi jingine.',
                    'Kusimamia kutokuwepo : Weka alama mshindani kama hayupo au amejiondoa. Mfumo unahesabu upya makabiliano na nafasi kiotomatiki.',
                    'Kuthibitisha makundi : Ukiridhika, thibitisha makundi. Kitendo hiki kinatengeneza jedwali la makabiliano kiotomatiki.',
                ],
                'tip_sw': 'Thibitisha makundi aina kwa aina ili kuanza mapigano ya aina za kwanza huku ukimalizia nyingine.',
            },
            3: {
                'title_sw': 'Kupanga ratiba ya mapigano',
                'steps_sw': [
                    'Kufafanua maeneo ya mapigano : Kutoka Ratiba > Maeneo, fafanua idadi ya tatami/ringo zinazopatikana na majina yake (Tatami 1, Ringo A, n.k.).',
                    'Kugawa vipindi : Buruta aina kwenye maeneo na vipindi vya muda. MartialComp inahesabu kiotomatiki muda unaokadiriwa.',
                    'Kugundua migogoro : Mfumo unagundua migogoro: mshindani aliyeandikishwa katika aina 2 kwa wakati mmoja. Tumia tahadhari kurekebisha.',
                    'Kuchapisha ratiba : Chapisha ratiba. Washindani, makocha na hakimu wanapokea arifa yenye ratiba zao za ushiriki.',
                ],
                'tip_sw': 'Panga muda wa ziada wa 20% kwa aina kusimamia kuchelewa kusiko kuepukika.',
            },
            4: {
                'title_sw': 'Kutumia kiolesura cha mapigano (alama za moja kwa moja)',
                'steps_sw': [
                    'Kuingia kwenye eneo : Kwenye kompyuta kibao au simu yako, fungua MartialComp na uchague eneo lako la mapigano lililoteuliwa. Ingiza PIN yako ya hakimu.',
                    'Kiolesura cha alama : Skrini inaonyesha: washindani 2 (nyekundu/buluu), vitufe vya vitendo (alama, adhabu), kipima muda na alama za sasa.',
                    'Kutoa alama : Bonyeza vitufe vya alama: Yuko (+1), Waza-ari (+2), Ippon (+3) kwa mshindani mwekundu au buluu. Alama zinasasishwa kwa wakati halisi.',
                    'Kusimamia adhabu : Bonyeza Adhabu kutoa onyo (Shido) au kufukuzwa (Hansoku). Adhabu ni za mrundikano.',
                    'Kumalizia pambano : Kipima muda kinasimama kiotomatiki. Thibitisha matokeo (ushindi kwa alama, Ippon, kuacha). Nafasi zinasasishwa mara moja.',
                ],
                'tip_sw': 'Kiolesura kimeboreshwa kwa kompyuta kibao katika hali ya mlalo. Vitufe ni vikubwa kwa makusudi kwa matumizi ya haraka na yasiyo na makosa.',
            },
            5: {
                'title_sw': 'Hali ya Kiosiki ya tatami nyingi',
                'steps_sw': [
                    'Kuwezesha hali ya Kiosiki : Kutoka Mipangilio > Hali ya Kiosiki, wezesha hali na uweke msimbo wa PIN kwa kila eneo la mapigano.',
                    'Kusanidi kila kompyuta kibao : Kwenye kila kompyuta kibao ya eneo, ingia na uchague eneo husika. Ingiza PIN kufunga skrini kwenye eneo hili.',
                    'Usimamizi huru : Kila eneo linafanya kazi kwa uhuru: alama, kipima muda, kuonyesha. Bao kuu linasasishwa kwa wakati halisi.',
                    'Skrini ya watazamaji : Unganisha skrini ya ziada katika hali ya \'Mtazamaji\' kuonyesha alama katika muundo mkubwa, unaoonekana kutoka kwenye viti.',
                ],
                'tip_sw': 'Hali ya Kiosiki inazuia hakimu kutembea kwa bahati mbaya nje ya kiolesura cha alama.',
            },
            6: {
                'title_sw': 'Kufuatilia nafasi za moja kwa moja',
                'steps_sw': [
                    'Paneli ya moja kwa moja : Skrini ya ufuatiliaji inaonyesha kwa wakati halisi: mapigano yanayoendelea kwa eneo, nafasi za makundi, maendeleo kuelekea hatua za mwisho.',
                    'Kuchuja kwa aina : Chagua aina kuona maelezo: makundi yaliyokamilika, yanayoendelea na yanayosubiri, pamoja na nafasi za muda.',
                    'Arifa za kiotomatiki : Mfumo unawajulisha kiotomatiki makocha wakati washindani wao lazima wajiwasilishe kwenye eneo la mapigano.',
                ],
                'tip_sw': 'Onyesha paneli kwenye skrini kubwa katika eneo la mapokezi ili washiriki wote waweze kufuatilia maendeleo.',
            },
            7: {
                'title_sw': 'Kutengeneza hatua za mwisho (nusu fainali/fainali)',
                'steps_sw': [
                    'Makundi yamekamilika : Mara makundi yote ya aina yamekamilika, mfumo unahesabu waliostahili kulingana na sheria zilizofafanuliwa (wa 1 na wa 2 kwa kundi, n.k.).',
                    'Kutengeneza mchoro : Bonyeza \'Tengeneza hatua za mwisho\'. Mchoro wa kuondolewa (robo fainali, nusu fainali, fainali, fainali ya shaba) unatengenezwa kiotomatiki.',
                    'Kusimamia mechi za kurudia : Ikiwa sheria zinaruhusu, mechi za kurudia zinatengenezwa kiotomatiki na walioshindwa nusu fainali.',
                    'Kuanza fainali : Mapigano ya hatua za mwisho yanaonekana kwenye ratiba. Alama zinafanya kazi sawa na za makundi.',
                ],
                'tip_sw': 'Mchoro wa kuondolewa unatengenezwa kiotomatiki ukizuia, inapowezekana, makabiliano kati ya washindani wa klabu moja.',
            },
            8: {
                'title_sw': 'Kusimamia sherehe ya podio',
                'steps_sw': [
                    'Kufikia podio : Kutoka kwenye aina iliyokamilika, bonyeza \'Podio\'. Nafasi ya mwisho inaonyeshwa: Dhahabu, Fedha, Shaba (na labda Shaba 2).',
                    'Kuonyesha kwa hatua : Tumia hali ya \'Sherehe\' kwa kuonyesha kwa hatua: wa 3, kisha wa 2, kisha wa 1, na michoro na sauti.',
                    'Kutangaza kwenye skrini kubwa : Unganisha hali ya Wasilisho kwenye projekta kwa kuonyesha kwa kuvutia wakati wa utoaji medali.',
                    'Kushiriki matokeo : Podio zinachapishwa kiotomatiki kwenye ukurasa wa mashindano na zinaweza kushirikiwa kwenye mitandao ya kijamii.',
                ],
                'tip_sw': 'Piga picha ya podio na uiongeze kwenye mashindano ili kuimarisha mkusanyiko na mitandao ya kijamii.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 6: Alama za Kiufundi (mafunzo 6)
    # =========================================================================
    6: {
        'title_sw': 'Alama za Kiufundi',
        'tutorials': {
            1: {
                'title_sw': 'Kusanidi vigezo vya alama',
                'steps_sw': [
                    'Kufikia vigezo : Kutoka kwenye mashindano, nenda Alama > Vigezo. Chagua kiolezo au uunde vigezo vyako mwenyewe.',
                    'Kufafanua vigezo : Ongeza vigezo vya tathmini: Mbinu (misimamo, mabadiliko), Nguvu (kime, nguvu), Mdundo (tempo, mtiririko), Kujieleza (zanshin, roho).',
                    'Kugawa uzito : Fafanua uzito wa kila kigezo: mfano Mbinu 40%, Nguvu 25%, Mdundo 20%, Kujieleza 15%. Jumla lazima iwe 100%.',
                    'Kufafanua kipimo : Chagua kipimo cha alama: 1-5, 1-10, 5.0-10.0 au maalum. Fafanua ongezeko (0.1, 0.5 au 1).',
                ],
                'tip_sw': 'Violezo vya WKF na WTF vimesanidiwa mapema. Vibinafsishe kulingana na mahitaji yako maalum.',
            },
            2: {
                'title_sw': 'Kuwagawa hakimu kwa aina',
                'steps_sw': [
                    'Kufungua paneli ya ugawaji : Kutoka Alama > Hakimu, angalia orodha ya hakimu walioandikishwa na aina za kushughulikiwa.',
                    'Kugawa kwa aina : Buruta hakimu kwenye aina. Fafanua idadi ya hakimu kwa aina (kawaida 5 au 7).',
                    'Uthibitishaji wa kutokuwa na upendeleo : MartialComp inathibitisha kiotomatiki migogoro ya kimaslahi: hakimu hawezi kutathmini mshindani wa klabu yake mwenyewe.',
                    'Kusimamia mabadilishano : Panga mabadilishano ya hakimu kati ya aina kuzuia uchovu na kudumisha usawa.',
                ],
                'tip_sw': 'Mfumo wa kugundua upendeleo unachunguza tofauti za alama kati ya hakimu na kuonya ikiwa hakimu anapiga alama mara kwa mara juu au chini sana.',
            },
            3: {
                'title_sw': 'Kutumia karatasi ya alama za kiufundi',
                'steps_sw': [
                    'Kuingia kama hakimu : Kwenye kompyuta yako kibao, ingia na akaunti yako ya hakimu. Chagua aina iliyoteuliwa.',
                    'Kiolesura cha alama : Skrini inaonyesha mshindani wa sasa, vigezo vya tathmini na kibodi ya nambari. Kila kigezo kina kitelezi au kibodi yake.',
                    'Kutathmini kwa zamu : Kwa kila mshindani, ingiza alama yako kwa kila kigezo. Thibitisha tathmini yako kabla ya kuendelea na anayefuata.',
                    'Kuhifadhi : Tathmini yako inahifadhiwa mara moja. Unaweza kubadilisha alama zako mradi zamu haijafungwa na mwandaaji.',
                ],
                'tip_sw': 'Kiolesura cha kidijitali kimeboreshwa kwa kuingiza haraka kwenye kompyuta kibao. Mguso mmoja kwa kila alama.',
            },
            4: {
                'title_sw': 'Alama za kiufundi za timu (Ulandanishi)',
                'steps_sw': [
                    'Kuelewa hali ya timu : Katika alama za Ulandanishi, vigezo vya ziada vinaonekana: Ulandanishi, Mpangilio wa Anga, Kujieleza Pamoja.',
                    'Kutathmini timu kwa pamoja : Ikisanidiwa hivyo, tathmini timu kwa pamoja kwa kila kigezo, ikiwa ni pamoja na ulandanishi.',
                    'Kutathmini kibinafsi + timu : Ikisanidiwa kwa tathmini ya mchanganyiko, tathmini kila mwanachama kibinafsi NA KISHA ongeza alama ya timu kwa ulandanishi.',
                ],
                'tip_sw': 'Katika hali ya Ulandanishi, kigezo cha ulandanishi kinawakilisha kawaida 20-30% ya alama za jumla.',
            },
            5: {
                'title_sw': 'Kufunga na kuchapisha alama',
                'steps_sw': [
                    'Kuthibitisha alama : Kutoka kwenye paneli ya mwandaaji, angalia alama za hakimu wote kwa kila mshindani. Tambua tofauti za kutiliwa shaka.',
                    'Kufunga zamu : Bonyeza \'Funga\' kuzuia marekebisho yoyote. Hesabu ya mwisho (kuondoa alama ya juu zaidi/ya chini zaidi, wastani) inafanywa.',
                    'Kuchapisha matokeo : Chapisha nafasi. Alama za kina za kila hakimu zinaweza kufichwa au kuonyeshwa kulingana na usanidi wako.',
                    'Hali ya majaribio / kufanya upya : Kabla ya mashindano, tumia hali ya majaribio kuthibitisha mfumo. Kufanya upya kunafuta alama zote za majaribio.',
                ],
                'tip_sw': 'Kufunga zamu kwa zamu kunaruhusu kuchapisha matokeo zamu kwa zamu wakati mashindano yanaendelea.',
            },
            6: {
                'title_sw': 'Kuona nafasi za muda',
                'steps_sw': [
                    'Kufikia nafasi : Kutoka kwenye kichupo cha Nafasi, angalia nafasi kwa wakati halisi pamoja na alama kwa kigezo na alama ya mwisho.',
                    'Kupanga na kuchuja : Panga kwa alama za jumla au kwa kigezo maalum. Chuja kwa kundi au washindani wote.',
                    'Takwimu za hakimu : Angalia takwimu: wastani kwa hakimu, kupotoka kwa kawaida, kugundua upendeleo. Chombo muhimu kwa usawa.',
                ],
                'tip_sw': 'Nafasi za muda zinaonekana tu kwa waandaaji na hakimu. Zinachapishwa kwa washindani tu baada ya kufunga.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 7: Matokeo na Rekodi (mafunzo 4)
    # =========================================================================
    7: {
        'title_sw': 'Matokeo na Rekodi',
        'tutorials': {
            1: {
                'title_sw': 'Kuona matokeo ya mashindano',
                'steps_sw': [
                    'Kupata mashindano : Kutoka kwenye menyu ya Mashindano au ukurasa wa umma, chagua mashindano unayotaka.',
                    'Kushauriana matokeo : Matokeo yamepangwa kwa aina. Kwa kila aina: podio, nafasi kamili na maelezo ya alama.',
                    'Maelezo ya pambano : Bonyeza pambano kuona maelezo: alama kwa raundi, adhabu, kipima muda na labda video ya pambano.',
                ],
                'tip_sw': 'Matokeo ya umma yanapatikana bila akaunti ya MartialComp kupitia kiungo cha mashindano.',
            },
            2: {
                'title_sw': 'Kuchapisha na kushiriki matokeo',
                'steps_sw': [
                    'Kuthibitisha matokeo : Kutoka kwenye paneli ya mwandaaji, kagua matokeo ya kila aina. Bonyeza \'Thibitisha na uchapishie\'.',
                    'Kutengeneza kiungo cha umma : Kiungo cha kudumu kwa ukurasa wa matokeo kinatengenezwa. Kinakili kushiriki.',
                    'Kushiriki kwenye mitandao ya kijamii : Tumia vitufe vya kushiriki vilivyojumuishwa kuchapisha kwenye Facebook, Instagram, Twitter. Podio zinatengeneza picha kiotomatiki.',
                    'Msimbo wa QR wa matokeo : Tengeneza msimbo wa QR wa matokeo kuonyesha kwenye eneo la mashindano kwa watazamaji.',
                ],
                'tip_sw': 'Picha ya kiotomatiki ya podio imeumbizwa kwa Instagram Stories (9:16) na Facebook (16:9).',
            },
            3: {
                'title_sw': 'Kusafirisha matokeo (CSV/PDF)',
                'steps_sw': [
                    'Kufikia usafirishaji : Kutoka Matokeo > Safirisha, chagua muundo: CSV (data ghafi), PDF (ripoti iliyoumbizwa) au Excel.',
                    'Kuchagua maudhui : Chagua: Nafasi za jumla, Podio tu, Maelezo kwa aina, Ripoti ya medali kwa klabu au Yote.',
                    'Kubinafsisha PDF : Kwa PDF, chagua kiolezo: ripoti rasmi (yenye nembo ya shirikisho), ripoti rahisi au diploma.',
                ],
                'tip_sw': 'Ripoti ya medali kwa klabu ni muhimu sana kwa mashirikisho na wadhamini.',
            },
            4: {
                'title_sw': 'Kushauriana rekodi yako ya kibinafsi',
                'steps_sw': [
                    'Kufikia Rekodi yangu : Kutoka kwenye wasifu wako wa mwanafunzi, bonyeza \'Rekodi\'. Historia yako ya mashindano inaonyeshwa.',
                    'Kuona takwimu : Angalia: idadi ya mashindano, medali (dhahabu/fedha/shaba), asilimia ya ushindi, maendeleo kwa wakati.',
                    'Kushiriki rekodi yako : Tengeneza kiungo cha umma kwa rekodi yako au isafirishe kwa PDF kwa maombi yako ya udhamini au ufadhili.',
                ],
                'tip_sw': 'Rekodi yako inasasishwa kiotomatiki baada ya kila mashindano. Inaonekana kwenye wasifu wako wa umma ukiiruhusu.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 8: Usimamizi wa Daraja (mafunzo 5)
    # =========================================================================
    8: {
        'title_sw': 'Usimamizi wa Daraja',
        'tutorials': {
            1: {
                'title_sw': 'Kusanidi mfumo wa daraja',
                'steps_sw': [
                    'Kufikia usanidi : Kutoka Mipangilio > Daraja, chagua taaluma na ufafanue mfumo wako wa daraja.',
                    'Kuunda viwango : Ongeza viwango kwa mpangilio: Ukanda mweupe, Njano, Machungwa, Kijani, Buluu, Kahawia, Mweusi Dan ya 1, Dan ya 2, n.k.',
                    'Kufafanua masharti ya awali : Kwa kila daraja, fafanua: muda wa chini katika daraja la awali, umri wa chini, idadi ya chini ya madarasa, kama mtihani unahitajika.',
                    'Kugawa rangi : Gawa rangi za ukanda kwa kuonyesha katika kiolesura na wasifu.',
                ],
                'tip_sw': 'Mifumo ya daraja ya kawaida (Judo, Karate, TKD, BJJ) imesanidiwa mapema. Unaweza kuibinafsisha au kuunda mpya.',
            },
            2: {
                'title_sw': 'Kugawa daraja kwa mwanafunzi',
                'steps_sw': [
                    'Kufikia faili : Kutoka kwenye faili ya mwanafunzi, bonyeza kichupo cha Daraja kisha \'Gawa daraja jipya\'.',
                    'Kuchagua daraja : Chagua daraja kutoka kwenye orodha. Mfumo unathibitisha kiotomatiki masharti ya awali (muda, umri, mitihani).',
                    'Kuingiza maelezo : Ongeza tarehe ya ugawaji, mahali, juri/mtahini na maoni.',
                    'Ugawaji wa wingi : Kutoka Daraja > Ugawaji wa wingi, chagua wanafunzi kadhaa na ugawie daraja moja kwa wote.',
                ],
                'tip_sw': 'Barua pepe ya pongezi inatumwa kiotomatiki kwa mwanafunzi na daraja lake jipya.',
            },
            3: {
                'title_sw': 'Kupanga mtihani wa daraja',
                'steps_sw': [
                    'Kuunda mtihani : Kutoka Daraja > Mitihani, unda mtihani mpya: tarehe, mahali, taaluma, daraja zinazoshughulikiwa, juri.',
                    'Kuandikisha wagombea : Ongeza wagombea kwa mikono au ruhusu kujiandikisha mwenyewe. Mfumo unathibitisha masharti ya awali ya kila mmoja.',
                    'Siku ya mtihani : Tumia kiolesura cha mtihani kutathmini kila mgombea: mbinu zinazohitajika, mapigano, nadharia.',
                    'Kuchapisha matokeo : Thibitisha waliofaulu na walioshindwa. Daraja zinagawanywa kiotomatiki kwa wagombea waliofaulu.',
                ],
                'tip_sw': 'Mitihani ya daraja inaweza kuunganishwa na mashindano (mfano kupandishwa daraja wakati wa mashindano).',
            },
            4: {
                'title_sw': 'Kusimamia historia na maendeleo ya daraja',
                'steps_sw': [
                    'Kuona historia : Faili ya kila mwanafunzi inaonyesha historia kamili ya daraja: tarehe, mahali, juri, maoni.',
                    'Kuona maendeleo : Chati inaonyesha maendeleo kwa wakati. Linganisha na wastani wa klabu.',
                    'Kubatilisha daraja : Katika hali ya kosa, batilisha daraja na sababu. Historia inahifadhi rekodi ya kubatilisha.',
                ],
                'tip_sw': 'Historia ya daraja inaweza kuhamishwa ikiwa mwanafunzi anabadilisha klabu.',
            },
            5: {
                'title_sw': 'Kutengeneza vyeti vya daraja',
                'steps_sw': [
                    'Kufikia vyeti : Kutoka Daraja > Vyeti, chagua mwanafunzi na daraja ambalo cheti kitatengenezwa.',
                    'Kuchagua kiolezo : Chagua kiolezo cha cheti: rasmi (yenye nembo ya shirikisho), cha klabu au maalum.',
                    'Kubinafsisha : Ongeza saini, muhuri wa klabu na maelezo maalum. Msimbo wa QR wa uthibitishaji unaongezwa kiotomatiki.',
                    'Kutengeneza na kusambaza : Tengeneza PDF. Chapisha au utume kwa barua pepe. Msimbo wa QR unaruhusu mtu yeyote kuthibitisha uhalisi wa cheti.',
                ],
                'tip_sw': 'Msimbo wa QR wa uthibitishaji unaelekeza kwenye ukurasa wa umma wa MartialComp unaothibitisha uhalali wa daraja.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 9: Usimamizi wa Shirikisho (mafunzo 8)
    # =========================================================================
    9: {
        'title_sw': 'Usimamizi wa Shirikisho',
        'tutorials': {
            1: {
                'title_sw': 'Kusimamia klabu zilizoshirikishwa',
                'steps_sw': [
                    'Mtazamo wa jumla : Paneli ya shirikisho inaonyesha ramani ya klabu zilizoshirikishwa, hali yao (hai, inasubiri, imemalizika) na takwimu.',
                    'Kushughulikia maombi : Maombi mapya ya ushirika yanaonekana katika Klabu > Zinazosubiri. Kagua nyaraka na uidhinishe au ukatae.',
                    'Kufuatilia upyaji : Angalia ushirika unaokaribia kumalizika. Tuma vikumbusho vya kiotomatiki siku 30, 15 na 7 kabla.',
                ],
                'tip_sw': 'Paneli ya shirikisho inatoa mtazamo wa wakati halisi wa jumla ya wanafunzi wenye leseni katika klabu zote.',
            },
            2: {
                'title_sw': 'Kusimamia misimu na ada',
                'steps_sw': [
                    'Kuunda msimu : Kutoka Misimu > Mpya, fafanua tarehe za kuanza na kumaliza na viwango vya ada kwa aina (klabu, mtu binafsi, watoto, watu wazima).',
                    'Kusanidi ada : Fafanua kiasi kwa aina: ushirika wa klabu (fasta), leseni ya mtu binafsi (kwa mwanafunzi), bima (hiari).',
                    'Kufuatilia malipo : Angalia ada zilizopokelewa, zinazosubiri na zilizomalizika kwa wakati halisi. Tuma vikumbusho vya kiotomatiki.',
                    'Kufunga msimu : Mwisho wa msimu, ufunge kutengeneza ripoti ya kifedha na kuandaa msimu unaofuata.',
                ],
                'tip_sw': 'Ada zinaweza kulipwa mtandaoni kupitia Stripe au kwa uhamisho wa benki. Ufuatiliaji ni wa kiotomatiki katika hali zote mbili.',
            },
            3: {
                'title_sw': 'Kusimamia mashindano',
                'steps_sw': [
                    'Mtazamo wa jumla : Kalenda ya shirikisho inaonyesha mashindano yote ya klabu zilizoshirikishwa, pamoja na hali na idadi ya washiriki.',
                    'Kuidhinisha mashindano : Klabu zinatuma mashindano yao kwa idhini. Thibitisha sheria, hakimu na uidhinishe.',
                    'Kuona matokeo : Fikia matokeo ya mashindano yote yaliyoidhinishwa. Nafasi za kitaifa zinasasishwa kiotomatiki.',
                ],
                'tip_sw': 'Mashindano yaliyoidhinishwa na shirikisho yanaangaziwa katika saraka na kalenda ya umma.',
            },
            4: {
                'title_sw': 'Kusimamia hakimu na sifa zao',
                'steps_sw': [
                    'Hifadhidata ya hakimu : Angalia hifadhidata ya hakimu walioshirikishwa pamoja na sifa zao, utaalamu na historia ya shughuli.',
                    'Kusimamia viwango : Gawa viwango vya sifa: kikanda, kitaifa, kimataifa. Fafanua vigezo vya kupandishwa.',
                    'Ufuatiliaji wa kutokuwa na upendeleo : MartialComp inachunguza takwimu za alama za kila hakimu na kugundua upendeleo unaowezekana.',
                ],
                'tip_sw': 'Hakimu wenye historia ya alama zilizo sawa wanaangaziwa kwa mashindano muhimu.',
            },
            5: {
                'title_sw': 'Kusimamia vyeti',
                'steps_sw': [
                    'Kuunda kiolezo : Buni violezo vyako vya cheti na nembo ya shirikisho, maelezo ya kisheria na sehemu za nguvu.',
                    'Kutoa vyeti : Tengeneza vyeti kwa: daraja, sifa za hakimu, diploma za kufundisha, ushahidi mbalimbali.',
                    'Uthibitishaji wa umma : Kila cheti kina msimbo wa QR wa kipekee. Mtu yeyote anaweza kuuskenni kuthibitisha uhalisi kwenye martialcomp.com.',
                ],
                'tip_sw': 'Vyeti vya kidijitali haviwezi kughushiwa shukrani kwa msimbo wa QR wa uthibitishaji uliounganishwa na MartialComp.',
            },
            6: {
                'title_sw': 'Kubinafsisha tovuti ya umma ya shirikisho',
                'steps_sw': [
                    'Kufikia kijenzi cha tovuti : Kutoka Mipangilio > Tovuti ya umma, fungua kihariri cha ukurasa. Shirikisho lako lina URL: shirikisho.martialcomp.com.',
                    'Kubinafsisha muonekano : Chagua rangi, mandhari, bango na nembo. Ongeza maelezo na viungo vya mitandao yako ya kijamii.',
                    'Kuongeza maudhui : Chapisha habari, mkusanyiko wa picha, video, kalenda ya mashindano na nyaraka za kupakua.',
                    'Kusimamia kurasa : Unda kurasa za ziada: Historia, Viongozi, Kanuni, Mawasiliano.',
                ],
                'tip_sw': 'Tovuti ya umma imeboreshwa kwa SEO. Kadri inavyokuwa kamili, ndivyo inavyoorodheshwa vizuri kwenye Google.',
            },
            7: {
                'title_sw': 'Kuona takwimu na ripoti',
                'steps_sw': [
                    'Paneli ya uchambuzi : Paneli inaonyesha viashirio muhimu: idadi ya klabu, wanafunzi, mashindano, leseni hai, ukuaji.',
                    'Ripoti kwa klabu : Tengeneza ripoti za kina kwa klabu: idadi ya wanachama, ada, ushiriki katika mashindano, daraja zilizotolewa.',
                    'Ripoti kwa taaluma : Chunguza usambazaji kwa taaluma, umri, jinsia. Tambua mielekeo ya ukuaji.',
                    'Kusafirisha na kushiriki : Safirisha ripoti kwa PDF, Excel au CSV kwa mikutano yako mikuu na ripoti rasmi.',
                ],
                'tip_sw': 'Ripoti zinasasishwa kwa wakati halisi. Panga utumaji wa kiotomatiki wa kila mwezi au robo mwaka.',
            },
            8: {
                'title_sw': 'Kusimamia programu za mafunzo',
                'steps_sw': [
                    'Kuunda programu : Kutoka Mafunzo > Mpya, fafanua programu: kichwa, taaluma, kiwango, muda, masharti ya awali.',
                    'Kupanga vipindi : Ongeza vipindi vya mafunzo: tarehe, maeneo, wakufunzi, idadi ya nafasi.',
                    'Kusimamia usajili : Makocha na hakimu wanajiandikisha mtandaoni. Thibitisha usajili na utume mialiko.',
                    'Ufuatiliaji na utoaji vyeti : Fuatilia mahudhurio ya vipindi. Toa vyeti kwa washiriki waliokamilisha programu.',
                ],
                'tip_sw': 'Programu za mafunzo zilizokamilika zinaonekana kiotomatiki kwenye wasifu wa makocha na hakimu.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 10: Fedha (mafunzo 5)
    # =========================================================================
    10: {
        'title_sw': 'Fedha',
        'tutorials': {
            1: {
                'title_sw': 'Kufuatilia miamala ya klabu',
                'steps_sw': [
                    'Mtazamo wa jumla : Paneli ya kifedha inaonyesha: salio, mapato ya mwezi, matumizi na chati ya mielekeo.',
                    'Kurekodi muamala : Ongeza mapato au matumizi: kiasi, tarehe, aina (ada, vifaa, kodi), maelezo.',
                    'Uainishaji wa kiotomatiki : MartialComp inaainisha kiotomatiki miamala inayorudiwa. Binafsisha aina kulingana na mahitaji yako.',
                ],
                'tip_sw': 'Unganisha akaunti yako ya benki ili kuingiza miamala kiotomatiki na kurahisisha upatanishi.',
            },
            2: {
                'title_sw': 'Kuunda na kutuma ankara',
                'steps_sw': [
                    'Kuunda ankara : Kutoka Fedha > Ankara > Mpya, chagua mpokeaji (mwanafunzi, klabu, mdhamini) na mistari ya ankara.',
                    'Kubinafsisha : Ongeza nembo yako, maelezo ya kisheria, masharti ya malipo. Chagua sarafu na kiwango cha VAT.',
                    'Kutuma : Tuma ankara kwa barua pepe. Mpokeaji anapokea kiungo cha malipo mtandaoni (Stripe) na ankara kwa PDF.',
                    'Kufuatilia malipo : Angalia ankara zilizolipwa, zinazosubiri na zilizomalizika. Tuma vikumbusho vya kiotomatiki.',
                ],
                'tip_sw': 'Ada za wanafunzi zinatengeneza kiotomatiki ankara ikiwa utawezesha chaguo hili.',
            },
            3: {
                'title_sw': 'Kusimamia malipo mtandaoni (Stripe)',
                'steps_sw': [
                    'Kuunganisha Stripe : Kutoka Mipangilio > Malipo, bonyeza \'Unganisha Stripe\'. Fuata hatua kuunganisha akaunti yako ya Stripe.',
                    'Kusanidi checkout : Weka viwango kwa: ada, usajili wa mashindano, duka. Wezesha malipo ya kurudia ikihitajika.',
                    'Kujaribu malipo : Tumia hali ya majaribio ya Stripe kuthibitisha kuwa kila kitu kinafanya kazi kabla ya kuwezesha malipo halisi.',
                    'Kufuatilia mapato : Paneli ya Stripe katika MartialComp inaonyesha malipo yaliyopokelewa, marejesho na uhamisho kwenye akaunti yako ya benki.',
                ],
                'tip_sw': 'Stripe inatoza ada ya 1.4% + EUR 0.25 kwa muamala barani Ulaya. Fedha zinahamishwa katika siku 2-7.',
            },
            4: {
                'title_sw': 'Kuingiza taarifa za benki',
                'steps_sw': [
                    'Kupakua taarifa : Kutoka kwenye benki yako, safirisha taarifa katika muundo wa CSV, OFX au QIF.',
                    'Kuingiza katika MartialComp : Kutoka Fedha > Ingiza, pakia faili. MartialComp inagundua muundo na kuoanisha safu wima.',
                    'Kupatanisha : Mfumo unaoanisha kiotomatiki miamala iliyoingizwa na ankara na ada zilizopo.',
                    'Kuthibitisha : Thibitisha kuoanisha, sahihisha makosa na uthibitishe. Miamala isiyooanishwa inaongezwa kama inazosubiri.',
                ],
                'tip_sw': 'Kuingiza taarifa za benki kila mwezi kunahifadhi hesabu zako zikiwa sasa bila kuingiza kwa mikono.',
            },
            5: {
                'title_sw': 'Kusimamia ada za wanafunzi',
                'steps_sw': [
                    'Kusanidi viwango : Kutoka Fedha > Ada, weka viwango vya kila mwaka kwa aina: mtoto, kijana, mtu mzima, familia.',
                    'Kutoa maombi ya malipo : Mwanzoni mwa msimu, tengeneza maombi ya malipo kwa wanachama wote. Kila mmoja anapokea barua pepe yenye kiungo cha malipo.',
                    'Kufuatilia malipo : Angalia ada zilizolipwa, zinazosubiri na zilizomalizika. Hali inaonekana kwenye faili ya kila mwanafunzi.',
                    'Kutuma vikumbusho : Panga vikumbusho vya kiotomatiki: wiki 1, wiki 2, mwezi 1 baada ya tarehe ya kumalizika.',
                ],
                'tip_sw': 'Wanafunzi wenye ada zilizomalizika wanaweza kuzuiwa kujiandikisha kwa mashindano.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 11: Matukio na Kalenda (mafunzo 3)
    # =========================================================================
    11: {
        'title_sw': 'Matukio na Kalenda',
        'tutorials': {
            1: {
                'title_sw': 'Kuunda tukio (semina, gala, mkutano)',
                'steps_sw': [
                    'Kuunda tukio : Kutoka Kalenda > Tukio jipya, ingiza: aina (semina, gala, mkutano, siku ya wazi), kichwa, tarehe, mahali na maelezo.',
                    'Kusanidi usajili : Wezesha usajili mtandaoni. Weka idadi ya nafasi, bei (bure au ya kulipia) na tarehe ya mwisho ya usajili.',
                    'Kuchapisha : Chapisha tukio. Linaonekana kwenye kalenda ya klabu na linaweza kushirikiwa kwenye mitandao ya kijamii.',
                ],
                'tip_sw': 'Semina zenye mabwana wageni ni zana bora za masoko. Ongeza picha na wasifu wao kuvutia watu zaidi.',
            },
            2: {
                'title_sw': 'Kusimamia matukio yanayorudiwa',
                'steps_sw': [
                    'Kuunda kurudia : Wakati wa uundaji, weka alama \'Tukio linalorudiwa\'. Weka marudio: kila siku, kila wiki, kila mwezi.',
                    'Kusimamia masingizio : Ghairi au ubadilishe tukio moja bila kuathiri mengine (mfano darasa limeghairiwa kwa sababu ya likizo).',
                    'Kubadilisha mfululizo : Badilisha mfululizo mzima (mfano mabadiliko ya kudumu ya ratiba) au tukio moja tu.',
                ],
                'tip_sw': 'Madarasa ya kila wiki yanapaswa kuundwa kama matukio yanayorudiwa ili yaonekane kiotomatiki kwenye kalenda.',
            },
            3: {
                'title_sw': 'Kufuatilia usajili na mahudhurio',
                'steps_sw': [
                    'Kuona waliojiandikisha : Kutoka kwenye tukio, angalia orodha ya waliojiandikisha na hali yao: amejiandikisha, amethibitishwa, ameghairi.',
                    'Kurekodi mahudhurio : Siku ya tukio, rekodi mahudhurio kwa orodha au msimbo wa QR.',
                    'Kusafirisha : Safirisha orodha ya washiriki kwa CSV au PDF kwa kumbukumbu zako.',
                ],
                'tip_sw': 'Kiwango cha ushiriki katika matukio ni kiashirio muhimu cha ushiriki wa wanachama wako.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 12: Usimamizi wa Familia (mafunzo 3)
    # =========================================================================
    12: {
        'title_sw': 'Usimamizi wa Familia',
        'tutorials': {
            1: {
                'title_sw': 'Kuunda kundi la familia',
                'steps_sw': [
                    'Kufikia makundi ya familia : Kutoka kwenye wasifu wako, nenda Mipangilio > Kundi la Familia > Unda.',
                    'Kuongeza wanachama : Ongeza kila mwanachama wa familia: mwenzi, watoto. Unganisha akaunti zao za MartialComp zilizopo au uunde mpya.',
                    'Kuweka mhusika : Mhusika wa kundi la familia anapokea arifa zote na anasimamia malipo ya familia nzima.',
                ],
                'tip_sw': 'Klabu nyingine zinatoa viwango vya familia (punguzo kuanzia mwanachama wa 3). Kundi la familia linawezesha punguzo hizi kiotomatiki.',
            },
            2: {
                'title_sw': 'Kuandikisha familia nzima kwa mashindano',
                'steps_sw': [
                    'Usajili wa kundi : Kutoka kwenye mashindano, bonyeza \'Andikisha familia yangu\'. Wanachama wanaostahili wa kundi lako la familia wanaonyeshwa.',
                    'Kuchagua na kuthibitisha : Chagua wanachama wa kuandikisha. Aina zinapendekezwa kiotomatiki kwa kila mmoja.',
                    'Malipo moja : Lipa usajili wote kwa muamala mmoja.',
                ],
                'tip_sw': 'Usajili wa kundi unaokoa muda muhimu wakati watoto kadhaa wanashiriki katika mashindano sawa.',
            },
            3: {
                'title_sw': 'Kituo cha malipo ya familia',
                'steps_sw': [
                    'Mtazamo wa jumla : Kituo cha familia kinaonyesha ada zote, usajili na ankara za familia kwenye skrini moja.',
                    'Malipo ya pamoja : Jumlisha malipo kadhaa yanayosubiri na ulipe kwa muamala mmoja.',
                    'Historia : Angalia historia kamili ya malipo ya familia na risiti zinazoweza kupakuliwa.',
                ],
                'tip_sw': 'Wezesha malipo ya kiotomatiki ili usisahau ada kamwe.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 13: Usimamizi wa Kazi (Kanban) (mafunzo 2)
    # =========================================================================
    13: {
        'title_sw': 'Usimamizi wa Kazi (Kanban)',
        'tutorials': {
            1: {
                'title_sw': 'Kutumia bodi ya Kanban',
                'steps_sw': [
                    'Kuunda bodi : Kutoka Zana > Kanban, unda bodi mpya: jina, maelezo na wanachama walioalikwa.',
                    'Kuongeza safu wima : Unda safu wima za mchakato wako wa kazi: Ya kufanya, Inaendelea, Inasubiri, Imekamilika. Binafsisha majina na rangi.',
                    'Kuunda kazi : Ongeza kazi zenye: kichwa, maelezo, tarehe ya mwisho, mhusika, kipaumbele (juu/kati/chini) na lebo.',
                    'Kusimamia kwa kuburuta na kudondosha : Hamisha kazi kati ya safu wima kwa kuzibubuta. Historia ya mienendo inahifadhiwa.',
                ],
                'tip_sw': 'Unda bodi maalum kwa kila mashindano ya kupanga. Kazi za kawaida (kutenga eneo, kuagiza medali, n.k.) zinaweza kuingizwa kutoka kwenye kiolezo.',
            },
            2: {
                'title_sw': 'Kusimamia kazi za shirika',
                'steps_sw': [
                    'Kiolezo cha mashindano : Tumia kiolezo cha \'Mpangilio wa Mashindano\' chenye kazi za kawaida: usafirishaji, mawasiliano, hakimu, medali, n.k.',
                    'Kugawa kwa wanachama : Gawa kila kazi kwa mwanachama wa timu ya mpangilio. Weka tarehe za mwisho.',
                    'Kufuatilia maendeleo : Asilimia ya maendeleo ya jumla inaonyeshwa juu ya bodi. Kazi zilizomalizika muda zinaangaziwa kwa nyekundu.',
                ],
                'tip_sw': 'Bodi ya Kanban inapatikana kutoka kwenye programu ya simu kusasisha kazi unapokuwa njiani.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 14: Duka la Mtandaoni (mafunzo 2)
    # =========================================================================
    14: {
        'title_sw': 'Duka la Mtandaoni',
        'tutorials': {
            1: {
                'title_sw': 'Kusanidi duka la klabu',
                'steps_sw': [
                    'Kuwezesha duka : Kutoka Mipangilio > Duka, wezesha kipengele cha biashara ya mtandaoni. Unganisha akaunti yako ya Stripe ikiwa bado hujafanya.',
                    'Kuongeza bidhaa : Unda bidhaa zako: jina, maelezo, picha, bei, ukubwa/tofauti zinazopatikana, stoku.',
                    'Kupanga kwa aina : Ainisha bidhaa zako: Sare (kimono, dobok, glavu), Vifaa (kinga, mifuko), Vifaa vidogo (kanda, alama), Bidhaa za chapa.',
                    'Kuchapisha duka : Duka lako linapatikana kutoka kwenye ukurasa wa umma wa klabu yako. Shiriki kiungo au msimbo wa QR.',
                ],
                'tip_sw': 'Toa vifurushi (kimono + ukanda + mfuko) kwa punguzo kuongeza wastani wa tiketi.',
            },
            2: {
                'title_sw': 'Kufanya agizo',
                'steps_sw': [
                    'Kuvinjari duka : Kutoka kwenye ukurasa wa klabu yako, fikia duka. Vinjari bidhaa kwa aina.',
                    'Kuongeza kwenye kikapu : Chagua ukubwa/tofauti na uongeze kwenye kikapu. Kikapu kinahifadhiwa kati ya vipindi.',
                    'Kuagiza na kulipa : Thibitisha kikapu chako, chagua njia ya utoaji (kuchukua dojo au kusafirishwa kwa posta) na ulipe mtandaoni.',
                    'Kufuatilia agizo : Pokea arifa kwa kila hatua: agizo limethibitishwa, linaandaliwa, liko tayari kuchukuliwa / limetumwa.',
                ],
                'tip_sw': 'Hali ya \'Kuchukua Dojo\' inaepuka gharama za usafirishaji. Kocha atakupa agizo lako katika darasa linalofuata.',
            },
        },
    },

    # =========================================================================
    # Sehemu ya 15: Vipengele vya Juu (mafunzo 5)
    # =========================================================================
    15: {
        'title_sw': 'Vipengele vya Juu',
        'tutorials': {
            1: {
                'title_sw': 'Kusanidi matangazo ya mashindano',
                'steps_sw': [
                    'Kuandaa matangazo : Unda tukio la moja kwa moja kwenye YouTube, Twitch au Facebook. Nakili URL ya matangazo na ufunguo wa matangazo.',
                    'Kusanidi katika MartialComp : Kutoka kwenye mashindano, nenda Mipangilio > Matangazo. Bandika URL na uwezesha kuonyesha kwenye ukurasa wa umma.',
                    'Picha ya juu ya alama : Wezesha picha ya juu ya MartialComp inayoonyesha alama za moja kwa moja kwenye matangazo ya video. Binafsisha nafasi na mtindo.',
                    'Kuanza na kujaribu : Anza matangazo na uthibitishe kuwa picha ya juu inafanya kazi. Watazamaji wataona alama za moja kwa moja kwenye matangazo.',
                ],
                'tip_sw': 'Matangazo yenye picha ya juu ya alama za MartialComp hutoa muonekano wa kitaalamu hata kwa mashindano madogo.',
            },
            2: {
                'title_sw': 'Kutumia programu ya simu',
                'steps_sw': [
                    'Kupakua programu : Tafuta \'MartialComp\' kwenye Play Store (Android) au App Store (iOS). Sakinisha na ufungue.',
                    'Kuingia : Ingia na akaunti yako ya MartialComp iliyopo. Unaweza pia kutumia kuingia kwa Google, Facebook au Apple.',
                    'Kugundua kiolesura cha simu : Programu inatoa: wasifu, matokeo, kalenda, arifa za push, msimbo wa QR wa kibinafsi na usajili wa mashindano.',
                    'Hali ya nje ya mtandao : Data muhimu (wasifu, daraja, leseni) inapatikana bila muunganisho. Usawazishaji wa kiotomatiki unaporejelea.',
                ],
                'tip_sw': 'Wezesha arifa za push kupokea tahadhari za matokeo ya moja kwa moja wakati wa mashindano.',
            },
            3: {
                'title_sw': 'Kubadilisha jukumu kwenye programu',
                'steps_sw': [
                    'Kufikia kichaguzi cha jukumu : Gusa picha yako ya wasifu juu ya skrini au telezesha kutoka kushoto kufungua menyu ya pembeni.',
                    'Kuchagua jukumu : Orodha yako ya majukumu inaonekana: Kocha, Mwanafunzi, Hakimu, Msimamizi wa Klabu. Gusa jukumu unalotaka.',
                    'Kiolesura kilichobadilishwa : Dashibodi na menyu zinasasishwa mara moja kuonyesha jukumu lililochaguliwa.',
                ],
                'tip_sw': 'Unaweza kuwa kocha katika klabu moja na mwanafunzi katika nyingine. Kila jukumu limefungamanishwa na shirika lake.',
            },
            4: {
                'title_sw': 'Kuingiza/Kusafirisha data kwa kina',
                'steps_sw': [
                    'Muundo unaotumika : MartialComp inasaidia kuingiza na kusafirisha katika CSV, Excel (XLSX), JSON na PDF. Kila moduli ina chaguo zake.',
                    'Kuingiza na kuoanisha : Kiolesura cha kuoanisha kinaruhusu kuunganisha muundo wowote wa faili na sehemu za MartialComp.',
                    'Kusafirisha kwa kawaida : Chagua sehemu za kusafirisha, vichujio na muundo. Panga usafirishaji wa kiotomatiki unaorudiwa.',
                    'Operesheni za wingi : Operesheni za wingi zinaruhusu marekebisho ya wingi ya: daraja, kundi, hali ya usajili, n.k.',
                ],
                'tip_sw': 'Kusafirisha JSON ni bora kwa kuunganisha na mifumo ya watu wengine (tovuti, programu ya nje, CRM).',
            },
            5: {
                'title_sw': 'Kusimamia hakimu wa dharura (watu wa kujitolea)',
                'steps_sw': [
                    'Kuunda hakimu wa muda : Siku ya mashindano, kutoka Hakimu > Ongeza mtu wa kujitolea, unda wasifu wa muda: jina, klabu na utaalamu.',
                    'Kugawa PIN : PIN ya kipekee inatengenezwa kiotomatiki. Mtu wa kujitolea anatumia PIN hii kufikia kiolesura cha alama.',
                    'Kugawa kwa aina : Gawa hakimu wa kujitolea kwenye aina kama hakimu wa kawaida. Anaweza kuanza kutathmini mara moja.',
                    'Baada ya mashindano : Wasifu wa muda unawekwa kumbukumbuni baada ya mashindano. Alama zinahifadhiwa katika historia.',
                ],
                'tip_sw': 'Hakimu wa dharura ni muhimu kwa mashindano madogo ambapo idadi ya hakimu rasmi ni ndogo.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to Swahili (hardcoded translations)'

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

            section.title_sw = sec_data['title_sw']
            if not dry_run:
                section.save(update_fields=['title_sw'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_sw"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_sw = tut_data['title_sw']
                tutorial.steps_sw = json.dumps(tut_data['steps_sw'], ensure_ascii=False)
                tutorial.tip_sw = tut_data.get('tip_sw', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_sw', 'steps_sw', 'tip_sw'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_sw"]}')

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
