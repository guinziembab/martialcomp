#!/usr/bin/env python
"""
Script pour ajouter les 19 entrées manquantes aux fichiers PO.
"""

import os

# Les 19 entrées manquantes avec traductions
MISSING_ENTRIES = {
    "am": {  # Amharic
        "Aide et conseils": "እርዳታ እና ምክሮች",
        "Assurez-vous que les dates sont au bon format": "ቀኖች በትክክለኛው ቅርጸት መሆናቸውን ያረጋግጡ",
        "Conseils pour l'import": "ለማስገባት ምክሮች",
        "Exporter les pratiquants": "ተለማማጆችን ወደ ውጭ ላክ",
        "Format attendu:": "የሚጠበቅ ቅርጸት:",
        "Format: Excel (.xlsx)": "ቅርጸት: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "ተቀባይነት ያላቸው ቅርጸቶች: CSV, Excel (.xlsx, .xls) - ከፍተኛ 10MB",
        "Importation en cours...": "ማስገባት በሂደት ላይ...",
        "Importer des pratiquants": "ተለማማጆችን አስገባ",
        "JJ-MM-AAAA (ex: 15-03-2010)": "ቀቀ-ወወ-ዓዓዓዓ (ምሳሌ: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "ቀቀ.ወወ.ዓዓዓዓ (ምሳሌ: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "ቀቀ/ወወ/ዓዓዓዓ (ምሳሌ: 15/03/2010)",
        "Modèle de fichier": "የፋይል አብነት",
        "NOM": "ስም",
        "Résultats de l'importation": "የማስገባት ውጤቶች",
        "Télécharger le modèle Excel": "የExcel አብነት አውርድ",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "ፋይልዎ በትክክለኛው ቅርጸት መሆኑን ለማረጋገጥ ይህን አብነት ያውርዱ።",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "ለመጠባበቂያ ወይም ከመስመር ውጭ ማስተካከያ የተለማማጆችዎን ሙሉ ዝርዝር በExcel ቅርጸት ያውርዱ።",
        "adresse mail": "የኢሜይል አድራሻ",
    },
    "ar": {  # Arabic
        "Aide et conseils": "المساعدة والنصائح",
        "Assurez-vous que les dates sont au bon format": "تأكد من أن التواريخ بالتنسيق الصحيح",
        "Conseils pour l'import": "نصائح للاستيراد",
        "Exporter les pratiquants": "تصدير الممارسين",
        "Format attendu:": "التنسيق المتوقع:",
        "Format: Excel (.xlsx)": "التنسيق: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "التنسيقات المقبولة: CSV, Excel (.xlsx, .xls) - الحد الأقصى 10MB",
        "Importation en cours...": "جاري الاستيراد...",
        "Importer des pratiquants": "استيراد الممارسين",
        "JJ-MM-AAAA (ex: 15-03-2010)": "يي-شش-سسسس (مثال: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "يي.شش.سسسس (مثال: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "يي/شش/سسسس (مثال: 15/03/2010)",
        "Modèle de fichier": "قالب الملف",
        "NOM": "الاسم",
        "Résultats de l'importation": "نتائج الاستيراد",
        "Télécharger le modèle Excel": "تحميل قالب Excel",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "قم بتحميل هذا القالب للتأكد من أن ملفك بالتنسيق الصحيح.",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "قم بتحميل القائمة الكاملة للممارسين بتنسيق Excel للنسخ الاحتياطي أو التعديل دون اتصال.",
        "adresse mail": "عنوان البريد الإلكتروني",
    },
    "hi": {  # Hindi
        "Aide et conseils": "सहायता और सुझाव",
        "Assurez-vous que les dates sont au bon format": "सुनिश्चित करें कि तिथियां सही प्रारूप में हैं",
        "Conseils pour l'import": "आयात के लिए सुझाव",
        "Exporter les pratiquants": "अभ्यासकर्ताओं को निर्यात करें",
        "Format attendu:": "अपेक्षित प्रारूप:",
        "Format: Excel (.xlsx)": "प्रारूप: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "स्वीकृत प्रारूप: CSV, Excel (.xlsx, .xls) - अधिकतम 10MB",
        "Importation en cours...": "आयात प्रगति पर है...",
        "Importer des pratiquants": "अभ्यासकर्ताओं को आयात करें",
        "JJ-MM-AAAA (ex: 15-03-2010)": "दिन-माह-वर्ष (उदा: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "दिन.माह.वर्ष (उदा: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "दिन/माह/वर्ष (उदा: 15/03/2010)",
        "Modèle de fichier": "फ़ाइल टेम्पलेट",
        "NOM": "नाम",
        "Résultats de l'importation": "आयात परिणाम",
        "Télécharger le modèle Excel": "Excel टेम्पलेट डाउनलोड करें",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "अपनी फ़ाइल सही प्रारूप में है यह सुनिश्चित करने के लिए यह टेम्पलेट डाउनलोड करें।",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "बैकअप या ऑफ़लाइन संपादन के लिए अपने अभ्यासकर्ताओं की पूरी सूची Excel प्रारूप में डाउनलोड करें।",
        "adresse mail": "ईमेल पता",
    },
    "ja": {  # Japanese
        "Aide et conseils": "ヘルプとヒント",
        "Assurez-vous que les dates sont au bon format": "日付が正しい形式であることを確認してください",
        "Conseils pour l'import": "インポートのヒント",
        "Exporter les pratiquants": "練習者をエクスポート",
        "Format attendu:": "予想される形式:",
        "Format: Excel (.xlsx)": "形式: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "対応形式: CSV, Excel (.xlsx, .xls) - 最大10MB",
        "Importation en cours...": "インポート中...",
        "Importer des pratiquants": "練習者をインポート",
        "JJ-MM-AAAA (ex: 15-03-2010)": "日-月-年 (例: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "日.月.年 (例: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "日/月/年 (例: 15/03/2010)",
        "Modèle de fichier": "ファイルテンプレート",
        "NOM": "名前",
        "Résultats de l'importation": "インポート結果",
        "Télécharger le modèle Excel": "Excelテンプレートをダウンロード",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "ファイルが正しい形式であることを確認するために、このテンプレートをダウンロードしてください。",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "バックアップまたはオフライン編集用に、練習者の完全なリストをExcel形式でダウンロードしてください。",
        "adresse mail": "メールアドレス",
    },
    "ko": {  # Korean
        "Aide et conseils": "도움말 및 팁",
        "Assurez-vous que les dates sont au bon format": "날짜가 올바른 형식인지 확인하세요",
        "Conseils pour l'import": "가져오기 팁",
        "Exporter les pratiquants": "수련생 내보내기",
        "Format attendu:": "예상 형식:",
        "Format: Excel (.xlsx)": "형식: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "지원 형식: CSV, Excel (.xlsx, .xls) - 최대 10MB",
        "Importation en cours...": "가져오는 중...",
        "Importer des pratiquants": "수련생 가져오기",
        "JJ-MM-AAAA (ex: 15-03-2010)": "일-월-년 (예: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "일.월.년 (예: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "일/월/년 (예: 15/03/2010)",
        "Modèle de fichier": "파일 템플릿",
        "NOM": "이름",
        "Résultats de l'importation": "가져오기 결과",
        "Télécharger le modèle Excel": "Excel 템플릿 다운로드",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "파일이 올바른 형식인지 확인하려면 이 템플릿을 다운로드하세요.",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "백업 또는 오프라인 편집을 위해 수련생 전체 목록을 Excel 형식으로 다운로드하세요.",
        "adresse mail": "이메일 주소",
    },
    "no": {  # Norwegian
        "Aide et conseils": "Hjelp og tips",
        "Assurez-vous que les dates sont au bon format": "Sørg for at datoene er i riktig format",
        "Conseils pour l'import": "Tips for import",
        "Exporter les pratiquants": "Eksporter utøvere",
        "Format attendu:": "Forventet format:",
        "Format: Excel (.xlsx)": "Format: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Aksepterte formater: CSV, Excel (.xlsx, .xls) - Maks 10MB",
        "Importation en cours...": "Importerer...",
        "Importer des pratiquants": "Importer utøvere",
        "JJ-MM-AAAA (ex: 15-03-2010)": "DD-MM-ÅÅÅÅ (f.eks: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "DD.MM.ÅÅÅÅ (f.eks: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "DD/MM/ÅÅÅÅ (f.eks: 15/03/2010)",
        "Modèle de fichier": "Filmal",
        "NOM": "NAVN",
        "Résultats de l'importation": "Importresultater",
        "Télécharger le modèle Excel": "Last ned Excel-mal",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Last ned denne malen for å sikre at filen din er i riktig format.",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Last ned den komplette listen over utøverne dine i Excel-format for sikkerhetskopiering eller frakoblet redigering.",
        "adresse mail": "e-postadresse",
    },
    "ru": {  # Russian
        "Aide et conseils": "Помощь и советы",
        "Assurez-vous que les dates sont au bon format": "Убедитесь, что даты в правильном формате",
        "Conseils pour l'import": "Советы по импорту",
        "Exporter les pratiquants": "Экспортировать практикующих",
        "Format attendu:": "Ожидаемый формат:",
        "Format: Excel (.xlsx)": "Формат: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Допустимые форматы: CSV, Excel (.xlsx, .xls) - Макс. 10MB",
        "Importation en cours...": "Импорт выполняется...",
        "Importer des pratiquants": "Импортировать практикующих",
        "JJ-MM-AAAA (ex: 15-03-2010)": "ДД-ММ-ГГГГ (напр.: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "ДД.ММ.ГГГГ (напр.: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "ДД/ММ/ГГГГ (напр.: 15/03/2010)",
        "Modèle de fichier": "Шаблон файла",
        "NOM": "ФАМИЛИЯ",
        "Résultats de l'importation": "Результаты импорта",
        "Télécharger le modèle Excel": "Скачать шаблон Excel",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Скачайте этот шаблон, чтобы убедиться, что ваш файл в правильном формате.",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Скачайте полный список практикующих в формате Excel для резервного копирования или редактирования офлайн.",
        "adresse mail": "электронная почта",
    },
    "sw": {  # Swahili
        "Aide et conseils": "Msaada na vidokezo",
        "Assurez-vous que les dates sont au bon format": "Hakikisha tarehe ziko katika muundo sahihi",
        "Conseils pour l'import": "Vidokezo vya kuingiza",
        "Exporter les pratiquants": "Hamisha wanafunzi",
        "Format attendu:": "Muundo unaotarajiwa:",
        "Format: Excel (.xlsx)": "Muundo: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Muundo unaokubaliwa: CSV, Excel (.xlsx, .xls) - Upeo 10MB",
        "Importation en cours...": "Kuingiza inaendelea...",
        "Importer des pratiquants": "Ingiza wanafunzi",
        "JJ-MM-AAAA (ex: 15-03-2010)": "SS-MM-MMMM (mf: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "SS.MM.MMMM (mf: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "SS/MM/MMMM (mf: 15/03/2010)",
        "Modèle de fichier": "Kiolezo cha faili",
        "NOM": "JINA",
        "Résultats de l'importation": "Matokeo ya kuingiza",
        "Télécharger le modèle Excel": "Pakua kiolezo cha Excel",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Pakua kiolezo hiki ili kuhakikisha faili yako iko katika muundo sahihi.",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Pakua orodha kamili ya wanafunzi wako katika muundo wa Excel kwa hifadhi rudufu au uhariri nje ya mtandao.",
        "adresse mail": "anwani ya barua pepe",
    },
    "vi": {  # Vietnamese
        "Aide et conseils": "Trợ giúp và mẹo",
        "Assurez-vous que les dates sont au bon format": "Đảm bảo ngày tháng đúng định dạng",
        "Conseils pour l'import": "Mẹo nhập dữ liệu",
        "Exporter les pratiquants": "Xuất danh sách học viên",
        "Format attendu:": "Định dạng dự kiến:",
        "Format: Excel (.xlsx)": "Định dạng: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Định dạng chấp nhận: CSV, Excel (.xlsx, .xls) - Tối đa 10MB",
        "Importation en cours...": "Đang nhập...",
        "Importer des pratiquants": "Nhập danh sách học viên",
        "JJ-MM-AAAA (ex: 15-03-2010)": "NN-TT-NNNN (ví dụ: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "NN.TT.NNNN (ví dụ: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "NN/TT/NNNN (ví dụ: 15/03/2010)",
        "Modèle de fichier": "Mẫu tệp",
        "NOM": "HỌ",
        "Résultats de l'importation": "Kết quả nhập",
        "Télécharger le modèle Excel": "Tải mẫu Excel",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Tải mẫu này để đảm bảo tệp của bạn đúng định dạng.",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Tải danh sách đầy đủ học viên của bạn dưới dạng Excel để sao lưu hoặc chỉnh sửa ngoại tuyến.",
        "adresse mail": "địa chỉ email",
    },
    "yo": {  # Yoruba
        "Aide et conseils": "Iranlowo ati awon imoran",
        "Assurez-vous que les dates sont au bon format": "Rii daju pe awon ojo wa ni ọna ti o tọ",
        "Conseils pour l'import": "Awọn imọran fun gbigbewọle",
        "Exporter les pratiquants": "Gbejade awọn akẹkọọ",
        "Format attendu:": "Ọna ti a retí:",
        "Format: Excel (.xlsx)": "Ọna: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Awọn ọna ti a gba: CSV, Excel (.xlsx, .xls) - Ti o pọ julọ 10MB",
        "Importation en cours...": "Gbigbewọle n lọ lọwọ...",
        "Importer des pratiquants": "Gbewọle awọn akẹkọọ",
        "JJ-MM-AAAA (ex: 15-03-2010)": "ỌỌ-OṢ-ỌỌỌỌ (apẹẹrẹ: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "ỌỌ.OṢ.ỌỌỌỌ (apẹẹrẹ: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "ỌỌ/OṢ/ỌỌỌỌ (apẹẹrẹ: 15/03/2010)",
        "Modèle de fichier": "Awoṣe faili",
        "NOM": "ORUKỌ",
        "Résultats de l'importation": "Awọn abajade gbigbewọle",
        "Télécharger le modèle Excel": "Gba awoṣe Excel silẹ",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Gba awoṣe yii silẹ lati rii daju pe faili rẹ wa ni ọna ti o tọ.",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Gba atokọ pipe ti awọn akẹkọọ rẹ silẹ ni ọna Excel fun itọju aabo tabi ṣiṣatunkọ laisi intanẹẹti.",
        "adresse mail": "adirẹsi imeeli",
    },
    "zh": {  # Chinese
        "Aide et conseils": "帮助和提示",
        "Assurez-vous que les dates sont au bon format": "确保日期格式正确",
        "Conseils pour l'import": "导入提示",
        "Exporter les pratiquants": "导出学员",
        "Format attendu:": "预期格式:",
        "Format: Excel (.xlsx)": "格式: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "接受的格式: CSV, Excel (.xlsx, .xls) - 最大10MB",
        "Importation en cours...": "正在导入...",
        "Importer des pratiquants": "导入学员",
        "JJ-MM-AAAA (ex: 15-03-2010)": "日-月-年 (例: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "日.月.年 (例: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "日/月/年 (例: 15/03/2010)",
        "Modèle de fichier": "文件模板",
        "NOM": "姓",
        "Résultats de l'importation": "导入结果",
        "Télécharger le modèle Excel": "下载Excel模板",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "下载此模板以确保您的文件格式正确。",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "下载学员完整列表的Excel格式，用于备份或离线编辑。",
        "adresse mail": "电子邮件地址",
    },
    "zu": {  # Zulu
        "Aide et conseils": "Usizo namathiphu",
        "Assurez-vous que les dates sont au bon format": "Qiniseka ukuthi izinsuku zisefomethini efanele",
        "Conseils pour l'import": "Amathiphu okungenisa",
        "Exporter les pratiquants": "Thumela abafundi ngaphandle",
        "Format attendu:": "Ifomethi elindelekile:",
        "Format: Excel (.xlsx)": "Ifomethi: Excel (.xlsx)",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Amafomethi amukelwayo: CSV, Excel (.xlsx, .xls) - Okungenani 10MB",
        "Importation en cours...": "Ukungeniswa kuyaqhubeka...",
        "Importer des pratiquants": "Ngenisa abafundi",
        "JJ-MM-AAAA (ex: 15-03-2010)": "UU-NN-UUUU (isibonelo: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "UU.NN.UUUU (isibonelo: 15.03.2010)",
        "JJ/MM/AAAA (ex: 15/03/2010)": "UU/NN/UUUU (isibonelo: 15/03/2010)",
        "Modèle de fichier": "Isifanekiso sefayela",
        "NOM": "ISIBONGO",
        "Résultats de l'importation": "Imiphumela yokungenisa",
        "Télécharger le modèle Excel": "Landa isifanekiso se-Excel",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Landa lesi sifanekiso ukuqinisekisa ukuthi ifayela lakho lisefomethini efanele.",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Landa uhlu oluphelele lwabafundi bakho ngefomethi ye-Excel ukuze ugcine noma uhlele ngaphandle kwe-inthanethi.",
        "adresse mail": "ikheli le-imeyili",
    },
}


def add_translations_to_po(po_file_path, translations, lang_code):
    """Add missing translations to a PO file."""
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    existing_msgids = set()
    for line in content.split('\n'):
        if line.startswith('msgid "') and line != 'msgid ""':
            msgid = line[7:-1]
            existing_msgids.add(msgid)

    new_entries = []
    for msgid, msgstr in translations.items():
        if msgid not in existing_msgids:
            escaped_msgid = msgid.replace('"', '\\"')
            escaped_msgstr = msgstr.replace('"', '\\"')
            entry = f'\nmsgid "{escaped_msgid}"\nmsgstr "{escaped_msgstr}"\n'
            new_entries.append(entry)

    if new_entries:
        with open(po_file_path, 'a', encoding='utf-8') as f:
            f.write(f'\n# Final missing translations for {lang_code}\n')
            for entry in new_entries:
                f.write(entry)
        return len(new_entries)
    return 0


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    total = 0
    for lang_code, translations in MISSING_ENTRIES.items():
        po_path = os.path.join(base_dir, 'locale', lang_code, 'LC_MESSAGES', 'django.po')
        if os.path.exists(po_path):
            count = add_translations_to_po(po_path, translations, lang_code)
            if count > 0:
                print(f"{lang_code}: +{count} translations")
                total += count

    print(f"\nTotal: {total} translations added")


if __name__ == '__main__':
    main()
