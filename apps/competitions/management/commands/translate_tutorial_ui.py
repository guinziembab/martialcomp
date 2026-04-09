"""
Management command to add tutorial UI string translations to all .po files.
Usage: python manage.py translate_tutorial_ui
"""
import os
import re

from django.core.management.base import BaseCommand
from django.conf import settings


# All tutorial UI strings with translations for each language
# Format: {msgid: {lang_code: msgstr}}
UI_STRINGS = {
    "Centre de Tutoriels": {
        "en": "Tutorial Center",
        "es": "Centro de Tutoriales",
        "it": "Centro Tutorial",
        "de": "Tutorial-Center",
        "pt": "Centro de Tutoriais",
        "ru": "Центр обучения",
        "ja": "チュートリアルセンター",
        "zh-hans": "教程中心",
        "ko": "튜토리얼 센터",
        "hi": "ट्यूटोरियल केंद्र",
        "ar": "مركز الدروس التعليمية",
        "vi": "Trung tâm Hướng dẫn",
        "no": "Opplæringssenter",
        "sw": "Kituo cha Mafunzo",
        "am": "የትምህርት ማዕከል",
        "zu": "Isikhungo Sezifundo",
        "yo": "Ile-iṣẹ Ikẹkọ",
    },
    "Guides pas a pas pour maitriser MartialComp": {
        "en": "Step-by-step guides to master MartialComp",
        "es": "Guias paso a paso para dominar MartialComp",
        "it": "Guide passo passo per padroneggiare MartialComp",
        "de": "Schritt-für-Schritt-Anleitungen für MartialComp",
        "pt": "Guias passo a passo para dominar o MartialComp",
        "ru": "Пошаговые руководства по MartialComp",
        "ja": "MartialCompをマスターするためのステップバイステップガイド",
        "zh-hans": "掌握MartialComp的分步指南",
        "ko": "MartialComp 마스터를 위한 단계별 가이드",
        "hi": "MartialComp में महारत हासिल करने के लिए चरण-दर-चरण मार्गदर्शिकाएं",
        "ar": "أدلة خطوة بخطوة لإتقان MartialComp",
        "vi": "Hướng dẫn từng bước để thành thạo MartialComp",
        "no": "Trinn-for-trinn-guider for å mestre MartialComp",
        "sw": "Miongozo ya hatua kwa hatua ya kutumia MartialComp",
        "am": "MartialCompን ለመቆጣጠር ደረጃ በደረጃ መመሪያዎች",
        "zu": "Iziqondiso zesinyathelo ngesinyathelo zokuphatha i-MartialComp",
        "yo": "Awọn itọnisọna igbesẹ-nipasẹ-igbesẹ lati ni MartialComp",
    },
    "Tutoriels": {
        "en": "Tutorials",
        "es": "Tutoriales",
        "it": "Tutorial",
        "de": "Tutorials",
        "pt": "Tutoriais",
        "ru": "Уроки",
        "ja": "チュートリアル",
        "zh-hans": "教程",
        "ko": "튜토리얼",
        "hi": "ट्यूटोरियल",
        "ar": "الدروس التعليمية",
        "vi": "Hướng dẫn",
        "no": "Veiledninger",
        "sw": "Mafunzo",
        "am": "ትምህርቶች",
        "zu": "Izifundo",
        "yo": "Awọn ẹkọ",
    },
    "Sections": {
        "en": "Sections",
        "es": "Secciones",
        "it": "Sezioni",
        "de": "Abschnitte",
        "pt": "Secções",
        "ru": "Разделы",
        "ja": "セクション",
        "zh-hans": "章节",
        "ko": "섹션",
        "hi": "अनुभाग",
        "ar": "الأقسام",
        "vi": "Phần",
        "no": "Seksjoner",
        "sw": "Sehemu",
        "am": "ክፍሎች",
        "zu": "Izigaba",
        "yo": "Awọn apakan",
    },
    "Videos": {
        "en": "Videos",
        "es": "Videos",
        "it": "Video",
        "de": "Videos",
        "pt": "Vídeos",
        "ru": "Видео",
        "ja": "動画",
        "zh-hans": "视频",
        "ko": "동영상",
        "hi": "वीडियो",
        "ar": "فيديوهات",
        "vi": "Video",
        "no": "Videoer",
        "sw": "Video",
        "am": "ቪዲዮዎች",
        "zu": "Amavidiyo",
        "yo": "Awọn fidio",
    },
    "Rechercher un tutoriel...": {
        "en": "Search for a tutorial...",
        "es": "Buscar un tutorial...",
        "it": "Cerca un tutorial...",
        "de": "Tutorial suchen...",
        "pt": "Procurar um tutorial...",
        "ru": "Поиск урока...",
        "ja": "チュートリアルを検索...",
        "zh-hans": "搜索教程...",
        "ko": "튜토리얼 검색...",
        "hi": "ट्यूटोरियल खोजें...",
        "ar": "ابحث عن درس تعليمي...",
        "vi": "Tìm kiếm hướng dẫn...",
        "no": "Søk etter veiledning...",
        "sw": "Tafuta mafunzo...",
        "am": "ትምህርት ፈልግ...",
        "zu": "Sesha isifundo...",
        "yo": "Ṣawari ẹkọ kan...",
    },
    "Tous": {
        "en": "All",
        "es": "Todos",
        "it": "Tutti",
        "de": "Alle",
        "pt": "Todos",
        "ru": "Все",
        "ja": "すべて",
        "zh-hans": "全部",
        "ko": "전체",
        "hi": "सभी",
        "ar": "الكل",
        "vi": "Tất cả",
        "no": "Alle",
        "sw": "Yote",
        "am": "ሁሉም",
        "zu": "Konke",
        "yo": "Gbogbo",
    },
    "tutoriels": {
        "en": "tutorials",
        "es": "tutoriales",
        "it": "tutorial",
        "de": "Tutorials",
        "pt": "tutoriais",
        "ru": "уроков",
        "ja": "チュートリアル",
        "zh-hans": "教程",
        "ko": "튜토리얼",
        "hi": "ट्यूटोरियल",
        "ar": "دروس",
        "vi": "hướng dẫn",
        "no": "veiledninger",
        "sw": "mafunzo",
        "am": "ትምህርቶች",
        "zu": "izifundo",
        "yo": "ẹkọ",
    },
    "Video": {
        "en": "Video",
        "es": "Video",
        "it": "Video",
        "de": "Video",
        "pt": "Vídeo",
        "ru": "Видео",
        "ja": "動画",
        "zh-hans": "视频",
        "ko": "동영상",
        "hi": "वीडियो",
        "ar": "فيديو",
        "vi": "Video",
        "no": "Video",
        "sw": "Video",
        "am": "ቪዲዮ",
        "zu": "Ividiyo",
        "yo": "Fidio",
    },
    "Aucun tutoriel trouve": {
        "en": "No tutorials found",
        "es": "No se encontraron tutoriales",
        "it": "Nessun tutorial trovato",
        "de": "Keine Tutorials gefunden",
        "pt": "Nenhum tutorial encontrado",
        "ru": "Уроки не найдены",
        "ja": "チュートリアルが見つかりません",
        "zh-hans": "未找到教程",
        "ko": "튜토리얼을 찾을 수 없습니다",
        "hi": "कोई ट्यूटोरियल नहीं मिला",
        "ar": "لم يتم العثور على دروس",
        "vi": "Không tìm thấy hướng dẫn",
        "no": "Ingen veiledninger funnet",
        "sw": "Hakuna mafunzo yaliyopatikana",
        "am": "ምንም ትምህርት አልተገኘም",
        "zu": "Azikho izifundo ezitholakele",
        "yo": "Ko si ẹkọ ti a ri",
    },
    "Essayez de modifier vos filtres de recherche.": {
        "en": "Try changing your search filters.",
        "es": "Intente cambiar sus filtros de busqueda.",
        "it": "Prova a modificare i filtri di ricerca.",
        "de": "Versuchen Sie, Ihre Suchfilter zu ändern.",
        "pt": "Tente alterar os filtros de pesquisa.",
        "ru": "Попробуйте изменить фильтры поиска.",
        "ja": "検索フィルターを変更してみてください。",
        "zh-hans": "请尝试更改搜索过滤条件。",
        "ko": "검색 필터를 변경해 보세요.",
        "hi": "अपने खोज फ़िल्टर बदलने का प्रयास करें।",
        "ar": "حاول تغيير فلاتر البحث.",
        "vi": "Hãy thử thay đổi bộ lọc tìm kiếm.",
        "no": "Prøv å endre søkefiltrene dine.",
        "sw": "Jaribu kubadilisha vichujio vya utafutaji.",
        "am": "የፍለጋ ማጣሪያዎችን ለመቀየር ይሞክሩ።",
        "zu": "Zama ukushintsha amafiltha okucinga kwakho.",
        "yo": "Gbiyanju lati yi awọn asẹ wiwa rẹ pada.",
    },
    "Tout deployer / replier": {
        "en": "Expand / Collapse all",
        "es": "Expandir / Contraer todo",
        "it": "Espandi / Comprimi tutto",
        "de": "Alle aufklappen / zuklappen",
        "pt": "Expandir / Recolher tudo",
        "ru": "Развернуть / Свернуть все",
        "ja": "すべて展開 / 折りたたむ",
        "zh-hans": "全部展开 / 收起",
        "ko": "모두 펼치기 / 접기",
        "hi": "सभी विस्तार / संकुचित करें",
        "ar": "توسيع / طي الكل",
        "vi": "Mở rộng / Thu gọn tất cả",
        "no": "Vis alle / Skjul alle",
        "sw": "Panua / Kunja yote",
        "am": "ሁሉንም አስፋ / ጠቅልል",
        "zu": "Nweba / Goqa konke",
        "yo": "Fọ / Di gbogbo rẹ",
    },
    "Video tutoriel": {
        "en": "Tutorial video",
        "es": "Video tutorial",
        "it": "Video tutorial",
        "de": "Tutorial-Video",
        "pt": "Vídeo tutorial",
        "ru": "Обучающее видео",
        "ja": "チュートリアル動画",
        "zh-hans": "教程视频",
        "ko": "튜토리얼 동영상",
        "hi": "ट्यूटोरियल वीडियो",
        "ar": "فيديو تعليمي",
        "vi": "Video hướng dẫn",
        "no": "Opplæringsvideo",
        "sw": "Video ya mafunzo",
        "am": "የትምህርት ቪዲዮ",
        "zu": "Ividiyo lesifundo",
        "yo": "Fidio ẹkọ",
    },
    "Etapes": {
        "en": "Steps",
        "es": "Pasos",
        "it": "Passaggi",
        "de": "Schritte",
        "pt": "Etapas",
        "ru": "Шаги",
        "ja": "ステップ",
        "zh-hans": "步骤",
        "ko": "단계",
        "hi": "चरण",
        "ar": "الخطوات",
        "vi": "Các bước",
        "no": "Trinn",
        "sw": "Hatua",
        "am": "ደረጃዎች",
        "zu": "Izinyathelo",
        "yo": "Awọn igbesẹ",
    },
    "Astuce": {
        "en": "Tip",
        "es": "Consejo",
        "it": "Suggerimento",
        "de": "Tipp",
        "pt": "Dica",
        "ru": "Совет",
        "ja": "ヒント",
        "zh-hans": "提示",
        "ko": "팁",
        "hi": "सुझाव",
        "ar": "نصيحة",
        "vi": "Mẹo",
        "no": "Tips",
        "sw": "Dokezo",
        "am": "ምክር",
        "zu": "Icebiso",
        "yo": "Imọran",
    },
    "Precedent": {
        "en": "Previous",
        "es": "Anterior",
        "it": "Precedente",
        "de": "Zurück",
        "pt": "Anterior",
        "ru": "Предыдущий",
        "ja": "前へ",
        "zh-hans": "上一个",
        "ko": "이전",
        "hi": "पिछला",
        "ar": "السابق",
        "vi": "Trước",
        "no": "Forrige",
        "sw": "Iliyopita",
        "am": "ቀዳሚ",
        "zu": "Okwedlule",
        "yo": "Ti tẹlẹ",
    },
    "Suivant": {
        "en": "Next",
        "es": "Siguiente",
        "it": "Successivo",
        "de": "Weiter",
        "pt": "Seguinte",
        "ru": "Следующий",
        "ja": "次へ",
        "zh-hans": "下一个",
        "ko": "다음",
        "hi": "अगला",
        "ar": "التالي",
        "vi": "Tiếp theo",
        "no": "Neste",
        "sw": "Ifuatayo",
        "am": "ቀጣይ",
        "zu": "Okulandelayo",
        "yo": "Atẹle",
    },
    "Documentation": {
        "en": "Documentation",
        "es": "Documentación",
        "it": "Documentazione",
        "de": "Dokumentation",
        "pt": "Documentação",
        "ru": "Документация",
        "ja": "ドキュメント",
        "zh-hans": "文档",
        "ko": "문서",
        "hi": "प्रलेखन",
        "ar": "التوثيق",
        "vi": "Tài liệu",
        "no": "Dokumentasjon",
        "sw": "Nyaraka",
        "am": "ሰነድ",
        "zu": "Amadokhumenti",
        "yo": "Iwe akọsilẹ",
    },
}

