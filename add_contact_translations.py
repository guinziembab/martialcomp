#!/usr/bin/env python3
"""
Add missing contact form translations to all .po files.
"""
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(BASE_DIR, 'locale')

# Missing translations per language
# Format: { msgid: { lang: msgstr } }
TRANSLATIONS = {
    # Welcome page contact section
    "Ecoles, federations, clubs — nous sommes a votre ecoute. Remplissez le formulaire ci-dessous et nous vous repondrons sous 48h.": {
        "en": "Schools, federations, clubs — we are here for you. Fill out the form below and we will get back to you within 48 hours.",
        "de": "Schulen, Verbände, Vereine — wir sind für Sie da. Füllen Sie das untenstehende Formular aus und wir antworten Ihnen innerhalb von 48 Stunden.",
        "es": "Escuelas, federaciones, clubes — estamos a su disposición. Complete el formulario a continuación y le responderemos en un plazo de 48 horas.",
        "it": "Scuole, federazioni, club — siamo a vostra disposizione. Compilate il modulo qui sotto e vi risponderemo entro 48 ore.",
        "pt": "Escolas, federações, clubes — estamos à sua disposição. Preencha o formulário abaixo e responderemos em até 48 horas.",
        "ar": "مدارس، اتحادات، أندية — نحن في خدمتكم. املأ النموذج أدناه وسنرد عليك خلال 48 ساعة.",
        "ja": "学校、連盟、クラブの皆様へ — お気軽にお問い合わせください。以下のフォームにご記入いただければ、48時間以内にご返信いたします。",
        "ko": "학교, 연맹, 클럽 — 여러분을 위해 준비되어 있습니다. 아래 양식을 작성해 주시면 48시간 이내에 답변드리겠습니다.",
        "zh": "学校、联盟、俱乐部 — 我们随时为您服务。请填写以下表格，我们将在48小时内回复您。",
        "ru": "Школы, федерации, клубы — мы к вашим услугам. Заполните форму ниже, и мы ответим вам в течение 48 часов.",
        "hi": "स्कूल, फ़ेडरेशन, क्लब — हम आपकी सेवा में हैं। नीचे दिया गया फ़ॉर्म भरें और हम 48 घंटों के भीतर जवाब देंगे।",
        "no": "Skoler, forbund, klubber — vi er her for dere. Fyll ut skjemaet nedenfor, og vi svarer innen 48 timer.",
        "sw": "Shule, mashirikisho, klabu — tuko hapa kwa ajili yenu. Jaza fomu hapa chini na tutawajibu ndani ya saa 48.",
        "vi": "Trường học, liên đoàn, câu lạc bộ — chúng tôi luôn sẵn sàng hỗ trợ bạn. Điền vào biểu mẫu dưới đây và chúng tôi sẽ phản hồi trong vòng 48 giờ.",
        "yo": "Ile-iwe, ajosepo, egbe — a wa nibi fun yin. Kun foomu ti o wa ni isale a o si dahun laarin wakati 48.",
        "am": "ትምህርት ቤቶች፣ ፌዴሬሽኖች፣ ክለቦች — ለእናንተ እዚህ ነን። ከዚህ በታች ያለውን ቅጽ ሙሉ እና በ48 ሰዓታት ውስጥ እንመልስላችኋለን።",
        "zu": "Izikole, izinhlangano, amaklabhu — silapha ngenxa yenu. Gcwalisa ifomu engezansi futhi sizokuphendula ngaphakathi kwamahora angu-48.",
    },
    "Club, ecole, federation...": {
        "en": "Club, school, federation...",
        "de": "Verein, Schule, Verband...",
        "es": "Club, escuela, federación...",
        "it": "Club, scuola, federazione...",
        "pt": "Clube, escola, federação...",
        "ar": "نادي، مدرسة، اتحاد...",
        "ja": "クラブ、学校、連盟...",
        "ko": "클럽, 학교, 연맹...",
        "zh": "俱乐部、学校、联盟...",
        "ru": "Клуб, школа, федерация...",
        "hi": "क्लब, स्कूल, फ़ेडरेशन...",
        "no": "Klubb, skole, forbund...",
        "sw": "Klabu, shule, shirikisho...",
        "vi": "Câu lạc bộ, trường, liên đoàn...",
        "yo": "Egbe, ile-iwe, ajosepo...",
        "am": "ክለብ፣ ትምህርት ቤት፣ ፌዴሬሽን...",
        "zu": "Iklabu, isikole, inhlangano...",
    },
    "Decrivez votre besoin...": {
        "en": "Describe your needs...",
        "de": "Beschreiben Sie Ihr Anliegen...",
        "es": "Describa su necesidad...",
        "it": "Descrivete la vostra esigenza...",
        "pt": "Descreva a sua necessidade...",
        "ar": "صف احتياجاتك...",
        "ja": "ご要望をお書きください...",
        "ko": "필요 사항을 설명해 주세요...",
        "zh": "请描述您的需求...",
        "ru": "Опишите ваши потребности...",
        "hi": "अपनी आवश्यकता का वर्णन करें...",
        "no": "Beskriv ditt behov...",
        "sw": "Eleza mahitaji yako...",
        "vi": "Mô tả nhu cầu của bạn...",
        "yo": "Se apejuwe ohun ti o nilo...",
        "am": "ፍላጎትዎን ይግለጹ...",
        "zu": "Chaza isidingo sakho...",
    },
    "Ou ecrivez-nous directement a": {
        "en": "Or write to us directly at",
        "de": "Oder schreiben Sie uns direkt an",
        "es": "O escríbanos directamente a",
        "it": "Oppure scriveteci direttamente a",
        "pt": "Ou escreva-nos diretamente para",
        "ar": "أو اكتب لنا مباشرة على",
        "ja": "または直接メールでお問い合わせください：",
        "ko": "또는 직접 이메일로 문의하세요:",
        "zh": "或直接发邮件至",
        "ru": "Или напишите нам напрямую на",
        "hi": "या हमें सीधे लिखें:",
        "no": "Eller skriv direkte til oss på",
        "sw": "Au andika kwetu moja kwa moja kwa",
        "vi": "Hoặc liên hệ trực tiếp qua",
        "yo": "Tabi ko si taara si",
        "am": "ወይም በቀጥታ ይጻፉልን:",
        "zu": "Noma usibhalele ngqo ku",
    },
    "Page de contact complete": {
        "en": "Full contact page",
        "de": "Vollständige Kontaktseite",
        "es": "Página de contacto completa",
        "it": "Pagina di contatto completa",
        "pt": "Página de contato completa",
        "ar": "صفحة الاتصال الكاملة",
        "ja": "お問い合わせページ",
        "ko": "전체 연락처 페이지",
        "zh": "完整联系页面",
        "ru": "Полная страница контактов",
        "hi": "पूर्ण संपर्क पृष्ठ",
        "no": "Fullstendig kontaktside",
        "sw": "Ukurasa kamili wa mawasiliano",
        "vi": "Trang liên hệ đầy đủ",
        "yo": "Oju-iwe olubasoro ni kikun",
        "am": "ሙሉ የመገኛ ገጽ",
        "zu": "Ikhasi eligcwele lokuxhumana",
    },
    # Contact model fields
    "Partenariat": {
        "en": "Partnership",
        "de": "Partnerschaft",
        "es": "Asociación",
        "it": "Partenariato",
        "pt": "Parceria",
        "ar": "شراكة",
        "ja": "パートナーシップ",
        "ko": "파트너십",
        "zh": "合作",
        "ru": "Партнёрство",
        "hi": "साझेदारी",
        "no": "Partnerskap",
        "sw": "Ushirikiano",
        "vi": "Đối tác",
        "yo": "Ajosepo",
        "am": "ሽርክና",
        "zu": "Ubambiswano",
    },
    "Club / Ecole": {
        "en": "Club / School",
        "de": "Verein / Schule",
        "es": "Club / Escuela",
        "it": "Club / Scuola",
        "pt": "Clube / Escola",
        "ar": "نادي / مدرسة",
        "ja": "クラブ / 学校",
        "ko": "클럽 / 학교",
        "zh": "俱乐部 / 学校",
        "ru": "Клуб / Школа",
        "hi": "क्लब / स्कूल",
        "no": "Klubb / Skole",
        "sw": "Klabu / Shule",
        "vi": "Câu lạc bộ / Trường",
        "yo": "Egbe / Ile-iwe",
        "am": "ክለብ / ትምህርት ቤት",
        "zu": "Iklabu / Isikole",
    },
    "Nom de votre club, ecole ou federation": {
        "en": "Name of your club, school or federation",
        "de": "Name Ihres Vereins, Ihrer Schule oder Ihres Verbandes",
        "es": "Nombre de su club, escuela o federación",
        "it": "Nome del vostro club, scuola o federazione",
        "pt": "Nome do seu clube, escola ou federação",
        "ar": "اسم ناديك أو مدرستك أو اتحادك",
        "ja": "クラブ、学校、または連盟の名前",
        "ko": "클럽, 학교 또는 연맹 이름",
        "zh": "您的俱乐部、学校或联盟名称",
        "ru": "Название вашего клуба, школы или федерации",
        "hi": "आपके क्लब, स्कूल या फ़ेडरेशन का नाम",
        "no": "Navn på din klubb, skole eller forbund",
        "sw": "Jina la klabu, shule au shirikisho lako",
        "vi": "Tên câu lạc bộ, trường hoặc liên đoàn của bạn",
        "yo": "Oruko egbe, ile-iwe tabi ajosepo re",
        "am": "የክለብዎ፣ ትምህርት ቤትዎ ወይም ፌዴሬሽንዎ ስም",
        "zu": "Igama leklabu, isikole noma inhlangano yakho",
    },
    "Date de creation": {
        "en": "Date created",
        "de": "Erstellungsdatum",
        "es": "Fecha de creación",
        "it": "Data di creazione",
        "pt": "Data de criação",
        "ar": "تاريخ الإنشاء",
        "ja": "作成日",
        "ko": "생성일",
        "zh": "创建日期",
        "ru": "Дата создания",
        "hi": "निर्माण तिथि",
        "no": "Opprettelsesdato",
        "sw": "Tarehe ya kuundwa",
        "vi": "Ngày tạo",
        "yo": "Ojo ti a da",
        "am": "የተፈጠረበት ቀን",
        "zu": "Usuku lokwenziwa",
    },
    "Message de contact": {
        "en": "Contact message",
        "de": "Kontaktnachricht",
        "es": "Mensaje de contacto",
        "it": "Messaggio di contatto",
        "pt": "Mensagem de contato",
        "ar": "رسالة الاتصال",
        "ja": "お問い合わせメッセージ",
        "ko": "문의 메시지",
        "zh": "联系消息",
        "ru": "Контактное сообщение",
        "hi": "संपर्क संदेश",
        "no": "Kontaktmelding",
        "sw": "Ujumbe wa mawasiliano",
        "vi": "Tin nhắn liên hệ",
        "yo": "Ifiranṣẹ olubasoro",
        "am": "የመገኛ መልእክት",
        "zu": "Umlayezo wokuxhumana",
    },
    "Messages de contact": {
        "en": "Contact messages",
        "de": "Kontaktnachrichten",
        "es": "Mensajes de contacto",
        "it": "Messaggi di contatto",
        "pt": "Mensagens de contato",
        "ar": "رسائل الاتصال",
        "ja": "お問い合わせメッセージ一覧",
        "ko": "문의 메시지 목록",
        "zh": "联系消息列表",
        "ru": "Контактные сообщения",
        "hi": "संपर्क संदेश",
        "no": "Kontaktmeldinger",
        "sw": "Ujumbe wa mawasiliano",
        "vi": "Tin nhắn liên hệ",
        "yo": "Awon ifiranṣẹ olubasoro",
        "am": "የመገኛ መልእክቶች",
        "zu": "Imilayezo yokuxhumana",
    },
    "Repondu": {
        "en": "Replied",
        "de": "Beantwortet",
        "es": "Respondido",
        "it": "Risposto",
        "pt": "Respondido",
        "ar": "تم الرد",
        "ja": "返信済み",
        "ko": "답변됨",
        "zh": "已回复",
        "ru": "Отвечено",
        "hi": "उत्तर दिया",
        "no": "Besvart",
        "sw": "Imejibiwa",
        "vi": "Đã trả lời",
        "yo": "A ti dahun",
        "am": "ተመልሷል",
        "zu": "Kuphendulwe",
    },
    "Repondu le": {
        "en": "Replied on",
        "de": "Beantwortet am",
        "es": "Respondido el",
        "it": "Risposto il",
        "pt": "Respondido em",
        "ar": "تم الرد في",
        "ja": "返信日",
        "ko": "답변 날짜",
        "zh": "回复日期",
        "ru": "Отвечено",
        "hi": "उत्तर दिया गया",
        "no": "Besvart den",
        "sw": "Imejibiwa tarehe",
        "vi": "Đã trả lời ngày",
        "yo": "A dahun ni",
        "am": "የተመለሰበት ቀን",
        "zu": "Kuphendulwe ngomhla ka",
    },
    "Lu le": {
        "en": "Read on",
        "de": "Gelesen am",
        "es": "Leído el",
        "it": "Letto il",
        "pt": "Lido em",
        "ar": "قُرئ في",
        "ja": "既読日",
        "ko": "읽은 날짜",
        "zh": "阅读日期",
        "ru": "Прочитано",
        "hi": "पढ़ा गया",
        "no": "Lest den",
        "sw": "Imesomwa tarehe",
        "vi": "Đã đọc ngày",
        "yo": "A ka ni",
        "am": "የተነበበበት ቀን",
        "zu": "Kufundwe ngomhla ka",
    },
    # Updated FAQ answer (after quote fix)
    "Pour créer un compte sur MartialComp, cliquez sur le bouton « S\\u2019inscrire » en haut à droite de la page d\\u2019accueil. Remplissez le formulaire avec vos informations et choisissez votre rôle (organisateur, club, arbitre, pratiquant ou spectateur). Vous recevrez un email de confirmation pour activer votre compte.": {
        "en": "To create an account on MartialComp, click on the \"Register\" button at the top right of the homepage. Fill in the form with your details and choose your role (organizer, club, referee, practitioner or spectator). You will receive a confirmation email to activate your account.",
        "de": "Um ein Konto bei MartialComp zu erstellen, klicken Sie oben rechts auf der Startseite auf \"Registrieren\". Füllen Sie das Formular mit Ihren Daten aus und wählen Sie Ihre Rolle (Veranstalter, Verein, Schiedsrichter, Sportler oder Zuschauer). Sie erhalten eine Bestätigungs-E-Mail zur Aktivierung Ihres Kontos.",
        "es": "Para crear una cuenta en MartialComp, haga clic en el botón \"Registrarse\" en la parte superior derecha de la página de inicio. Complete el formulario con sus datos y elija su rol (organizador, club, árbitro, practicante o espectador). Recibirá un correo electrónico de confirmación para activar su cuenta.",
        "it": "Per creare un account su MartialComp, cliccate sul pulsante \"Registrati\" in alto a destra della pagina iniziale. Compilate il modulo con i vostri dati e scegliete il vostro ruolo (organizzatore, club, arbitro, praticante o spettatore). Riceverete un'email di conferma per attivare il vostro account.",
        "pt": "Para criar uma conta no MartialComp, clique no botão \"Registar\" no canto superior direito da página inicial. Preencha o formulário com os seus dados e escolha o seu papel (organizador, clube, árbitro, praticante ou espectador). Receberá um email de confirmação para ativar a sua conta.",
    },
    # Email acknowledgment strings
    "Votre message a ete envoye avec succes ! Nous vous repondrons dans les plus brefs delais.": {
        "en": "Your message has been sent successfully! We will get back to you as soon as possible.",
        "de": "Ihre Nachricht wurde erfolgreich gesendet! Wir werden Ihnen so schnell wie möglich antworten.",
        "es": "¡Su mensaje ha sido enviado con éxito! Le responderemos lo antes posible.",
        "it": "Il vostro messaggio è stato inviato con successo! Vi risponderemo il prima possibile.",
        "pt": "A sua mensagem foi enviada com sucesso! Responderemos o mais breve possível.",
        "ar": "تم إرسال رسالتك بنجاح! سنرد عليك في أقرب وقت ممكن.",
        "ja": "メッセージが正常に送信されました！できるだけ早くお返事いたします。",
        "ko": "메시지가 성공적으로 전송되었습니다! 최대한 빨리 답변드리겠습니다.",
        "zh": "您的消息已成功发送！我们会尽快回复您。",
        "ru": "Ваше сообщение успешно отправлено! Мы ответим вам в ближайшее время.",
    },
}

