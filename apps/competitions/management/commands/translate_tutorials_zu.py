"""
Management command to translate all 81 tutorials from French to Zulu (isiZulu).
Updates title_zu, steps_zu, and tip_zu fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_zu
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Isigaba 1: Ukubhaliswa Nokuqala (7 izifundo)
    # =========================================================================
    1: {
        'title_zu': 'Ukubhaliswa Nokuqala',
        'tutorials': {
            1: {
                'title_zu': 'Dala i-akhawunti yakho ukhethe indima yakho',
                'steps_zu': [
                    'Finyelela ku-MartialComp : Iya ku-martialcomp.com bese uchofoza ku-\'Bhalisela mahhala\'. Ungakwazi futhi ukulanda uhlelo lokusebenza lweselula ku-Play Store noma ku-App Store.',
                    'Gcwalisa ifomu lokubhalisa : Faka isibongo sakho, igama, i-imeyili nephasiwedi. Ungakwazi futhi ukubhalisa nge-Google, iFacebook noma i-Apple ID ukuze uthole ukufinyelela okulula.',
                    'Khetha indima yakho eyinhloko : Khetha indima yakho: Umphathi Wekilabhu, Umqeqeshi, Umahluleli/Unrefereli, Umzileli noma Umphathi Wenhlangano. Lesi sinqumo sinquma iphaneli yakho yokulawula nezici, kodwa ungakwazi ukwengeza ezinye izindima kamuva.',
                    'Qinisekisa i-imeyili yakho : Bheka ibhokisi lakho lemiyalezo engenayo bese uchofoza isixhumanisi sokuqinisekisa. I-akhawunti yakho iyasebenza futhi ungakwazi ukufinyelela iphaneli yakho eqondiswe ngqo.',
                ],
                'tip_zu': 'Ungaba nezindima eziningi (isib. umqeqeshi KANYE nomzileli). Shintsha phakathi kwezindima zakho kusuka kumenyu esohlangothini nganoma yisiphi isikhathi.',
            },
            2: {
                'title_zu': 'Dala ikilabhu yakho',
                'steps_zu': [
                    'Qala umsizi wokudala : Kusuka ephanelini yakho yokulawula, chofoza ku-\'Dala ikilabhu\'. Umsizi wokumisa ngezinyathelo ezi-4 uqala ngokuzenzakalelayo.',
                    'Ulwazi oluvamile : Faka igama lekilabhu, isifinyezo, ikheli eligcwele nemininingwane yokuxhumana (ucingo, i-imeyili, iwebhusayithi). Engeza ilogo yakho ngefomethi ye-PNG noma ye-JPG (usayizi onconyiwe: 500x500px).',
                    'Khetha imidlalo yomzimba : Khetha umudlalo owodwa noma ngaphezulu phakathi kwezi-14+ ezitholakalayo: iKarate, iJudo, iBJJ, iTaekwondo, iMMA, iKung Fu, i-Aikido, iKendo, iMuay Thai, iBhokisi, iCapoeira, njll.',
                    'Qondanisa i-subdomain yakho : Khetha ikheli lakho eliyingqayizivele: ikilabhu-yakho.martialcomp.com. Leli lizoba yikheli lomphakathi lekilabhu yakho, elifinyeleleka kuwo wonke umuntu.',
                    'Misa izinketho : Beka amahora okuvula, engeza incazelo nezithombe zedojo yakho. Vula noma uvale ukubhaliswa kwe-inthanethi kwabazileli.',
                ],
                'tip_zu': 'Ikilabhu yakho idalwa ngePlani Lamahhala (kuya kumalungu ayi-10). Zonke izici zitholakala kusukela ekuqaleni. Thuthukela ku-Premium uma udlula amalungu ayi-10.',
            },
            3: {
                'title_zu': 'Dala inhlangano yakho',
                'steps_zu': [
                    'Cela ukudalwa : Khetha indima ethi \'Umphathi Wenhlangano\' ngesikhathi sokubhaliswa noma uyengeze kusuka ezilungiselelweni. Gcwalisa ifomu lokudala nolwazi olusemthethweni lwenhlangano yakho.',
                    'Ulwazi olusemthethweni : Faka igama eligcwele, isifinyezo, izwe, imidlalo yomzimba ehlanganisiwe, inombolo yokubhaliswa esemthethweni nemininingwane yokuxhumana.',
                    'Misa isayithi somphakathi : Qondanisa ikhasi lakho lomphakathi: ibhena, ilogo, imibala, incazelo, igalari yezithombe nezixhumanisi zamanethiwekhi akho okuxhumana.',
                    'Chaza isakhiwo : Misa amaliigi akho ezifunda uma kusebenza, chaza izigaba zokuzihlanganyela kwezinhlangano zamaklilobhu nezintengo zemali yobulungu.',
                ],
                'tip_zu': 'Izinhlangano zinendawo yokuphatha ebanzi ukuze ziqaphe zonke izinhlangano zamaklilobhu ezihlanganyelwe, imincintiswano namazinga.',
            },
            4: {
                'title_zu': 'Misa iphrofayili yakho yomqeqeshi',
                'steps_zu': [
                    'Finyelela iphrofayili yomqeqeshi : Kusuka kumenyu esohlangothini, chofoza ku-\'Iphrofayili Yami Yomqeqeshi\'. Uma ungakabi nayo indima yomqeqeshi, yengeze kusuka kuZilungiselo > Izindima Zami.',
                    'Faka iziqu zakho : Engeza amadiploma akho (BPJEPS, DEJEPS, CQP, njll.), amazinga akho kumudlalo ngamunye neminyaka yakho yolwazi.',
                    'Chaza imidlalo yakho yomzimba : Khetha imidlalo yomzimba oyifundisayo kanye nezinga lakho lokugxila kumudlalo ngamunye (abaqalayo, abathuthukile, umncintiswano).',
                    'Beka ukutholakala kwakho : Khombisa izikhathi zakho zeviki zokufundisa. Lolu lwazi luzobonakala emaklilobhini afuna abaqeqeshi.',
                ],
                'tip_zu': 'Iphrofayili yomqeqeshi egcwele enesithombe nezitifiketi ikhuphula kakhulu ukubonakala kwakho emaklilobhini.',
            },
            5: {
                'title_zu': 'Misa iphrofayili yakho yokwahlulela',
                'steps_zu': [
                    'Vula indima yokwahlulela : Kusuka kuZilungiselo > Izindima Zami, vula indima ethi \'Umahluleli / Unrefereli\'. Faka inombolo yakho yelayisensi yokwahlulela uma isebenza.',
                    'Engeza iziqu zakho : Khombisa izinga lakho lokwahlulela (lesifunda, lesizwe, lamazwe ngamazwe), imidlalo yomzimba oyifanelekele nezitifiketi zakho.',
                    'Chaza okukhethekile kwakho : Ikata/amasu, ukulwa, ukuskosha kwezobuciko... Okukhethekile ngakunye kukuvumela imincintiswano ehambisanayo.',
                    'Faka ukutholakala kwakho : Khombisa izindawo zakho zendawo nezikhathi zokutholakala kwemincintiswano.',
                ],
                'tip_zu': 'Abahleli bemincintiswano bazokwazi ukukufuna bakumeme ngqo ngokusukela eziqu nasekutholakaleni kwakho.',
            },
            6: {
                'title_zu': 'Misa iphrofayili yakho yomzileli',
                'steps_zu': [
                    'Gcwalisa ulwazi lomuntu siqu : Faka usuku lwakho lokuzalwa, ubulili, isisindo (sezigaba zomncintiswano), ubude nesithombe sephrofayili.',
                    'Engeza izinga lakho lamanje : Khombisa umudlalo wakho oyinhloko womzimba, izinga lakho lamanje (ibhande), usuku lokutholwa kanye nenhlangano eyalinikeza.',
                    'Faka ilayisensi yakho : Engeza inombolo yakho yelayisensi yenhlangano, usuku lokuphelelwa yisikhathi nesitifiketi samanje sezokwelapha.',
                    'Oxhumana nabo uma kuphuthuma : Engeza okungenani oxhumana naye oyedwa uma kuphuthuma (kudingekile emincintiswanweni): igama, ucingo, ubudlelwano.',
                ],
                'tip_zu': 'Iphrofayili egcwele iyadingeka ukuze ubhalisele imincintiswano. Isisindo nezinga kunquma ngokuzenzakalelayo isigaba sakho.',
            },
            7: {
                'title_zu': 'Qonda iphaneli yokulawula nokuzulazula',
                'steps_zu': [
                    'Iphaneli yokulawula : Iphaneli yakho ibonisa isifinyezo esiqondiswe ngqo: imicimbi ezayo, imilayezo yakamuva, izibalo ezisheshayo nezindlela ezisheshayo zezenzo zakho ezijwayelekile.',
                    'Ibha esohlangothini : Imenyu esohlangothini inikeza ukufinyelela kuzo zonke izingxenye: Amalungu, Imincintiswano, Amazinga, Ezezimali, Ikhalenda, Izilungiselo. Iqondaniswa nendima yakho esebenzayo.',
                    'Shintsha indima : Uma unezindima eziningi (isib. umqeqeshi + umzileli), chofoza ku-avatar yakho phezulu ngakwesokudla ukuze ushintshe. Iphaneli nemenyu kuziqondanisa ngokuzenzakalelayo.',
                    'Izaziso nemilayezo : Isithonjana sensimbi phezulu ngakwesokudla sibonisa izaziso zakho: ukubhalisa, imiphumela, imilayezo. Misa okuthandayo kwezaziso ezilungiselelweni.',
                    'Ukusesha okuvamile : Sebenzisa ibha yokusesha ukuze uthole ngokushesha umzileli, ikilabhu, umncintiswano noma umcimbi.',
                ],
                'tip_zu': 'Qondanisa iphaneli yakho ngokubeka ama-widget akho owathandayo. Indlela emfishane yekhibhodi u-Ctrl+K ivula ukusesha okusheshayo.',
            },
        },
    },

    # =========================================================================
    # Isigaba 2: Ukuphatha Ikilabhu (10 izifundo)
    # =========================================================================
    2: {
        'title_zu': 'Ukuphatha Ikilabhu',
        'tutorials': {
            1: {
                'title_zu': 'Engeza abazileli ngesandla',
                'steps_zu': [
                    'Vula ifomu lokungena : Kusuka kuMalungu > Engeza umzileli, gcwalisa ifomu: isibongo, igama, usuku lokuzalwa, ubulili, i-imeyili nocingo.',
                    'Ulwazi olwengeziwe : Engeza izinga lamanje, inombolo yelayisensi, isithombe somazisi (okukhethwa) nesitifiketi sezokwelapha.',
                    'Abele eqenjini : Abele umzileli eqenjini lokuziqeqesha elilodwa noma ngaphezulu (isib. iKarate Abadala Abathuthukile, iJudo Izingane Abaqalayo).',
                    'Thumela isimemo : Maka \'Thumela i-imeyili yesimemo\' ukuze umzileli akwazi ukudala i-akhawunti yakhe afinyelele iphrofayili yakhe ye-inthanethi.',
                ],
                'tip_zu': 'Umzileli uzothola i-imeyili enesixhumanisi sokuqedela ukubhaliswa kwakhe nokulanda uhlelo lokusebenza lweselula.',
            },
            2: {
                'title_zu': 'Ukungeniswa ngobuningi kwabazileli (CSV/Excel)',
                'steps_zu': [
                    'Landa isifanekiso : Kusuka kuMalungu > Ngenisa, landa isifanekiso se-CSV noma se-Excel. Ifayela liqukethe izinhla ezidingekayo: Isibongo, Igama, Usuku_lokuzalwa, I-imeyili, nezinhla ezikhethwayo: Izinga, Ilayisensi, Ucingo.',
                    'Gcwalisa ifayela : Gcwalisa ifayela ngedatha yabazileli bakho. Hlonipha amafomethi: izinsuku nge-DD/MM/YYYY, amazinga njengombhalo (isib. \'Ibhande eliluhlaza\', \'uDan wesi-2\').',
                    'Layisha futhi uhlanganise izinhla : Ngenisa ifayela. Isixhumi esobuso sokuhlanganisa sikuvumela ukuxhumanisa inhla ngayinye yefayela lakho namangeno e-MartialComp. Hlola ukuhlanganiswa.',
                    'Qinisekisa ulungise : I-MartialComp ithola amaphutha (okungatholakala kabili, amafomethi angalungile). Lungisa imigqa enamaphutha noma uyeqe. Qinisekisa ukungeniswa.',
                ],
                'tip_zu': 'Ungakwazi ukungenisa kuya kwabazileli abangu-500 ngomsebenzi owodwa. Ukungeniswa kuthola ngokuzenzakalelayo okungatholakala kabili nge-imeyili noma isibongo + igama + usuku lokuzalwa.',
            },
            3: {
                'title_zu': 'Phatha amakhadi abazileli',
                'steps_zu': [
                    'Finyelela ikhadi : Kusuka ohlwini lwamalungu, chofoza igama lomzileli ukuze uvule ikhadi lakhe eligcwele.',
                    'Buka imininingwane : Ikhadi libonisa: ulwazi lomuntu siqu, umlando wamazinga, imincintiswano eyenziwe, ukuza izinkokhelo.',
                    'Hlela ulwazi : Chofoza ku-\'Hlela\' ukuze ubuyekeze idatha. Izinguquko zibhaliswa emlandweni.',
                    'Izenzo ezisheshayo : Kusuka ekhadi ungakwazi: ukubhalisa emncintiswanweni, ukuabela izinga, ukuthumela umyalezo, ukukhiqiza isitifiketi.',
                ],
                'tip_zu': 'Sebenzisa izihluzi ezithuthukile (izinga, iminyaka, ilayisensi esebenzayo, inkokhelo ekhokhelwe) ukuze uthole umzileli ngokushesha.',
            },
            4: {
                'title_zu': 'Dala i-akhawunti yomsebenzisi yomzileli',
                'steps_zu': [
                    'Finyelela ikhadi lomzileli : Vula ikhadi lomzileli olufanelekile kusuka ohlwini lwamalungu.',
                    'Xhumanisa ne-akhawunti : Chofoza ku-\'Dala i-akhawunti yomsebenzisi\'. I-imeyili yesimemo izothunyelwa kumzileli enesixhumanisi sokudala iphasiwedi yakhe.',
                    'Beka izimvume : Khetha okungakwazi ukukwenza umzileli: ukubuka imiphumela yakhe, ukubhalisela imincintiswano, ukubuka ikhalenda, ukukhokha nge-inthanethi.',
                ],
                'tip_zu': 'Abazileli abangaphansi kweminyaka bangaba ne-akhawunti exhunywe kweyomzali ngesici seQembu Lomndeni.',
            },
            5: {
                'title_zu': 'Phatha izindima nezimvume zekilabhu',
                'steps_zu': [
                    'Finyelela ukuphathwa kwezindima : Kusuka kuZilungiselo > Izindima Nezimvume, buka izindima ezitholakalayo: Umphathi, Unobhala, Umgcinimafa, Umqeqeshi, Ilungu.',
                    'Abela indima : Khetha ilungu bese ulabela indima. Indima ngayinye inikeza ukufinyelela ezicini ezithile.',
                    'Qondanisa izimvume : Ngendima ngayinye, chaza amalungelo: ukufunda kuphela, ukuhlela, ukususa, ukufinyelela ezezimali, ukuphatha ukubhaliswa.',
                    'Hlola ukufinyelela : Bheka irekhodi lemisebenzi ukuze ubone ukuthi ubani wenzeni nini ekuphathweni kwekilabhu.',
                ],
                'tip_zu': 'Indima yoMphathi inayo yonke amalungelo. Dala indima kaNobhala enokufinyelela kumalungu nasekhalendeni kodwa hhayi kwezezimali.',
            },
            6: {
                'title_zu': 'Ukuqapha ukuza / Ukubhaliswa kokufika',
                'steps_zu': [
                    'Dala iseshini : Kusuka kuKuza > Iseshini Entsha, khetha iqembu lokuziqeqesha, usuku nesikhathi seklasi.',
                    'Bhalisela ngohlwini : Bonisa uhlu lwamalungu eqembu bese umaka abakhona. Ukubhalisa kwenziwa ngokuthinta okukodwa kuselula.',
                    'Bhalisela ngekhodi ye-QR : Bonisa ikhodi ye-QR yeseshini. Abazileli bayiskena ngomakhalekhukhwini wabo lapho befika edojo.',
                    'Buka izibalo : Buka amazinga okuza ngomzileli, iqembu nenkathi. Bona ukungabikho okuphindaphindiwe.',
                ],
                'tip_zu': 'Ukubhaliswa kokufika ngekhodi ye-QR yindlela esheshayo kunamaqembu amakhulu. Ikhodi yenziwa kabusha iseshini ngayinye ukuze kugwenywe ukukhohlisa.',
            },
            7: {
                'title_zu': 'Phatha izinhlelo zokuqeqesha',
                'steps_zu': [
                    'Dala uhlelo : Kusuka kuZinhlelo > Olusha, chaza igama, umudlalo womzimba, izinga (omusha, ophakathi nendawo, othuthukile) nobude bomjikelezo.',
                    'Hlela izeseshini : Engeza izikhathi zeviki: usuku, isikhathi sokuqala, isikhathi sokuphela, iholo/itatami, umqeqeshi ophethe.',
                    'Chaza okuqukethwe : Ngeseshini ngayinye, engeza uhlelo: ukufudumala, umsebenzi wamasu, ukuziqeqesha/irandori, ukuphumula. Namathisela amafayela noma amavidiyo.',
                    'Shicilela wazise : Shicilela uhlelo. Abazileli beqembu bathola isaziso esinomhlelo ogcwele.',
                ],
                'tip_zu': 'Phinda uhlelo olukhona ukuze udale ngokushesha umjikelezo omusha onokuguquka.',
            },
            8: {
                'title_zu': 'Khiqiza usebenzise amakhodi e-QR ekilabhu',
                'steps_zu': [
                    'Khiqiza ikhodi ye-QR yekilabhu : Kusuka kuZilungiselo > Amakhodi e-QR, khiqiza ikhodi ye-QR yekilabhu yakho. Ivumela izivakashi ukufinyelela ngqo ikhasi lakho lomphakathi.',
                    'Amakhodi e-QR akhethekile : Khiqiza amakhodi e-QR a-: ukubhalisa kwe-inthanethi, ukubhaliswa kokufika kweseshini, ikhasi lomcimbi noma isixhumanisi sohlelo lokusebenza lweselula.',
                    'Phrinta ubeke : Landa amakhodi e-QR ngomfanekiso ophezulu ukuze uphrinthe. Amafomethi atholakalayo: PNG, SVG, PDF (A4 noma ikhadi lebhizinisi).',
                    'Qapha izibalo : Buka inombolo yokuSkena ngekhodi ye-QR, ngosuku nangohlobo. Bona amakhodi e-QR aphumelela kakhulu.',
                ],
                'tip_zu': 'Beka ikhodi ye-QR yokubhaliswa emnyango wedojo yakho. Ukuskena ngakunye kungumthengi ongaba khona!',
            },
            9: {
                'title_zu': 'Cela ukuhlanganyela nenhlangano',
                'steps_zu': [
                    'Thola inhlangano yakho : Kusuka kuKilabhu > Ukuhlanganyela, sesha inhlangano yakho ngegama, umudlalo womzimba noma izwe.',
                    'Thumela isicelo : Gcwalisa ifomu lokuhlanganyela: ulwazi lwekilabhu, inombolo yokubhaliswa, amadokhumenti afunekayo (imithetho, umshwalense, njll.).',
                    'Qapha isimo : Isicelo sakho sidlula ezinyathelweni: Sithunyelwe > Kubuyekezwa > Samukelwe/Senqatshwe. Uthola izaziso isinyathelo ngasinye.',
                    'Vuselela isizini ngasinye : Ukuhlanganyela kungesesizini. Isikhumbuzo esizenzakalelayo sithunyelwa izinsuku ezingu-30 ngaphambi kokuphelelwa.',
                ],
                'tip_zu': 'Ukuhlanganyela kukunikeza ukufinyelela emincintiswanweni esemthethweni yenhlangano nokuphathwa okuhlangene kwamalayisensi.',
            },
            10: {
                'title_zu': 'Phatha ukudluliswa kwabazileli',
                'steps_zu': [
                    'Qala ukudluliswa : Kusuka ekhadi lomzileli, chofoza ku-\'Cela ukudluliswa\'. Khetha ikilabhu lapho kuya khona nesizathu sokudluliswa.',
                    'Inqubo yokuqinisekisa : Ikilabhu lapho kuya khona ithola isicelo futhi ingasamukela noma isenqabe. Uma inhlangano ihilelekile, nayo kufanele iqinisekise.',
                    'Ukudluliswa okusebenzayo : Uma kuqinisekisiwe, umzileli udluliselwa ngokuzenzakalelayo nezinga lakhe nomlando wemincintiswano.',
                    'Buka umlando : Umlando wokudluliswa ubonakala ekhadi lomzileli nasemibikweni yekilabhu.',
                ],
                'tip_zu': 'Ezinye izinhlangano zibeka izikhathi zokudluliswa (amawindi okudlulisa). I-MartialComp ihlonipha ngokuzenzakalelayo le mithetho.',
            },
        },
    },

    # =========================================================================
    # Isigaba 3: Imincintiswano - Ukudalwa Nokumiswsa (6 izifundo)
    # =========================================================================
    3: {
        'title_zu': 'Imincintiswano - Ukudalwa Nokumiswa',
        'tutorials': {
            1: {
                'title_zu': 'Dala umncintiswano womuntu ngamunye',
                'steps_zu': [
                    'Qala ukudalwa : Kusuka kuMincintiswano > Dala, khetha uhlobo oluthi \'Ngamunye\'. Faka igama, umudlalo/imidlalo yomzimba, izinsuku nendawo.',
                    'Chaza ifomethi : Khetha ifomethi: Ukulwa (kumite, randori, sparring), Okwamasu (kata, poomsae, amafomu) noma Okuxubile (kokubili).',
                    'Misa izigaba : Chaza izigaba ngobulili, ibanga leminyaka, isisindo kanye/noma izinga. I-MartialComp inikeza izifanekiso zezigaba ezijwayelekile ngomudlalo womzimba.',
                    'Izinketho nokushicilela : Vula izinketho ozithandayo: ukubhaliswa kwe-inthanethi, ukukhokha, ukusakaza bukhoma, imiphumela yomphakathi. Shicilela umncintiswano.',
                ],
                'tip_zu': 'Sebenzisa izifanekiso zezigaba (WKF, IJF, ITF...) ukuze wonge isikhathi. Ungakwazi ukuziqondanisa ngemva kokudalwa.',
            },
            2: {
                'title_zu': 'Dala umncintiswano wamaqembu (Sincro/Song Luyen)',
                'steps_zu': [
                    'Khetha imodi yeqembu : Ngesikhathi sokudalwa, khetha uhlobo oluthi \'Iqembu\'. Chaza inombolo encane nenkulu yamalungu eqembu ngalinye.',
                    'Misa ifomethi yeqembu : Khetha ifomethi: Ukuvumelana (kata/poomsae yeqembu), iSong Luyen (ukulwa okulungiswe ngaphambili kwababili) noma Ukulwa Ngamaqembu (ukushintshana).',
                    'Chaza ukwakheka : Cacisa izindima ngaphakathi kweqembu: inani labadlali abaqala, inani labadlali abangenayo, ukuthi ukuxuba kuvumelekile yini noma cha.',
                    'Imilinganiselo yokuskosha yeqembu : Ngokuskosha kwamasu, chaza ukuthi abahluleli bahlulela iqembu lonke noma ilungu ngalinye ngokwahlukana.',
                ],
                'tip_zu': 'Imodi yeSincro ivumela ukuskosha okunemigomo ekhethekile yokuvumelana (isikhathi, ukuqondana, ukukhombisa okwabelwana).',
            },
            3: {
                'title_zu': 'Misa izigaba zomncintiswano',
                'steps_zu': [
                    'Finyelela ukuphathwa kwezigaba : Kusuka emncintiswanweni odalwe, iya ethebhini Lezigaba. Chofoza ku-\'Engeza isigaba\'.',
                    'Chaza imilinganiselo : Ngesigaba ngasinye, chaza: ubulili (M/F/Okuxubile), ibanga leminyaka (isib. iminyaka eyi-12-14), ibanga lesisindo (isib. -60kg), izinga elincane/elikhulu.',
                    'Qamba isigaba : Linike igama elicacile: \'Abasha Besilisa -52kg\' noma \'Kata Abadala Besifazane Abathuthukile\'. I-MartialComp ikhiqiza amagama azenzakalelayo uma uthanda.',
                    'Hlela izigaba : Hlela kabusha izigaba ngokuhudula nokwehlisa ukuze umise ukuhlala kosuku lomncintiswano.',
                ],
                'tip_zu': 'Ngenisa izigaba zomncintiswano owedlule ukuze wonge isikhathi. Sebenzisa inketho \'Ukuphindaphinda Okuhlakaniphile\' ukuze udale izinhlobo.',
            },
            4: {
                'title_zu': 'Phinda umncintiswano okhona',
                'steps_zu': [
                    'Thola umncintiswano womsuka : Kusuka kuMincintiswano > Umlando, thola umncintiswano ofuna ukuwuphinda.',
                    'Qala ukuphinda : Chofoza kumachashazi ama-3 > Phinda. Khetha okufanele kukopishwe: izigaba, umthetho, ukumiswa, izintengo.',
                    'Lungisa ukumiswa : Shintsha izinsuku, indawo nemingcele edingekayo. Izigaba nomthetho kukopishwa ngokufanayo.',
                ],
                'tip_zu': 'Kulungele imincintiswano yonyaka ephindaphindayo. Phinda uhlobo lwangaphambili bese uyavela ubuyekeze izinsuku.',
            },
            5: {
                'title_zu': 'Misa izinketho zokubonakala',
                'steps_zu': [
                    'Finyelela ukumiswa kokubonakala : Kusuka emncintiswanweni, iya kuZilungiselo > Ukubonakala Nokwabelana.',
                    'Ukubhaliswa kwe-inthanethi : Vula/vala ukubhaliswa komphakathi. Beka izinsuku zokuvulwa nokuvala kokubhaliswa.',
                    'Imiphumela nezikhundla : Khetha uma imiphumela ingeyomphakathi ngesikhathi sangempela, ishicilelwe ngemva kokuqinisekiswa noma iyimfihlo (umhleli kuphela).',
                    'Ukusakaza bukhoma : Vula imodi yokusakaza bese wengeza isixhumanisi se-YouTube/Twitch/Facebook Live ukuze siboniswe ekhasini lomphakathi.',
                ],
                'tip_zu': 'Imiphumela ebukhoma iheha ababukeli ekhasini lakho futhi ikhuphula ukubonakala kwekilabhu noma inhlangano yakho.',
            },
            6: {
                'title_zu': 'Misa imithetho yokulwa',
                'steps_zu': [
                    'Khetha umthetho : Khetha umthetho olungiswe ngaphambili (WKF, IJF, ITF, IBJJF, njll.) noma udale owakho oqondanisiwe.',
                    'Chaza ukuskosha : Misa izenzo namaphuzu azo: Yuko (1pt), Waza-ari (2pts), Ippon (3pts), njll. Engeza izijeziso (Shido, Hansoku, njll.).',
                    'Misa amarawundi : Chaza ubude bamarwundi, inombolo yamarwundi, izikhefu nezimo zokunqoba (amaphuzu, Ippon, ukuyeka).',
                    'Imithetho ekhethekile : Misa imithetho ekhethekile: iGolden Score (isikhathi esengeziwe), iHantei (isinqumo sabahluleli), ukuphela ngaphambi kwesikhathi ngomahluko wamaphuzu.',
                ],
                'tip_zu': 'Gcina imithetho yakho eqondanisiwe njengezifanekiso ukuze uyisebenzise futhi emincintiswanweni esikhathini esizayo.',
            },
        },
    },

    # =========================================================================
    # Isigaba 4: Ukubhaliswa Namaqembu (7 izifundo)
    # =========================================================================
    4: {
        'title_zu': 'Ukubhaliswa Namaqembu',
        'tutorials': {
            1: {
                'title_zu': 'Bhalisa abazileli emncintiswanweni',
                'steps_zu': [
                    'Thola umncintiswano : Kusuka kuMincintiswano > Evulekele ukubhaliswa, thola umncintiswano odingekayo bese uchofoza ku-\'Bhalisa\'.',
                    'Khetha abazileli : Uhlu lwamalungu akho luboniswa. Khetha umzileli oyedwa noma ngaphezulu. I-MartialComp ikhombisa ngokuzenzakalelayo izigaba ezifanelekele umuntu ngamunye.',
                    'Qinisekisa izigaba : Ngomzileli ngamunye, qinisekisa noma ushintshe isigaba esihlongoziwe. Uhlelo luhlola ukuthi isisindo, iminyaka nezinga kuyahambisana.',
                    'Qinisekisa ukhokhe : Qinisekisa ukubhaliswa. Uma umncintiswano udinga ukukhokha, qhubeka nokukhokha konke ukubhaliswa.',
                ],
                'tip_zu': 'Abazileli abanephrofayili engaphelele (isisindo esingekho, ilayisensi ephelelwe) bazokhonjiswa ngesixwayiso esibomvu.',
            },
            2: {
                'title_zu': 'Ukubhaliswa ngobuningi ngefomu',
                'steps_zu': [
                    'Finyelela imodi yobuningi : Kusuka kusikrini sokubhaliswa, chofoza ku-\'Ukubhaliswa Ngobuningi\'. Khetha isigaba lapho kuya khona.',
                    'Khetha iqembu : Hluza ngeqembu lokuziqeqesha, izinga noma iminyaka. Khetha abazileli abafanelekile ngokuchofoza okukodwa.',
                    'Hlola ulungise : Isikrini sokuhlolwa sibonisa umzileli ngamunye nesigaba sakhe. Lungisa amaphutha uma ekhona.',
                    'Qinisekisa iqoqo : Qinisekisa konke ukubhaliswa ngomsebenzi owodwa. Isifinyezo sithunyelwa nge-imeyili.',
                ],
                'tip_zu': 'Ukubhaliswa ngobuningi kulungele amaklilobhu abhalisa abazileli abangu-10+ emncintiswanweni ofanayo.',
            },
            3: {
                'title_zu': 'Dala uphathi amaqembu',
                'steps_zu': [
                    'Dala iqembu : Kusuka emncintiswanweni, chofoza ku-\'Bhalisa iqembu\'. Linike igama iqembu bese ukhetha isigaba.',
                    'Engeza amalungu : Engeza amalungu eqembu kusuka ohlwini lwakho lwabazileli. Hlonipha izinombolo ezincane nezinkulu ezichazwe.',
                    'Beka abaqalayo nabangenayo : Qoka abaqalayo nabangenayo ngokuhudula nokwehlisa. Ukuhlala kokubonakala kungamiswa lapha.',
                    'Qinisekisa iqembu : Hlola ukuhambisana kweqembu (inombolo yamalungu, izigaba zomuntu ngamunye) bese uqinisekisa ukubhaliswa.',
                ],
                'tip_zu': 'Emincintiswanweni yamaqembu, igama leqembu libonakala emabhodini amaskosha nasemiphumeleni esemthethweni.',
            },
            4: {
                'title_zu': 'Shintsha isigaba seqembu',
                'steps_zu': [
                    'Finyelela iqembu : Kusuka ekubhalisweni kwakho, thola iqembu elidinga ukuguqulwa bese uchofoza ku-\'Hlela\'.',
                    'Shintsha isigaba : Khetha isigaba esisha kumenyu ewela phansi. Uhlelo luhlola ukuthi iqembu liyahambisana nemigomo.',
                    'Qinisekisa ushintsho : Qinisekisa. Uma umncintiswano unezintengo zokubhaliswa ezehlukile ngesigaba, ukulungiswa kwenzeka ngokuzenzakalelayo.',
                ],
                'tip_zu': 'Ukushintsha isigaba kungenzeka kuphela lapho ukubhaliswa kusavuliwe.',
            },
            5: {
                'title_zu': 'Cela isivumelwano (ukuhlangana phakathi kwamaklilobhu)',
                'steps_zu': [
                    'Bona isidingo : Ikilabhu yakho ayinamalungu anele ukwakha iqembu eligcwele? Isivumelwano sivumela ukuhlanganisa amaqembu amaklilobhu ahlukene.',
                    'Dala isicelo sesivumelwano : Kusuka eqenjini elingaphelele, chofoza ku-\'Phakamisa isivumelwano\'. Khetha ikilabhu ehlanganyele nezikhundla ezidingayo ukugcwaliswa.',
                    'Thumela isiphakamiso : Ikilabhu ehlanganyele ithola isicelo emininingwane: umncintiswano, isigaba, izikhundla ezitholakalayo, imibandela.',
                    'Qedela isivumelwano : Uma samukelwe, iqembu elihlanganisiwe libonakala namalungu amaklilobhu womabili. Iqembu lithwala igama elihlanganisa amaklilobhu womabili.',
                ],
                'tip_zu': 'Isivumelwano siphansi kokwamukelwa ngumhleli womncintiswano futhi, uma kusebenza, inhlangano.',
            },
            6: {
                'title_zu': 'Yamukela/nqaba isicelo sesivumelwano',
                'steps_zu': [
                    'Thola isaziso : Uthola isaziso sesicelo sesivumelwano. Chofoza ukuze ubone imininingwane.',
                    'Buyekeza isiphakamiso : Hlola: ikilabhu ecelayo, umncintiswano, isigaba, izikhundla ezidinga ukugcwaliswa nemibandela ephakanyisiwe.',
                    'Yamukela noma nqaba : Chofoza ku-\'Yamukela\' ukuze uqinisekise isivumelwano bese ukhetha amalungu akho, noma ku-\'Nqaba\' nomyalezo wokuchaza.',
                ],
                'tip_zu': 'Ungaphakamisa isiphakamiso esilungisiwe ngokushintsha imibandela ngaphambi kokwamukela.',
            },
            7: {
                'title_zu': 'Phatha ukubhaliswa okutholwe (ukwamukelwa)',
                'steps_zu': [
                    'Finyelela iphaneli yokubhaliswa : Kusuka emncintiswanweni, iya ethebhini Lokubhaliswa. Buka ukubhaliswa ngesimo: Okulindile, Okumukelwe, Okwenqatshiwe.',
                    'Buyekeza wamukele : Chofoza ekubhalisweni ukuze uhlole ulwazi lomzileli. Yamukela ngamunye noma ngobuningi.',
                    'Nqaba nesizathu : Uma kunqatshwa, khetha isizathu: isigaba esingalungile, ilayisensi engalungile, ukubhaliswa okuselwe, njll.',
                    'Thumela uhlu : Thumela uhlu lwababhalisiwe abaqinisekisiwe nge-CSV noma i-PDF ukuze kukalwe isisindo nokuphathwa ngosuku lomncintiswano.',
                ],
                'tip_zu': 'Vula ukwamukelwa okuzenzakalelayo uma ungafuni ukuqinisekisa ngamunye ukubhaliswa ngakunye.',
            },
        },
    },

    # =========================================================================
    # Isigaba 5: Usuku Lomncintiswano - Ukulwa (8 izifundo)
    # =========================================================================
    5: {
        'title_zu': 'Usuku Lomncintiswano - Ukulwa',
        'tutorials': {
            1: {
                'title_zu': 'Khiqiza amaqembu ngokuzenzakalelayo',
                'steps_zu': [
                    'Finyelela ukuphathwa kwamaqembu : Kusuka emncintiswanweni, iya kuMaqembu > Khiqiza Ngokuzenzakalelayo. Khetha izigaba ezidinga ukusetshenzwa.',
                    'Misa ukusatshalaliswa : Chaza: inombolo yabancintiswanayo eqenjini ngalinye, ukwehlukana kwamalungu ekilabhu efanayo, abaholi abanqunywe ngesandla (okukhethwa).',
                    'Khiqiza uhlole : Chofoza ku-\'Khiqiza\'. I-MartialComp isabalalisa abancintiswanayo igwema ukuhlangana phakathi kwekilabhu efanayo erawundini yokuqala.',
                    'Lungisa ngesandla : Uma kudingeka, hambisa abancintiswanayo phakathi kwamaqembu ngokuhudula nokwehlisa. Uhlelo luhlola izingxabano ngesikhathi sangempela.',
                ],
                'tip_zu': 'I-algorithm yokusabalalisa iqinisekisa ubulungiswa ngokuhlukanisa amaklilobhu nokulinganisa amazinga amakhono phakathi kwamaqembu.',
            },
            2: {
                'title_zu': 'Hlela uphinde uhlele amaqembu',
                'steps_zu': [
                    'Umbono wamaqembu wonke : Isikrini samaqembu sibonisa zonke izigaba nenombolo yabancintiswanayo, amaqembu nesimo (isidrafti, kuqinisekisiwe, kuyaqhubeka).',
                    'Hlela iqembu : Chofoza eqenjini ukuze ubone abancintiswanayo. Sebenzisa ukuhudula nokwehlisa ukuze uhambise umncintiswanayo eqenjini elinye.',
                    'Phatha ukungabikho : Maka umncintiswanayo njengongekho noma ohoximule. Uhlelo luphinde lubale ngokuzenzakalelayo ukulwa nezikhundla.',
                    'Qinisekisa amaqembu : Uma wenelisekile, qinisekisa amaqembu. Lesi senzo sikhiqiza ngokuzenzakalelayo ithebula lokuhlangana.',
                ],
                'tip_zu': 'Qinisekisa amaqembu isigaba ngesigaba ukuze uqale ukulwa kwezigaba zokuqala lapho uqedela esinye.',
            },
            3: {
                'title_zu': 'Hlela ikhalenda yomukhulwa',
                'steps_zu': [
                    'Chaza izindawo zokulwa : Kusuka kuHlelo > Izindawo, chaza inombolo yamatami/amaringi atholakalayo namagama awo (iTatami 1, iRingi A, njll.).',
                    'Abela izikhathi : Hudula izigaba phezu kwezindawo nezikhathi. I-MartialComp ibala ngokuzenzakalelayo ubude obulinganiselwe.',
                    'Thola izingxabano : Uhlelo luthola izingxabano: umncintiswanayo obhaliswe ezigabeni ezi-2 ngesikhathi esifanayo. Sebenzisa izexwayiso ukuze ulungise.',
                    'Shicilela uhlelo : Shicilela uhlelo. Abancintiswanayo, abaqeqeshi nabahluleli bathola isaziso nezikhathi zabo zokubamba iqhaza.',
                ],
                'tip_zu': 'Hlela isikhathi esingu-20% esengeziwe ngesigaba ukuze uphathwe ukubambezeleka okungenakugwenywa.',
            },
            4: {
                'title_zu': 'Sebenzisa isixhumi esobuso sokulwa (ukuskosha bukhoma)',
                'steps_zu': [
                    'Xhuma endaweni : Kuthebhulethi noma kumakhalekhukhwini wakho, vula i-MartialComp bese ukhetha indawo yakho yokulwa enikwe yona. Faka iPIN yakho yokwahlulela.',
                    'Isixhumi esobuso sokuskosha : Isikrini sibonisa: abancintiswanayo aba-2 (obomvu/oluhlaza okwesibhakabhaka), izinkinobho zesenzo (amaphuzu, izijeziso), isibali-sikhathi namaphuzu amanje.',
                    'Nika amaphuzu : Cindezela izinkinobho zokuskosha: Yuko (+1), Waza-ari (+2), Ippon (+3) komncintiswanayo obomvu noma oluhlaza okwesibhakabhaka. Amaphuzu abuyekezwa ngesikhathi sangempela.',
                    'Phatha izijeziso : Cindezela Isijeziso ukuze unikeze isexwayiso (Shido) noma ukususwa (Hansoku). Izijeziso ziyahlangana.',
                    'Qeda ukulwa : Isibali-sikhathi sima ngokuzenzakalelayo. Qinisekisa umphumela (ukunqoba ngamaphuzu, Ippon, ukuyeka). Isikhundla sibuyekezwa ngokushesha.',
                ],
                'tip_zu': 'Isixhumi esobuso senzelwe amathebhulethi kwimodi yokuvundleka. Izinkinobho zenzelwe ukuba zibe zinkulu ngamabomu ukuze zisetshenziswe ngokushesha nangaphandle kwamaphutha.',
            },
            5: {
                'title_zu': 'Imodi yeKiosiki yamatatami amaningi',
                'steps_zu': [
                    'Vula imodi yeKiosiki : Kusuka kuZilungiselo > Imodi yeKiosiki, vula imodi bese ubeka ikhodi yePIN endaweni yokulwa ngayinye.',
                    'Misa ithebhulethi ngayinye : Kuthebhulethi ngayinye yendawo, ngena bese ukhetha indawo efanelekile. Faka iPIN ukuze ukhiye isikrini kule ndawo.',
                    'Ukuphathwa okuzimele : Indawo ngayinye isebenza ngokuzimela: ukuskosha, isibali-sikhathi, ukubonisa. Ibhodi yamaskosha ephakathi ibuyekezwa ngesikhathi sangempela.',
                    'Isikrini sababukeli : Xhuma isikrini esengeziwe kwimodi \'Yababukeli\' ukuze ubonise amaskosha ngefomethi enkulu, ebonakala kusuka ezitulweni.',
                ],
                'tip_zu': 'Imodi yeKiosiki ivimbela abahluleli ukuba bazulazule ngephutha ngaphandle kwesixhumi esobuso sokuskosha.',
            },
            6: {
                'title_zu': 'Landela izikhundla bukhoma',
                'steps_zu': [
                    'Iphaneli ebukhoma : Isikrini sokulandela sibonisa ngesikhathi sangempela: ukulwa okwenzekayo ngendawo, izikhundla zamaqembu, ukuqhubeka kwezigaba zokugcina.',
                    'Hluza ngesigaba : Khetha isigaba ukuze ubone imininingwane: amaqembu aqediwe, aqhubekayo nalindile, nezikhundla zesikhashana.',
                    'Izaziso ezizenzakalelayo : Uhlelo lwazisa ngokuzenzakalelayo abaqeqeshi lapho abancintiswanayo babo kufanele bazethule endaweni yokulwa.',
                ],
                'tip_zu': 'Bonisa iphaneli esikrinini esikhulu endaweni yokwamukela ukuze bonke ababamba iqhaza bakwazi ukulandela ukuqhubeka.',
            },
            7: {
                'title_zu': 'Khiqiza izigaba zokugcina (okwesibili kokugcina/okugcina)',
                'steps_zu': [
                    'Amaqembu aqediwe : Uma wonke amaqembu esigaba eqediwe, uhlelo lubala abakhethiwe ngokwemithetho echazwe (owe-1 nowe-2 eqenjini ngalinye, njll.).',
                    'Khiqiza ibhodi : Chofoza ku-\'Khiqiza izigaba zokugcina\'. Ibhodi yokususa (ukukhetha, okwesibili kokugcina, ukugcina, ukugcina kwethusi) ikhiqizwa ngokuzenzakalelayo.',
                    'Phatha ukubuyiswa : Uma imithetho ikubonelela, ukubuyiswa kukhiqizwa ngokuzenzakalelayo nabalahlekile bokwesibili kokugcina.',
                    'Qala okugcina : Ukulwa kwezigaba zokugcina kubonakala ohlelweni. Ukuskosha kusebenza ngendlela efanayo namaqembu.',
                ],
                'tip_zu': 'Ibhodi yokususa ikhiqizwa ngokuzenzakalelayo igwema, uma kungenzeka, ukuhlangana phakathi kwabancintiswanayo bekilabhu efanayo.',
            },
            8: {
                'title_zu': 'Phatha umcimbi wephodiumu',
                'steps_zu': [
                    'Finyelela iphodiumu : Kusuka esigabeni esiqediwe, chofoza ku-\'Iphodiumu\'. Isikhundla sokugcina siboniswa: Igolide, Isiliva, Ithusi (futhi mhlawumbe Ithusi le-2).',
                    'Ukubonisa ngokuqhubeka : Sebenzisa imodi \'Yomcimbi\' ukuze kuboniswe ngokuqhubeka: owe-3, bese owe-2, bese owe-1, nama-animation nemisindo.',
                    'Bonisa esikrinini esikhulu : Xhuma imodi yeNethezeko kuprojektha ukuze kubonakale ngendlela emangalisayo ngesikhathi sokunikezwa kwamamedali.',
                    'Yabelana ngemiphumela : Amaphodiumu ashicilelwa ngokuzenzakalelayo ekhasini lomncintiswano futhi angabelwana ngawo kumanethiwekhi okuxhumana.',
                ],
                'tip_zu': 'Thatha isithombe sephodiumu usengeze emncintiswanweni ukuze ucebise igalari namanethiwekhi okuxhumana.',
            },
        },
    },

    # =========================================================================
    # Isigaba 6: Ukuskosha Kwamasu (6 izifundo)
    # =========================================================================
    6: {
        'title_zu': 'Ukuskosha Kwamasu',
        'tutorials': {
            1: {
                'title_zu': 'Misa imilinganiselo yokuskosha',
                'steps_zu': [
                    'Finyelela imilinganiselo : Kusuka emncintiswanweni, iya kuKuskosha > Imilinganiselo. Khetha isifanekiso noma udale eyakho imilinganiselo.',
                    'Chaza imilinganiselo : Engeza imilinganiselo yokuhlolwa: Amasu (izikhundla, ukuguquka), Amandla (kime, ukuguquguquka), Isigqi (itempo, ukugeleza), Ukukhombisa (zanshin, umoya).',
                    'Abela isisindo : Chaza isisindo somlinganiselo ngamunye: isib. Amasu 40%, Amandla 25%, Isigqi 20%, Ukukhombisa 15%. Isamba kufanele sibe ngu-100%.',
                    'Chaza isikali : Khetha isikali sokuskosha: 1-5, 1-10, 5.0-10.0 noma eqondanisiwe. Chaza ukwanda (0.1, 0.5 noma 1).',
                ],
                'tip_zu': 'Izifanekiso ze-WKF ne-WTF zilungiswe ngaphambili. Ziqondanise ngokwezidingo zakho ezikhethekile.',
            },
            2: {
                'title_zu': 'Abela abahluleli ezigabeni',
                'steps_zu': [
                    'Vula iphaneli yokuabela : Kusuka kuKuskosha > Abahluleli, buka uhlu lwabahluleli ababhalisiwe nezigaba ezidinga ukumbozelwa.',
                    'Abela ngesigaba : Hudula abahluleli ezigabeni. Chaza inombolo yabahluleli ngesigaba (ngokuvamile aba-5 noma aba-7).',
                    'Ukuhlolwa kobungathathi-hlangothi : I-MartialComp ihlola ngokuzenzakalelayo izingxabano zezintshisekelo: umahluleli akakwazi ukuhlulela umncintiswanayo wekilabhu yakhe.',
                    'Phatha ukushintshana : Hlela ukushintshana kwabahluleli phakathi kwezigaba ukuze kugwenywe ukukhathala kuqinisekiswe ubulungiswa.',
                ],
                'tip_zu': 'Uhlelo lokuthola ukukhetha kucubungula umehluko wokuskosha phakathi kwabahluleli bese luxwayisa uma umahluleli eskosha ngokuphezulu noma ngaphansi ngokuphindaphindiwe.',
            },
            3: {
                'title_zu': 'Sebenzisa ikhasi lokuskosha kwamasu',
                'steps_zu': [
                    'Ngena njengomahluleli : Kuthebhulethi yakho, ngena nge-akhawunti yakho yokwahlulela. Khetha isigaba esakho.',
                    'Isixhumi esobuso sokuskosha : Isikrini sibonisa umncintiswanayo wamanje, imilinganiselo yokuhlolwa nekhibhodi yezinombolo. Umlinganiselo ngamunye unesishelelisi noma ikhibhodi yakhe.',
                    'Hlola ngokulandelana : Ngomcintiswanayo ngamunye, faka amaskosha akho kumlinganiselo ngamunye. Qinisekisa ukuhlolwa kwakho ngaphambi kokudlulela kolandelayo.',
                    'Gcina : Ukuhlolwa kwakho kugcinwa ngokushesha. Ungashintsha amaskosha akho uma ukuphenduka kungakakhiywa ngumhleli.',
                ],
                'tip_zu': 'Isixhumi esobuso sedijithali senzelwe ukufaka okusheshayo kumathebhulethi. Ukuthinta okukodwa kumaskosha ngamanye.',
            },
            4: {
                'title_zu': 'Ukuskosha kwamasu kweqembu (iSincro)',
                'steps_zu': [
                    'Qonda imodi yeqembu : Ekuskosheni kweSincro, imilinganiselo eyengeziwe ibonakala: Ukuvumelana, Ukuqondana Kwendawo, Ukukhombisa Okwabelwana.',
                    'Hlola iqembu lonke : Uma kumiswe kanjalo, hlola iqembu lonke kumlinganiselo ngamunye, kufaka phakathi ukuvumelana.',
                    'Hlola ngamunye + iqembu : Uma kumiswe ukuhlolwa okuxubile, hlola ilungu ngalinye ngokwahlukene BESE wengeza iskosha leqembu lokuvumelana.',
                ],
                'tip_zu': 'Kwimodi yeSincro, umlinganiselo wokuvumelana umele ngokuvamile u-20-30% weskosha eliphelele.',
            },
            5: {
                'title_zu': 'Khiya ushicilele amaskosha',
                'steps_zu': [
                    'Hlola amaskosha : Kusuka ephanelini yomhleli, buka amaskosha abo bonke abahluleli ngomcintiswanayo ngamunye. Bona umehluko osolisayo.',
                    'Khiya ukuphenduka : Chofoza ku-\'Khiya\' ukuze kuvimbe noma yikuphi ukushintsha. Ukubala kokugcina (ukususa iskosha eliphezulu/eliphansi, isilinganiso) kwenziwa.',
                    'Shicilela imiphumela : Shicilela izikhundla. Amaskosha enziwe kabanzi ngomahluleli ngamunye angafihlwa noma aboniswe ngokwezilungiselo zakho.',
                    'Imodi yokuhlola / ukusetha kabusha : Ngaphambi komncintiswano, sebenzisa imodi yokuhlola ukuze uhlole uhlelo. Ukusetha kabusha kususa wonke amaskosha okuhlola.',
                ],
                'tip_zu': 'Ukukhiya ngokuphenduka ngakunye kuvumela ukushicilela imiphumela ngokuphenduka ngakunye lapho umncintiswano uqhubeka.',
            },
            6: {
                'title_zu': 'Buka izikhundla zesikhashana',
                'steps_zu': [
                    'Finyelela izikhundla : Kusuka ethebhini Lezikhundla, buka izikhundla ngesikhathi sangempela namaskosha ngomlinganiselo neskosha sokugcina.',
                    'Hlela uhluze : Hlela ngeskosha eliphelele noma ngomlinganiselo okhethekile. Hluza ngeqembu noma bonke abancintiswanayo.',
                    'Izibalo zabahluleli : Buka izibalo: isilinganiso ngomahluleli, ukuphambuka okujwayelekile, ukuthola ukukhetha. Ithuluzi elibalulekile lobulungiswa.',
                ],
                'tip_zu': 'Isikhundla sesikhashana sibonakala kubahleli nabahluleli kuphela. Sishicilelwa kubancintiswanayo kuphela ngemva kokukhiya.',
            },
        },
    },

    # =========================================================================
    # Isigaba 7: Imiphumela Nomlando (4 izifundo)
    # =========================================================================
    7: {
        'title_zu': 'Imiphumela Nomlando',
        'tutorials': {
            1: {
                'title_zu': 'Buka imiphumela yomncintiswano',
                'steps_zu': [
                    'Thola umncintiswano : Kusuka kumenyu yeMincintiswano noma ikhasi lomphakathi, khetha umncintiswano odingekayo.',
                    'Bheka imiphumela : Imiphumela ihlelwe ngesigaba. Ngesigaba ngasinye: iphodiumu, isikhundla esiphelele nemininingwane yamaskosha.',
                    'Imininingwane yokulwa : Chofoza ekulweni ukuze ubone imininingwane: iskosha ngerawundi, izijeziso, isibali-sikhathi futhi mhlawumbe ividyo yokulwa.',
                ],
                'tip_zu': 'Imiphumela yomphakathi ifinyeleleka ngaphandle kwe-akhawunti ye-MartialComp ngesixhumanisi somncintiswano.',
            },
            2: {
                'title_zu': 'Shicilela wabelane ngemiphumela',
                'steps_zu': [
                    'Qinisekisa imiphumela : Kusuka ephanelini yomhleli, buyekeza imiphumela yesigaba ngasinye. Chofoza ku-\'Qinisekisa ushicilele\'.',
                    'Khiqiza isixhumanisi somphakathi : Isixhumanisi esimile sikhiqizwa ekhasi lemiphumela. Sikopishe ukuze usabelane naso.',
                    'Yabelana kumanethiwekhi okuxhumana : Sebenzisa izinkinobho zokwabelana ezakhelwe ngaphakathi ukuze ushicilele ku-Facebook, Instagram, Twitter. Amaphodiumu akhiqiza ngokuzenzakalelayo isithombe.',
                    'Ikhodi ye-QR yemiphumela : Khiqiza ikhodi ye-QR yemiphumela ukuze iboniswe endaweni yomncintiswano yababukeli.',
                ],
                'tip_zu': 'Isithombe esizenzakalelayo sephodiumu sifomethwe sama-Instagram Stories (9:16) ne-Facebook (16:9).',
            },
            3: {
                'title_zu': 'Thumela imiphumela (CSV/PDF)',
                'steps_zu': [
                    'Finyelela ukuthunyelwa : Kusuka kuMiphumela > Thumela, khetha ifomethi: CSV (idatha eluhlaza), PDF (umbiko ofomethwe) noma Excel.',
                    'Khetha okuqukethwe : Khetha: Isikhundla esivamile, Amaphodiumu kuphela, Imininingwane ngesigaba, Umbiko wamamedali ngekilabhu noma Konke.',
                    'Qondanisa i-PDF : Nge-PDF, khetha isifanekiso: umbiko osemthethweni (onelogo yenhlangano), umbiko olula noma amadiploma.',
                ],
                'tip_zu': 'Umbiko wamamedali ngekilabhu ulusizo kakhulu ezinhlanganweni nakwabaxhasi.',
            },
            4: {
                'title_zu': 'Bheka umlando wakho wemiphumela',
                'steps_zu': [
                    'Finyelela kuMlando Wami : Kusuka ephrofayili yakho yomzileli, chofoza ku-\'Umlando\'. Umlando wakho wemincintiswano uboniswa.',
                    'Buka izibalo : Bheka: inombolo yemincintiswano, amamedali (igolide/isiliva/ithusi), iphesenti lokunqoba, ukuqhubeka ngesikhathi.',
                    'Yabelana ngomlando wakho : Khiqiza isixhumanisi somphakathi emlandweni wakho noma uyithumele nge-PDF yamafayela okufaka isicelo noma uxhaso.',
                ],
                'tip_zu': 'Umlando wakho ubuyekezwa ngokuzenzakalelayo ngemva komncintiswano ngamunye. Ubonakala ephrofayili yakho yomphakathi uma uvuma.',
            },
        },
    },

    # =========================================================================
    # Isigaba 8: Ukuphathwa Kwamazinga (5 izifundo)
    # =========================================================================
    8: {
        'title_zu': 'Ukuphathwa Kwamazinga',
        'tutorials': {
            1: {
                'title_zu': 'Misa uhlelo lwamazinga',
                'steps_zu': [
                    'Finyelela ukumiswa : Kusuka kuZilungiselo > Amazinga, khetha umudlalo womzimba bese uchaza uhlelo lwakho lwamazinga.',
                    'Dala amazinga : Engeza amazinga ngokulandelana: Ibhande elimhlophe, Eliphuzi, Eliyolinji, Eliluhlaza, Eliluhlaza okwesibhakabhaka, Elinsundu, Elimnyama uDan 1, uDan 2, njll.',
                    'Chaza izimfanelo : Ngezinga ngalinye, chaza: isikhathi esincane ezingeni elidlule, iminyaka encane, inombolo encane yamaklas, uma kudingeka ukuhlolwa.',
                    'Abela imibala : Abela imibala yamabhande ukuze ibonakale esixhumi esobuso nasemaphrofayili.',
                ],
                'tip_zu': 'Izinhlelo zamazinga ezijwayelekile (iJudo, iKarate, iTKD, iBJJ) zilungiswe ngaphambili. Ungaziqondanisa noma udale ezintsha.',
            },
            2: {
                'title_zu': 'Abela izinga kumzileli',
                'steps_zu': [
                    'Finyelela ikhadi : Kusuka ekhadi lomzileli, chofoza ethebhini Lamazinga bese uchofoza ku-\'Abela izinga elisha\'.',
                    'Khetha izinga : Khetha izinga ohlwini. Uhlelo luhlola ngokuzenzakalelayo izimfanelo (isikhathi, iminyaka, ukuhlolwa).',
                    'Faka imininingwane : Engeza usuku lokuabela, indawo, ijaji/umhloli nezinkulumo.',
                    'Ukuabela ngobuningi : Kusuka kuMazinga > Ukuabela Ngobuningi, khetha abazileli abaningi bese uabela izinga elifanayo kubo bonke.',
                ],
                'tip_zu': 'I-imeyili yokubingelela ithunyelwa ngokuzenzakalelayo kumzileli nezinga lakhe elisha.',
            },
            3: {
                'title_zu': 'Hlela ukuhlolwa kwamazinga',
                'steps_zu': [
                    'Dala ukuhlolwa : Kusuka kuMazinga > Ukuhlolwa, dala ukuhlolwa okusha: usuku, indawo, umudlalo womzimba, amazinga ahlanganiswe, ijaji.',
                    'Bhalisa abavivinywayo : Engeza abavivinywayo ngesandla noma uvumele ukuzibhalisa. Uhlelo luhlola izimfanelo zomuntu ngamunye.',
                    'Ngosuku lokuhlolwa : Sebenzisa isixhumi esobuso sokuhlolwa ukuze uhlole umvivinywa ngamunye: amasu adingekayo, ukulwa, ithiyori.',
                    'Shicilela imiphumela : Qinisekisa abaphumelele nabangaphumelelanga. Amazinga aabelwa ngokuzenzakalelayo kubavivinywayo abaphumelele.',
                ],
                'tip_zu': 'Ukuhlolwa kwamazinga kungaxhunyaniswa nomncintiswano (isib. ukuphakanyiswa kwezinga ngesikhathi somqhudelwano).',
            },
            4: {
                'title_zu': 'Phatha umlando nokuqhubeka kwamazinga',
                'steps_zu': [
                    'Buka umlando : Ikhadi lomzileli ngamunye libonisa umlando ophelele wamazinga: usuku, indawo, ijaji, izinkulumo.',
                    'Buka ukuqhubeka : Igrafu ibonisa ukuqhubeka ngesikhathi. Qhathanisa nesilinganiso sekilabhu.',
                    'Buyisa izinga : Uma kunephutha, buyisa izinga nesizathu. Umlando ugcina irekhodi lokubuyiswa.',
                ],
                'tip_zu': 'Umlando wamazinga uyahanjiswa uma umzileli eshintsha ikilabhu.',
            },
            5: {
                'title_zu': 'Khiqiza izitifiketi zamazinga',
                'steps_zu': [
                    'Finyelela izitifiketi : Kusuka kuMazinga > Izitifiketi, khetha umzileli nezinga elizodala isitifiketi.',
                    'Khetha isifanekiso : Khetha isifanekiso sesitifiketi: esisemthethweni (esinelogo yenhlangano), esekilabhu noma eqondanisiwe.',
                    'Qondanisa : Engeza ukusayina, isitembu sekilabhu nokushiwo okukhethekile. Ikhodi ye-QR yokuqinisekisa yengezwa ngokuzenzakalelayo.',
                    'Khiqiza usabalalise : Khiqiza i-PDF. Phrinta noma uthumele nge-imeyili. Ikhodi ye-QR ivumela noma ubani ukuqinisekisa ubuqiniso besitifiketi.',
                ],
                'tip_zu': 'Ikhodi ye-QR yokuqinisekisa iqondisa ekhasini lomphakathi le-MartialComp eliqinisekisa ukusebenza kwezinga.',
            },
        },
    },

    # =========================================================================
    # Isigaba 9: Ukuphathwa Kwenhlangano (8 izifundo)
    # =========================================================================
    9: {
        'title_zu': 'Ukuphathwa Kwenhlangano',
        'tutorials': {
            1: {
                'title_zu': 'Phatha amaklilobhu ahlanganyele',
                'steps_zu': [
                    'Umbono wophelele : Iphaneli yenhlangano ibonisa ibalazwe lamaklilobhu ahlanganyele, isimo sawo (asebenzayo, alindile, aphelelwe) nezibalo.',
                    'Setshenzwa izicelo : Izicelo ezintsha zokuhlanganyela zibonakala kuMaklilobhu > Alindile. Buyekeza amadokhumenti bese wamukela noma wenqaba.',
                    'Qapha ukuvuselelwa : Buka ukuhlanganyela okusondela ekupheleni. Thumela izikhumbuzo ezizenzakalelayo izinsuku ezingu-30, ezi-15 nezi-7 ngaphambi.',
                ],
                'tip_zu': 'Iphaneli yenhlangano inikeza umbono wesikhathi sangempela wenombolo yonke yabazileli abanelayisensi kuwo wonke amaklilobhu.',
            },
            2: {
                'title_zu': 'Phatha izinkathi zemali yobulungu',
                'steps_zu': [
                    'Dala inkathi : Kusuka kuZinkathi > Entsha, chaza izinsuku zokuqala nezokuphela nezintengo zemali yobulungu ngohlobo (ikilabhu, ngamunye, abasha, abadala).',
                    'Misa imali yobulungu : Chaza izinani ngesigaba: ukuhlanganyela kwekilabhu (okunqunyiwe), ilayisensi ngayinye (ngomzileli), umshwalense (okukhethwa).',
                    'Qapha izinkokhelo : Buka imali yobulungu etholwe, elindile nephelelwe ngesikhathi sangempela. Thumela izikhumbuzo ezizenzakalelayo.',
                    'Vala inkathi : Ekupheleni kwenkathi, yivale ukuze ukhiqize umbiko wezezimali ulungise inkathi elandelayo.',
                ],
                'tip_zu': 'Imali yobulungu ingakhokhwa nge-inthanethi nge-Stripe noma ngokudlulisa ebhange. Ukulandela kwenzeka ngokuzenzakalelayo kuzo zombili izimo.',
            },
            3: {
                'title_zu': 'Qapha imincintiswano',
                'steps_zu': [
                    'Umbono wophelele : Ikhalenda yenhlangano ibonisa yonke imincintiswano yamaklilobhu ahlanganyele, nesimo nenombolo yababamba iqhaza.',
                    'Gunyaza umncintiswano : Amaklilobhu athumela imincintiswano yawo ukuze igunyazwe. Hlola imithetho, abahluleli bese uqinisekisa.',
                    'Buka imiphumela : Finyelela imiphumela yayo yonke imincintiswano egunyaziwe. Izikhundla zesizwe zibuyekezwa ngokuzenzakalelayo.',
                ],
                'tip_zu': 'Imincintiswano egunyazwe yinhlangano iqhakanjiswa endleleni yokusesha nasekhalendeni yomphakathi.',
            },
            4: {
                'title_zu': 'Phatha abahluleli neziqu zabo',
                'steps_zu': [
                    'Idathabheyisi yabahluleli : Buka idathabheyisi yabahluleli abahlanganyele neziqu, okukhethekile kwabo nomlando wemisebenzi.',
                    'Phatha amazinga : Abela amazinga eziqu: esifunda, esizwe, samazwe ngamazwe. Chaza imilinganiselo yokuphakanyiswa.',
                    'Ukulandela kobungathathi-hlangothi : I-MartialComp icubungula izibalo zokuskosha zomahluleli ngamunye bese ithola ukukhetha okungenzeka.',
                ],
                'tip_zu': 'Abahluleli abanomlando wokuskosha okulinganisiwe baqhakanjiswa emincintiswanweni ebalulekile.',
            },
            5: {
                'title_zu': 'Phatha izitifiketi',
                'steps_zu': [
                    'Dala isifanekiso : Yila izifanekiso zakho zesitifiketi nelogo yenhlangano, imibhalo esemthethweni namangeno aguquguqukayo.',
                    'Khipha izitifiketi : Khiqiza izitifiketi za-: amazinga, iziqu zabahluleli, amadiploma okufundisa, iziqinisekiso ezihlukahlukene.',
                    'Ukuqinisekiswa komphakathi : Isitifiketi ngasinye sinekhodi ye-QR eyingqayizivele. Noma ubani angayiskena ukuze aqinisekise ubuqiniso ku-martialcomp.com.',
                ],
                'tip_zu': 'Izitifiketi zedijithali azikwazi ukuguqulwa ngenxa yekhodi ye-QR yokuqinisekisa exhunyaniswe ne-MartialComp.',
            },
            6: {
                'title_zu': 'Qondanisa isayithi somphakathi senhlangano',
                'steps_zu': [
                    'Finyelela kumakhi wesayithi : Kusuka kuZilungiselo > Isayithi Somphakathi, vula umhleli wekhasi. Inhlangano yakho ine-URL: inhlangano.martialcomp.com.',
                    'Qondanisa ukubukeka : Khetha imibala, indikimba, ibhena nelogo. Engeza incazelo nezixhumanisi zamanethiwekhi akho okuxhumana.',
                    'Engeza okuqukethwe : Shicilela izindaba, amagalari ezithombe, amavidiyo, ikhalenda yemincintiswano namadokhumenti alandwayo.',
                    'Phatha amakhasi : Dala amakhasi engeziwe: Umlando, Izikhulu, Imithetho, Xhumana nathi.',
                ],
                'tip_zu': 'Isayithi somphakathi senzelwe i-SEO. Uma sigcwele kakhulu, sizoba nezikhundla ezingcono ku-Google.',
            },
            7: {
                'title_zu': 'Buka izibalo nemibiko',
                'steps_zu': [
                    'Iphaneli yokuhlaziywa : Iphaneli ibonisa ama-KPI: inombolo yamaklilobhu, abazileli, imincintiswano, amalayisensi asebenzayo, ukukhula.',
                    'Imibiko ngekilabhu : Khiqiza imibiko enemininingwane ngekilabhu: inombolo yamalungu, imali yobulungu, ukubamba iqhaza emincintiswanweni, amazinga abelwe.',
                    'Imibiko ngomudlalo womzimba : Cwaningisisa ukusatshalaliswa ngomudlalo womzimba, iminyaka, ubulili. Bona izikhathi zokukhula.',
                    'Thumela wabelane : Thumela imibiko nge-PDF, Excel noma CSV yemihlangano yakho yonke nemibiko esemthethweni.',
                ],
                'tip_zu': 'Imibiko ibuyekezwa ngesikhathi sangempela. Hlela ukuthunyelwa okuzenzakalelayo kwenyanga noma kwekota.',
            },
            8: {
                'title_zu': 'Phatha izinhlelo zokuqeqesha',
                'steps_zu': [
                    'Dala uhlelo : Kusuka kuKuqeqesha > Olusha, chaza uhlelo: isihloko, umudlalo womzimba, izinga, ubude, izimfanelo.',
                    'Hlela izeseshini : Engeza izeseshini zokuqeqesha: izinsuku, izindawo, abaqeqeshi, inombolo yezindawo.',
                    'Phatha ukubhaliswa : Abaqeqeshi nabahluleli bayabhalisa nge-inthanethi. Qinisekisa ukubhaliswa bese uthumela izimemo.',
                    'Ukulandela nesitifiketi : Qapha ukuza ezeseshini. Khipha izitifiketi kubahlanganyeli abaqede uhlelo.',
                ],
                'tip_zu': 'Izinhlelo zokuqeqesha eziqediwe zibonakala ngokuzenzakalelayo emaphrofayili abaqeqeshi nabahluleli.',
            },
        },
    },

    # =========================================================================
    # Isigaba 10: Ezezimali (5 izifundo)
    # =========================================================================
    10: {
        'title_zu': 'Ezezimali',
        'tutorials': {
            1: {
                'title_zu': 'Qapha ukuthengiselana kwekilabhu',
                'steps_zu': [
                    'Umbono wophelele : Iphaneli yezezimali ibonisa: ibhalansi, imali engenayo yenyanga, izindleko negrafu yamikhuba.',
                    'Bhalisela ukuthengiselana : Engeza imali engenayo noma izindleko: inani, usuku, isigaba (imali yobulungu, izinto zokusebenza, ukuqasha), incazelo.',
                    'Ukufakwa ezigabeni ngokuzenzakalelayo : I-MartialComp ifaka ngokuzenzakalelayo ukuthengiselana okuphindaphindiwe ezigabeni. Qondanisa izigaba ngokwezidingo zakho.',
                ],
                'tip_zu': 'Xhuma i-akhawunti yakho yasebhange ukuze ungenise ngokuzenzakalelayo ukuthengiselana wenze lula ukuqondanisa.',
            },
            2: {
                'title_zu': 'Dala uthumele ama-invoyisi',
                'steps_zu': [
                    'Dala i-invoyisi : Kusuka kuZezimali > Ama-invoyisi > Entsha, khetha umthengi (umzileli, ikilabhu, umxhasi) nemigqa yokukhokha.',
                    'Qondanisa : Engeza ilogo yakho, imibhalo esemthethweni, imibandela yokukhokha. Khetha imali kanye nentengo ye-VAT.',
                    'Thumela : Thumela i-invoyisi nge-imeyili. Umthengi uthola isixhumanisi sokukhokha kwe-inthanethi (Stripe) ne-invoyisi nge-PDF.',
                    'Qapha izinkokhelo : Buka ama-invoyisi akhokhelwe, alindile naphelelwe. Thumela izikhumbuzo ezizenzakalelayo.',
                ],
                'tip_zu': 'Imali yobulungu yabazileli ikhiqiza ngokuzenzakalelayo ama-invoyisi uma uvula le nketho.',
            },
            3: {
                'title_zu': 'Phatha izinkokhelo ze-inthanethi (Stripe)',
                'steps_zu': [
                    'Xhuma i-Stripe : Kusuka kuZilungiselo > Izinkokhelo, chofoza ku-\'Xhuma i-Stripe\'. Landela izinyathelo ukuze uxhume i-akhawunti yakho ye-Stripe.',
                    'Misa i-checkout : Beka izintengo za-: imali yobulungu, ukubhaliswa emincintiswanweni, isitolo. Vula izinkokhelo eziphindaphindiwe uma kudingeka.',
                    'Hlola ukukhokha : Sebenzisa imodi yokuhlola ye-Stripe ukuze uhlole ukuthi konke kuyasebenza ngaphambi kokuvula izinkokhelo zangempela.',
                    'Qapha imali engenayo : Iphaneli ye-Stripe ku-MartialComp ibonisa izinkokhelo ezitholwe, izimbuyiselo nokudluliswa e-akhawuntini yakho yasebhange.',
                ],
                'tip_zu': 'I-Stripe ikhokhisa ikhomishini ka-1,4% + 0,25 EUR ngokuthengiselana ngakunye e-Europe. Izimali zidluliselwa ezinsukwini ezi-2-7.',
            },
            4: {
                'title_zu': 'Ngenisa izitatimende zasebhange',
                'steps_zu': [
                    'Landa isitatimende : Kusuka ebhange lakho, thumela isitatimende ngefomethi ye-CSV, OFX noma QIF.',
                    'Ngenisa ku-MartialComp : Kusuka kuZezimali > Ngenisa, layisha ifayela. I-MartialComp ithola ifomethi bese ihlanganisa izinhla.',
                    'Qondanisa : Uhlelo luqondanisa ngokuzenzakalelayo ukuthengiselana okungenisiwe nama-invoyisi nemali yobulungu ekhona.',
                    'Qinisekisa : Hlola ukuqondaniswa, lungisa amaphutha bese uqinisekisa. Ukuthengiselana okungaqondanisiwe kwengezwa njengokulindile.',
                ],
                'tip_zu': 'Ukungeniswa kwasebhange kwenyanga kugcina izinhlelo zakho zokubalwa kwemali zisemsheni ngaphandle kokufaka ngesandla.',
            },
            5: {
                'title_zu': 'Phatha imali yobulungu yabazileli',
                'steps_zu': [
                    'Misa izintengo : Kusuka kuZezimali > Imali Yobulungu, beka izintengo zonyaka ngesigaba: ingane, osakhulayo, omdala, umndeni.',
                    'Khipha izicelo zokukhokha : Ekuqaleni kwenkathi, khiqiza izicelo zokukhokha zabo bonke amalungu. Ngamunye uthola i-imeyili enesixhumanisi sokukhokha.',
                    'Qapha izinkokhelo : Buka imali yobulungu ekhokhelwe, elindile nephelelwe. Isimo sibonakala ekhadi lomzileli ngamunye.',
                    'Thumela izikhumbuzo : Hlela izikhumbuzo ezizenzakalelayo: isonto eli-1, amasonto ama-2, inyanga e-1 ngemva kosuku lokuphelelwa.',
                ],
                'tip_zu': 'Abazileli abanemali yobulungu ephelelwe bangavinjelwa ekubhalisweni emincintiswanweni.',
            },
        },
    },

    # =========================================================================
    # Isigaba 11: Imicimbi Nekhalenda (3 izifundo)
    # =========================================================================
    11: {
        'title_zu': 'Imicimbi Nekhalenda',
        'tutorials': {
            1: {
                'title_zu': 'Dala umcimbi (isemina, igala, umhlangano)',
                'steps_zu': [
                    'Dala umcimbi : Kusuka kuKhalenda > Umcimbi Omusha, faka: uhlobo (isemina, igala, umhlangano, iminyango evulekile), isihloko, izinsuku, indawo nencazelo.',
                    'Misa ukubhaliswa : Vula ukubhaliswa kwe-inthanethi. Beka inombolo yezindawo, intengo (yamahhala noma ekhokhelwayo) nosuku lokugcina lokubhaliswa.',
                    'Shicilela : Shicilela umcimbi. Ubonakala ekhalendeni yekilabhu futhi ungabelwana ngawo kumanethiwekhi okuxhumana.',
                ],
                'tip_zu': 'Izemina nabafundisi abamenyiwe ziyizinsiza ezinhle zokukhangisa. Engeza isithombe sabo nebhayografi ukuze uheha abantu abaningi.',
            },
            2: {
                'title_zu': 'Phatha imicimbi ephindaphindiwe',
                'steps_zu': [
                    'Dala ukuphindaphinda : Ngesikhathi sokudalwa, maka \'Umcimbi Ophindaphindiwe\'. Beka ukuvama: nsuku zonke, maviki onke, nyanga zonke.',
                    'Phatha izingqinamba : Khansela noma ushintshe okwenzeka okukodwa ngaphandle kokuthinta okunye (isib. iklasi elikhanselelwe ngeholidi).',
                    'Shintsha uchungechunge : Shintsha uchungechunge lonke (isib. ukushintsha kwesikhathi okuhlala njalo) noma okwenzeka okukodwa.',
                ],
                'tip_zu': 'Amaklasi eviki kufanele adalwe njengimicimbi ephindaphindiwe ukuze avele ngokuzenzakalelayo ekhalendeni.',
            },
            3: {
                'title_zu': 'Qapha ukubhaliswa nokuza',
                'steps_zu': [
                    'Buka ababhalisiwe : Kusuka emcimbini, buka uhlu lwababhalisiwe nesimo sabo: ubhaliswe, uqinisekisiwe, ukhanselelwe.',
                    'Bhalisela ukuza : Ngosuku lomcimbi, bhalisela ukuza ngohlwini noma ikhodi ye-QR.',
                    'Thumela : Thumela uhlu lwababamba iqhaza nge-CSV noma i-PDF yamafayela akho.',
                ],
                'tip_zu': 'Iphesenti lokubamba iqhaza emicimbini liyisikhombisi esibalulekile sokuzibophezela kwamalungu akho.',
            },
        },
    },

    # =========================================================================
    # Isigaba 12: Ukuphathwa Komndeni (3 izifundo)
    # =========================================================================
    12: {
        'title_zu': 'Ukuphathwa Komndeni',
        'tutorials': {
            1: {
                'title_zu': 'Dala iqembu lomndeni',
                'steps_zu': [
                    'Finyelela amaqembu omndeni : Kusuka ephrofayili yakho, iya kuZilungiselo > Iqembu Lomndeni > Dala.',
                    'Engeza amalungu : Engeza ilungu ngalinye lomndeni: umlingani, izingane. Xhuma ama-akhawunti abo e-MartialComp akhona noma udale amasha.',
                    'Beka ophethe : Ophethe weqembu lomndeni uthola zonke izaziso aphatha izinkokhelo zomndeni wonke.',
                ],
                'tip_zu': 'Amanye amaklilobhu anikeza izintengo zomndeni (isaphulelo kusukela kwelungu le-3). Iqembu lomndeni livula ngokuzenzakalelayo lezi zaphulelo.',
            },
            2: {
                'title_zu': 'Bhalisa umndeni wonke emncintiswanweni',
                'steps_zu': [
                    'Ukubhaliswa kweqembu : Kusuka emncintiswanweni, chofoza ku-\'Bhalisa umndeni wami\'. Amalungu afanelekile eqembu lakho lomndeni aboniswa.',
                    'Khetha uqinisekise : Khetha amalungu okufanele abhaliswe. Izigaba ziphakanyiswa ngokuzenzakalelayo ngamunye ngamunye.',
                    'Ukukhokha okukodwa : Khokha konke ukubhaliswa ngokuthengiselana okukodwa.',
                ],
                'tip_zu': 'Ukubhaliswa kweqembu kongiwa isikhathi esibalulekile lapho izingane eziningi zibamba iqhaza emncintiswanweni ofanayo.',
            },
            3: {
                'title_zu': 'Isikhungo sezinkokhelo somndeni',
                'steps_zu': [
                    'Umbono wophelele : Isikhungo somndeni sibonisa yonke imali yobulungu, ukubhaliswa nama-invoyisi omndeni esikrinini esisodwa.',
                    'Ukukhokha okuhlanganisiwe : Hlanganisa izinkokhelo eziningi ezilindile bese ukhokha ngokuthengiselana okukodwa.',
                    'Umlando : Buka umlando ophelele wezinkokhelo zomndeni namarisidi alandwayo.',
                ],
                'tip_zu': 'Vula ukukhokha okuzenzakalelayo ngqo ukuze ungakhohlwa neze imali yobulungu.',
            },
        },
    },

    # =========================================================================
    # Isigaba 13: Ukuphathwa Kwemisebenzi (Kanban) (2 izifundo)
    # =========================================================================
    13: {
        'title_zu': 'Ukuphathwa Kwemisebenzi (Kanban)',
        'tutorials': {
            1: {
                'title_zu': 'Sebenzisa ibhodi yeKanban',
                'steps_zu': [
                    'Dala ibhodi : Kusuka kuMathuluzi > Kanban, dala ibhodi entsha: igama, incazelo namalungu amenyiwe.',
                    'Engeza izinhla : Dala izinhla zomsebenzi wakho: Okufanele Kwenziwe, Kuyaqhubeka, Kuyalindwa, Kwenziwe. Qondanisa amagama nemibala.',
                    'Dala imisebenzi : Engeza imisebenzi ne-: isihloko, incazelo, usuku lokugcina, ophethe, isigcino sokubaluleka (phezulu/phakathi/phansi) nama-lebuli.',
                    'Phatha ngokuhudula nokwehlisa : Hambisa imisebenzi phakathi kwezinhla ngokuyihudula. Umlando wokuhamba uyagcinwa.',
                ],
                'tip_zu': 'Dala ibhodi eqondiwe yomncintiswano ngamunye ozowuhlela. Imisebenzi ejwayelekile (ukubhukha indawo, uku-oda amamedali, njll.) ingangeniselwa kusuka esifanekisweni.',
            },
            2: {
                'title_zu': 'Phatha imisebenzi yokuhlela',
                'steps_zu': [
                    'Isifanekiso somncintiswano : Sebenzisa isifanekiso \'Ukuhlela Umncintiswano\' esinomsebenzi ojwayelekile: amalojistikhi, ukukhulumisana, abahluleli, amamedali, njll.',
                    'Abela amalungu : Abela umsebenzi ngamunye elungwini leqembu lokuhlela. Beka izinkathi.',
                    'Qapha ukuqhubeka : Iphesenti lokuqhubeka elijimele liboniswa ngaphezulu kwebhodi. Imisebenzi ephelelwe iqhakanjiswa ngokubomvu.',
                ],
                'tip_zu': 'Ibhodi yeKanban ifinyeleleka kusuka kuhlelo lokusebenza lweselula ukuze ubuyekeze imisebenzi uhamba.',
            },
        },
    },

    # =========================================================================
    # Isigaba 14: Isitolo Se-inthanethi (2 izifundo)
    # =========================================================================
    14: {
        'title_zu': 'Isitolo Se-inthanethi',
        'tutorials': {
            1: {
                'title_zu': 'Misa isitolo sekilabhu',
                'steps_zu': [
                    'Vula isitolo : Kusuka kuZilungiselo > Isitolo, vula isici sokuthengisa nge-inthanethi. Xhuma i-akhawunti yakho ye-Stripe uma ungakakwenzi.',
                    'Engeza imikhiqizo : Dala imikhiqizo yakho: igama, incazelo, izithombe, intengo, usayizi/izinhlobo ezitholakalayo, isitoko.',
                    'Hlela ngezigaba : Hlukanisa imikhiqizo yakho: Izinyufomu (kimono, dobok, amagilavu), Izinto Zokusebenza (izivikelo, amasikhwama), Ama-aksesori (amabhande, amapheshi), Ukukhangisa.',
                    'Shicilela isitolo : Isitolo sakho sifinyeleleka kusuka ekhasini lomphakathi lekilabhu yakho. Yabelana ngesixhumanisi noma ikhodi ye-QR.',
                ],
                'tip_zu': 'Nikeza amaphakheji (kimono + ibhande + isikhwama) ngesaphulelo ukuze wandise ithikithi eliphakathi.',
            },
            2: {
                'title_zu': 'Yenza i-oda',
                'steps_zu': [
                    'Zulazula esitolo : Kusuka ekhasini lekilabhu yakho, finyelela isitolo. Zulazula imikhiqizo ngesigaba.',
                    'Engeza ebhasikidini : Khetha usayizi/uhlobo bese wengeza ebhasikidini. Ibhasikidi igcinwa phakathi kwezeseshini.',
                    'Oda ukhokhe : Qinisekisa ibhasikidi yakho, khetha indlela yokuhanjiswa (ukuqoqa edojo noma ukuthunyelwa ngeposi) bese ukhokha nge-inthanethi.',
                    'Qapha i-oda : Thola izaziso isinyathelo ngasinye: i-oda liqunisekisiwe, liyalungiswa, lilungele ukuqoqwa / lithunyelwe.',
                ],
                'tip_zu': 'Imodi \'Yokuqoqa Edojo\' igwema izindleko zokuhanjiswa. Umqeqeshi uzokunikeza i-oda yakho eklasini elilandelayo.',
            },
        },
    },

    # =========================================================================
    # Isigaba 15: Izici Ezithuthukile (5 izifundo)
    # =========================================================================
    15: {
        'title_zu': 'Izici Ezithuthukile',
        'tutorials': {
            1: {
                'title_zu': 'Misa ukusakaza imincintiswano',
                'steps_zu': [
                    'Lungisa ukusakaza : Dala umcimbi obukhoma ku-YouTube, Twitch noma Facebook. Kopisha i-URL yokusakaza nokhiye wokusakaza.',
                    'Misa ku-MartialComp : Kusuka emncintiswanweni, iya kuZilungiselo > Ukusakaza. Namathisela i-URL bese uvula ukubonisa ekhasini lomphakathi.',
                    'I-overlay yamaskosha : Vula i-overlay ye-MartialComp ebonisa amaskosha bukhoma ekusakazeni kwevidiyo. Qondanisa isikhundla nesitayela.',
                    'Qala uhlole : Qala ukusakaza bese uhlola ukuthi i-overlay iyasebenza. Ababukeli bazobona amaskosha bukhoma ekusakazeni.',
                ],
                'tip_zu': 'Ukusakaza ne-overlay yamaskosha ye-MartialComp kunikeza ukubukeka okungcono ngisho nemincintiswano emincane.',
            },
            2: {
                'title_zu': 'Sebenzisa uhlelo lokusebenza lweselula',
                'steps_zu': [
                    'Landa uhlelo lokusebenza : Sesha \'MartialComp\' ku-Play Store (Android) noma ku-App Store (iOS). Faka uvule.',
                    'Ngena : Ngena nge-akhawunti yakho ye-MartialComp ekhona. Ungakwazi futhi ukusebenzisa ukungena nge-Google, Facebook noma Apple.',
                    'Thola isixhumi esobuso seselula : Uhlelo lokusebenza lunikeza: iphrofayili, imiphumela, ikhalenda, izaziso ze-push, ikhodi ye-QR yomuntu siqu nokubhaliswa emincintiswanweni.',
                    'Imodi engaxhunyiwe : Idatha ebalulekile (iphrofayili, izinga, ilayisensi) itholakala ngaphandle kwexhumaniso. Ukuvumelanisa okuzenzakalelayo lapho uxhuma futhi.',
                ],
                'tip_zu': 'Vula izaziso ze-push ukuze uthole izexwayiso zemiphumela bukhoma ngesikhathi semincintiswano.',
            },
            3: {
                'title_zu': 'Shintsha indima kuhlelo lokusebenza',
                'steps_zu': [
                    'Finyelela isikhethi sendima : Thinta i-avatar yakho phezulu kwesikrini noma swayipha kusuka kwesokunxele ukuze uvule imenyu esohlangothini.',
                    'Khetha indima : Uhlu lwakho lwezindima lubonakala: Umqeqeshi, Umzileli, Umahluleli, Umphathi Wekilabhu. Thinta indima oyithandayo.',
                    'Isixhumi esobuso esiqondanisiwe : Iphaneli yokulawula nenmenyu kubuyekezwa ngokushesha ukuze kubonise indima ekhethiwe.',
                ],
                'tip_zu': 'Ungaba umqeqeshi ekilabhini eyodwa nomzileli kwenye. Indima ngayinye ixhunyaniswe nenhlangano yayo.',
            },
            4: {
                'title_zu': 'Ukungeniswa/Ukuthunyelwa kwedatha okuthuthukile',
                'steps_zu': [
                    'Amafomethi asekwayo : I-MartialComp isekela ukungeniswa nokuthunyelwa nge-CSV, Excel (XLSX), JSON ne-PDF. Isigaba ngasinye sinezinketho zaso.',
                    'Ukungeniswa nokuhlanganiswa : Isixhumi esobuso sokuhlanganisa sivumela ukuxhumanisa noma yisiphi isakhiwo sefayela namangeno e-MartialComp.',
                    'Ukuthunyelwa okuqondanisiwe : Khetha amangeno okufanele athunyelwe, izihluzi nefomethi. Hlela ukuthunyelwa okuzenzakalelayo okuphindaphindiwe.',
                    'Imisebenzi ngobuningi : Imisebenzi ngobuningi ivumela ukushintshwa ngobuningi kwe-: izinga, iqembu, isimo sokubhaliswa, njll.',
                ],
                'tip_zu': 'Ukuthunyelwa kwe-JSON kulungele ukuhlanganiswa nezinhlelo zangaphandle (iwebhusayithi, uhlelo lokusebenza lwangaphandle, i-CRM).',
            },
            5: {
                'title_zu': 'Phatha abahluleli besikhashana (amavolontiya)',
                'steps_zu': [
                    'Dala umahluleli wesikhashana : Ngosuku lomncintiswano, kusuka kuBahluleli > Engeza Ivolontiya, dala iphrofayili yesikhashana: igama, ikilabhu nokukhethekile.',
                    'Abela iPIN : iPIN eyingqayizivele ikhiqizwa ngokuzenzakalelayo. Ivolontiya lisebenzisa le PIN ukuze lifinyelele isixhumi esobuso sokuskosha.',
                    'Abela ezigabeni : Abela umahluleli weVolontiya ezigabeni njengomahluleli ovamile. Angaqala ukuhlulela ngokushesha.',
                    'Ngemva komncintiswano : Iphrofayili yesikhashana iyagcinwa ngemva komncintiswano. Amaskosha agcinwa emlandweni.',
                ],
                'tip_zu': 'Abahluleli besikhashana babalulekile emincintiswanweni emincane lapho inombolo yabahluleli abagunyaziwe ilinganiselwe.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to Zulu (hardcoded translations)'

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

            section.title_zu = sec_data['title_zu']
            if not dry_run:
                section.save(update_fields=['title_zu'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_zu"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_zu = tut_data['title_zu']
                tutorial.steps_zu = json.dumps(tut_data['steps_zu'], ensure_ascii=False)
                tutorial.tip_zu = tut_data.get('tip_zu', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_zu', 'steps_zu', 'tip_zu'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_zu"]}')

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