# Mapping of locale directory names to language codes used in our dict
LOCALE_DIR_MAP = {
    'en': 'en',
    'es': 'es',
    'it': 'it',
    'de': 'de',
    'pt': 'pt',
    'ru': 'ru',
    'ja': 'ja',
    'zh': 'zh-hans',
    'ko': 'ko',
    'hi': 'hi',
    'ar': 'ar',
    'vi': 'vi',
    'no': 'no',
    'sw': 'sw',
    'am': 'am',
    'zu': 'zu',
    'yo': 'yo',
}


class Command(BaseCommand):
    help = 'Add tutorial UI translations to all .po files'

    def handle(self, *args, **options):
        locale_base = os.path.join(settings.BASE_DIR, 'locale')

        for locale_dir, lang_code in LOCALE_DIR_MAP.items():
            po_path = os.path.join(locale_base, locale_dir, 'LC_MESSAGES', 'django.po')
            if not os.path.exists(po_path):
                self.stdout.write(self.style.WARNING(f'Skipping {locale_dir}: {po_path} not found'))
                continue

            with open(po_path, 'r', encoding='utf-8') as f:
                content = f.read()

            added = 0
            for msgid, translations in UI_STRINGS.items():
                msgstr = translations.get(lang_code, '')
                if not msgstr:
                    continue

                # Check if this msgid already exists in the file
                escaped_msgid = msgid.replace('"', '\\"')
                if f'msgid "{escaped_msgid}"' in content:
                    # Update existing empty translation
                    pattern = re.compile(
                        rf'(msgid "{re.escape(escaped_msgid)}"\s*\n)msgstr ""',
                        re.MULTILINE
                    )
                    escaped_msgstr = msgstr.replace('"', '\\"')
                    new_content = pattern.sub(
                        rf'\1msgstr "{escaped_msgstr}"',
                        content
                    )
                    if new_content != content:
                        content = new_content
                        added += 1
                else:
                    # Add new entry at the end
                    escaped_msgstr = msgstr.replace('"', '\\"')
                    entry = f'\nmsgid "{escaped_msgid}"\nmsgstr "{escaped_msgstr}"\n'
                    content += entry
                    added += 1

            with open(po_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.stdout.write(self.style.SUCCESS(
                f'{locale_dir}: {added} translations added/updated'
            ))

        self.stdout.write(self.style.SUCCESS('\nDone! Run compilemessages to compile .mo files.'))