# Also need the actual string from the template (with proper Unicode characters)
# The FAQ answer uses « S'inscrire » with actual Unicode
FAQ_ANSWER_MSGID = (
    "Pour créer un compte sur MartialComp, cliquez sur le bouton "
    "« S\u2019inscrire » en haut à droite de la page d\u2019accueil. "
    "Remplissez le formulaire avec vos informations et choisissez votre "
    "rôle (organisateur, club, arbitre, pratiquant ou spectateur). Vous "
    "recevrez un email de confirmation pour activer votre compte."
)


def get_po_file_path(lang):
    return os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', 'django.po')


def string_exists_in_po(po_content, msgid):
    """Check if a msgid already exists in the .po file."""
    # Escape for regex
    escaped = re.escape(msgid)
    # Check both single-line and multi-line msgid
    if f'msgid "{msgid}"' in po_content:
        return True
    # Also check if it's a substring of a multi-line msgid
    # Simple check: look for the first 40 chars
    if len(msgid) > 40:
        first_part = msgid[:40]
        if first_part in po_content:
            return True
    return False


def add_translations_to_po(lang):
    """Add missing translations to a language's .po file."""
    po_path = get_po_file_path(lang)
    if not os.path.exists(po_path):
        print(f"  SKIP: {po_path} does not exist")
        return 0

    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    added = 0
    new_entries = []

    for msgid, translations in TRANSLATIONS.items():
        # Handle the FAQ answer special case
        if "S\\u2019inscrire" in msgid:
            actual_msgid = FAQ_ANSWER_MSGID
        else:
            actual_msgid = msgid

        if string_exists_in_po(content, actual_msgid):
            continue

        msgstr = translations.get(lang, "")

        # Format the entry
        if len(actual_msgid) > 70:
            # Multi-line msgid
            words = actual_msgid.split(' ')
            lines = []
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > 70:
                    lines.append(current_line)
                    current_line = word
                else:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
            if current_line:
                lines.append(current_line)

            entry = 'msgid ""\n'
            for line in lines:
                entry += f'"{line} "\n'
            # Fix last line - remove trailing space
            entry = entry.rstrip('\n')
            last_quote = entry.rfind('" ')
            if last_quote > 0 and entry.endswith(' "'):
                pass
            # Actually let's just use simpler approach
            entry = f'msgid ""\n'
            for i, line in enumerate(lines):
                if i < len(lines) - 1:
                    entry += f'"{line} "\n'
                else:
                    entry += f'"{line}"\n'
        else:
            entry = f'msgid "{actual_msgid}"\n'

        if msgstr and len(msgstr) > 70:
            words = msgstr.split(' ')
            lines = []
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > 70:
                    lines.append(current_line)
                    current_line = word
                else:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
            if current_line:
                lines.append(current_line)

            entry += 'msgstr ""\n'
            for i, line in enumerate(lines):
                if i < len(lines) - 1:
                    entry += f'"{line} "\n'
                else:
                    entry += f'"{line}"\n'
        else:
            entry += f'msgstr "{msgstr}"\n'

        new_entries.append(entry)
        added += 1

    if new_entries:
        # Add before the last empty line or at the end
        all_entries = "\n" + "\n".join(new_entries)
        content = content.rstrip('\n') + "\n" + all_entries + "\n"

        with open(po_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return added


# Languages to process
LANGUAGES = ['en', 'de', 'es', 'it', 'pt', 'ar', 'ja', 'ko', 'zh', 'ru',
             'hi', 'no', 'sw', 'vi', 'yo', 'am', 'zu']

print("Adding missing contact form translations...")
print("=" * 50)

for lang in LANGUAGES:
    count = add_translations_to_po(lang)
    if count > 0:
        print(f"  {lang}: Added {count} translations")
    else:
        print(f"  {lang}: All translations already present")

# Also remove the old broken FAQ entry from English
print("\nFixing broken FAQ entry in English .po...")
en_po_path = get_po_file_path('en')
with open(en_po_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the old broken entry
old_entry = 'msgid "Pour créer un compte sur MartialComp, cliquez sur le bouton "\nmsgstr "To create an account on MartialComp, click on the button. "'
if old_entry in content:
    content = content.replace(old_entry + "\n\n", "")
    content = content.replace(old_entry + "\n", "")
    content = content.replace(old_entry, "")
    with open(en_po_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  Removed old broken FAQ entry")
else:
    print("  Old broken FAQ entry not found (already clean)")

print("\nDone! Now compile .mo files with: python manage.py compilemessages")
