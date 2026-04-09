#!/usr/bin/env python3
"""Add duplicate event translation keys to all language events.json files."""
import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mobile', 'src', 'i18n', 'locales')

TRANSLATIONS = {
    'de': {
        'duplicate': 'Duplizieren',
        'confirmDuplicate': 'Ereignis duplizieren',
        'confirmDuplicateMessage': 'Moechten Sie eine Kopie von "{{name}}" erstellen? Die Konfiguration wird ohne Teilnehmerdaten kopiert.',
        'duplicateSuccess': 'Ereignis dupliziert',
        'duplicateSuccessMessage': '"{{name}}" wurde erfolgreich erstellt.',
        'duplicateError': 'Ereignis konnte nicht dupliziert werden',
        'viewDuplicate': 'Kopie anzeigen',
    },
    'es': {
        'duplicate': 'Duplicar',
        'confirmDuplicate': 'Duplicar evento',
        'confirmDuplicateMessage': 'Desea crear una copia de "{{name}}"? La configuracion se copiara sin los datos de los participantes.',
        'duplicateSuccess': 'Evento duplicado',
        'duplicateSuccessMessage': '"{{name}}" se ha creado con exito.',
        'duplicateError': 'No se pudo duplicar el evento',
        'viewDuplicate': 'Ver copia',
    },
    'it': {
        'duplicate': 'Duplica',
        'confirmDuplicate': "Duplica l'evento",
        'confirmDuplicateMessage': 'Vuoi creare una copia di "{{name}}"? La configurazione verra copiata senza i dati dei partecipanti.',
        'duplicateSuccess': 'Evento duplicato',
        'duplicateSuccessMessage': '"{{name}}" stato creato con successo.',
        'duplicateError': "Impossibile duplicare l'evento",
        'viewDuplicate': 'Vedi copia',
    },
    'pt': {
        'duplicate': 'Duplicar',
        'confirmDuplicate': 'Duplicar evento',
        'confirmDuplicateMessage': 'Deseja criar uma copia de "{{name}}"? A configuracao sera copiada sem os dados dos participantes.',
        'duplicateSuccess': 'Evento duplicado',
        'duplicateSuccessMessage': '"{{name}}" foi criado com sucesso.',
        'duplicateError': 'Nao foi possivel duplicar o evento',
        'viewDuplicate': 'Ver copia',
    },
    'ar': {
        'duplicate': '\u062a\u0643\u0631\u0627\u0631',
        'confirmDuplicate': '\u062a\u0643\u0631\u0627\u0631 \u0627\u0644\u062d\u062f\u062b',
        'confirmDuplicateMessage': '\u0647\u0644 \u062a\u0631\u064a\u062f \u0625\u0646\u0634\u0627\u0621 \u0646\u0633\u062e\u0629 \u0645\u0646 "{{name}}"? \u0633\u064a\u062a\u0645 \u0646\u0633\u062e \u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a \u0628\u062f\u0648\u0646 \u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0645\u0634\u0627\u0631\u0643\u064a\u0646.',
        'duplicateSuccess': '\u062a\u0645 \u062a\u0643\u0631\u0627\u0631 \u0627\u0644\u062d\u062f\u062b',
        'duplicateSuccessMessage': '\u062a\u0645 \u0625\u0646\u0634\u0627\u0621 "{{name}}" \u0628\u0646\u062c\u0627\u062d.',
        'duplicateError': '\u062a\u0639\u0630\u0631 \u062a\u0643\u0631\u0627\u0631 \u0627\u0644\u062d\u062f\u062b',
        'viewDuplicate': '\u0639\u0631\u0636 \u0627\u0644\u0646\u0633\u062e\u0629',
    },
    'ru': {
        'duplicate': '\u0414\u0443\u0431\u043b\u0438\u0440\u043e\u0432\u0430\u0442\u044c',
        'confirmDuplicate': '\u0414\u0443\u0431\u043b\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0441\u043e\u0431\u044b\u0442\u0438\u0435',
        'confirmDuplicateMessage': '\u0425\u043e\u0442\u0438\u0442\u0435 \u0441\u043e\u0437\u0434\u0430\u0442\u044c \u043a\u043e\u043f\u0438\u044e "{{name}}"? \u041a\u043e\u043d\u0444\u0438\u0433\u0443\u0440\u0430\u0446\u0438\u044f \u0431\u0443\u0434\u0435\u0442 \u0441\u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u0430 \u0431\u0435\u0437 \u0434\u0430\u043d\u043d\u044b\u0445 \u0443\u0447\u0430\u0441\u0442\u043d\u0438\u043a\u043e\u0432.',
        'duplicateSuccess': '\u0421\u043e\u0431\u044b\u0442\u0438\u0435 \u0434\u0443\u0431\u043b\u0438\u0440\u043e\u0432\u0430\u043d\u043e',
        'duplicateSuccessMessage': '"{{name}}" \u0443\u0441\u043f\u0435\u0448\u043d\u043e \u0441\u043e\u0437\u0434\u0430\u043d\u043e.',
        'duplicateError': '\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0434\u0443\u0431\u043b\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0441\u043e\u0431\u044b\u0442\u0438\u0435',
        'viewDuplicate': '\u041f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u043a\u043e\u043f\u0438\u044e',
    },
    'hi': {
        'duplicate': '\u0921\u0941\u092a\u094d\u0932\u0940\u0915\u0947\u091f',
        'confirmDuplicate': '\u0907\u0935\u0947\u0902\u091f \u0921\u0941\u092a\u094d\u0932\u0940\u0915\u0947\u091f \u0915\u0930\u0947\u0902',
        'confirmDuplicateMessage': '\u0915\u094d\u092f\u093e \u0906\u092a "{{name}}" \u0915\u0940 \u090f\u0915 \u092a\u094d\u0930\u0924\u093f \u092c\u0928\u093e\u0928\u093e \u091a\u093e\u0939\u0924\u0947 \u0939\u0948\u0902? \u0915\u0949\u0928\u094d\u092b\u093c\u093f\u0917\u0930\u0947\u0936\u0928 \u092a\u094d\u0930\u0924\u093f\u092d\u093e\u0917\u0940 \u0921\u0947\u091f\u093e \u0915\u0947 \u092c\u093f\u0928\u093e \u0915\u0949\u092a\u0940 \u0915\u093f\u092f\u093e \u091c\u093e\u090f\u0917\u093e\u0964',
        'duplicateSuccess': '\u0907\u0935\u0947\u0902\u091f \u0921\u0941\u092a\u094d\u0932\u0940\u0915\u0947\u091f \u0915\u093f\u092f\u093e \u0917\u092f\u093e',
        'duplicateSuccessMessage': '"{{name}}" \u0938\u092b\u0932\u0924\u093e\u092a\u0942\u0930\u094d\u0935\u0915 \u092c\u0928\u093e\u092f\u093e \u0917\u092f\u093e \u0939\u0948\u0964',
        'duplicateError': '\u0907\u0935\u0947\u0902\u091f \u0921\u0941\u092a\u094d\u0932\u0940\u0915\u0947\u091f \u0915\u0930\u0928\u0947 \u092e\u0947\u0902 \u0905\u0938\u092e\u0930\u094d\u0925',
        'viewDuplicate': '\u092a\u094d\u0930\u0924\u093f \u0926\u0947\u0916\u0947\u0902',
    },
    'vi': {
        'duplicate': 'Nh\u00e2n b\u1ea3n',
        'confirmDuplicate': 'Nh\u00e2n b\u1ea3n s\u1ef1 ki\u1ec7n',
        'confirmDuplicateMessage': 'B\u1ea1n c\u00f3 mu\u1ed1n t\u1ea1o b\u1ea3n sao c\u1ee7a "{{name}}"? C\u1ea5u h\u00ecnh s\u1ebd \u0111\u01b0\u1ee3c sao ch\u00e9p m\u00e0 kh\u00f4ng c\u00f3 d\u1eef li\u1ec7u ng\u01b0\u1eddi tham gia.',
        'duplicateSuccess': '\u0110\u00e3 nh\u00e2n b\u1ea3n s\u1ef1 ki\u1ec7n',
        'duplicateSuccessMessage': '"{{name}}" \u0111\u00e3 \u0111\u01b0\u1ee3c t\u1ea1o th\u00e0nh c\u00f4ng.',
        'duplicateError': 'Kh\u00f4ng th\u1ec3 nh\u00e2n b\u1ea3n s\u1ef1 ki\u1ec7n',
        'viewDuplicate': 'Xem b\u1ea3n sao',
    },
    'ja': {
        'duplicate': '\u8907\u88fd',
        'confirmDuplicate': '\u30a4\u30d9\u30f3\u30c8\u3092\u8907\u88fd',
        'confirmDuplicateMessage': '"{{name}}"\u306e\u30b3\u30d4\u30fc\u3092\u4f5c\u6210\u3057\u307e\u3059\u304b\uff1f\u53c2\u52a0\u8005\u30c7\u30fc\u30bf\u306a\u3057\u3067\u8a2d\u5b9a\u304c\u30b3\u30d4\u30fc\u3055\u308c\u307e\u3059\u3002',
        'duplicateSuccess': '\u30a4\u30d9\u30f3\u30c8\u304c\u8907\u88fd\u3055\u308c\u307e\u3057\u305f',
        'duplicateSuccessMessage': '"{{name}}"\u304c\u6b63\u5e38\u306b\u4f5c\u6210\u3055\u308c\u307e\u3057\u305f\u3002',
        'duplicateError': '\u30a4\u30d9\u30f3\u30c8\u3092\u8907\u88fd\u3067\u304d\u307e\u305b\u3093',
        'viewDuplicate': '\u30b3\u30d4\u30fc\u3092\u898b\u308b',
    },
    'ko': {
        'duplicate': '\ubcf5\uc81c',
        'confirmDuplicate': '\uc774\ubca4\ud2b8 \ubcf5\uc81c',
        'confirmDuplicateMessage': '"{{name}}"\uc758 \uc0ac\ubcf8\uc744 \ub9cc\ub4dc\uc2dc\uaca0\uc2b5\ub2c8\uae4c? \ucc38\uac00\uc790 \ub370\uc774\ud130 \uc5c6\uc774 \uad6c\uc131\uc774 \ubcf5\uc0ac\ub429\ub2c8\ub2e4.',
        'duplicateSuccess': '\uc774\ubca4\ud2b8\uac00 \ubcf5\uc81c\ub418\uc5c8\uc2b5\ub2c8\ub2e4',
        'duplicateSuccessMessage': '"{{name}}"\uc774(\uac00) \uc131\uacf5\uc801\uc73c\ub85c \uc0dd\uc131\ub418\uc5c8\uc2b5\ub2c8\ub2e4.',
        'duplicateError': '\uc774\ubca4\ud2b8\ub97c \ubcf5\uc81c\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4',
        'viewDuplicate': '\uc0ac\ubcf8 \ubcf4\uae30',
    },
    'zh': {
        'duplicate': '\u590d\u5236',
        'confirmDuplicate': '\u590d\u5236\u6d3b\u52a8',
        'confirmDuplicateMessage': '\u60a8\u8981\u521b\u5efa"{{name}}"\u7684\u526f\u672c\u5417\uff1f\u914d\u7f6e\u5c06\u5728\u4e0d\u5305\u542b\u53c2\u4e0e\u8005\u6570\u636e\u7684\u60c5\u51b5\u4e0b\u590d\u5236\u3002',
        'duplicateSuccess': '\u6d3b\u52a8\u5df2\u590d\u5236',
        'duplicateSuccessMessage': '"{{name}}"\u5df2\u6210\u529f\u521b\u5efa\u3002',
        'duplicateError': '\u65e0\u6cd5\u590d\u5236\u6d3b\u52a8',
        'viewDuplicate': '\u67e5\u770b\u526f\u672c',
    },
    'no': {
        'duplicate': 'Dupliser',
        'confirmDuplicate': 'Dupliser hendelse',
        'confirmDuplicateMessage': 'Vil du lage en kopi av "{{name}}"? Konfigurasjonen kopieres uten deltagerdata.',
        'duplicateSuccess': 'Hendelse duplisert',
        'duplicateSuccessMessage': '"{{name}}" er opprettet.',
        'duplicateError': 'Kunne ikke duplisere hendelsen',
        'viewDuplicate': 'Vis kopi',
    },
    'sw': {
        'duplicate': 'Nakili',
        'confirmDuplicate': 'Nakili tukio',
        'confirmDuplicateMessage': 'Je, unataka kuunda nakala ya "{{name}}"? Usanidi utanakiliwa bila data ya washiriki.',
        'duplicateSuccess': 'Tukio limenakiliwa',
        'duplicateSuccessMessage': '"{{name}}" limeundwa kwa mafanikio.',
        'duplicateError': 'Imeshindwa kunakili tukio',
        'viewDuplicate': 'Tazama nakala',
    },
    'am': {
        'duplicate': '\u1245\u1302',
        'confirmDuplicate': '\u12AD\u1235\u1270\u1275 \u1245\u1302',
        'confirmDuplicateMessage': '\u12E8"{{name}}" \u1245\u1302 \u1218\u134D\u1320\u122D \u12ED\u1348\u120D\u130B\u1209? \u121B\u12CB\u1240\u1229 \u12EB\u1208 \u1270\u1233\u1273\u134A \u12CD\u1202\u1265 \u12ED\u1308\u1208\u1260\u1323\u120D\u1362',
        'duplicateSuccess': '\u12AD\u1235\u1270\u1275 \u1270\u1308\u120D\u1265\u1327\u120D',
        'duplicateSuccessMessage': '"{{name}}" \u1260\u1270\u1233\u12AB \u1201\u1294\u1273 \u1270\u1348\u1325\u122F\u120D\u1362',
        'duplicateError': '\u12AD\u1235\u1270\u1275 \u1218\u1308\u120D\u1260\u1325 \u12A0\u120D\u1270\u127B\u1208\u121D',
        'viewDuplicate': '\u1245\u1302 \u12ED\u1218\u120D\u12A8\u1271',
    },
    'yo': {
        'duplicate': '\u1E62e \u00e0d\u00e0k\u1ECD',
        'confirmDuplicate': '\u1E62e \u00e0d\u00e0k\u1ECD \u00ec\u1E63\u1EB9\u0300l\u1EB9\u0300',
        'confirmDuplicateMessage': '\u1E62\u00e9 o f\u1EB9\u0301 \u1E63e \u00e0d\u00e0k\u1ECD "{{name}}"? A \u00f3\u00f2 da \u00e0t\u00fant\u00f2 \u1E63e l\u00e1\u00ecs\u00ed d\u00e1t\u00e0 \u00e0w\u1ECDn ol\u00f9k\u00f3pa.',
        'duplicateSuccess': 'A ti \u1E63e \u00e0d\u00e0k\u1ECD \u00ec\u1E63\u1EB9\u0300l\u1EB9\u0300',
        'duplicateSuccessMessage': 'A ti \u1E63\u1EB9\u0300d\u00e1 "{{name}}" l\u00e1\u1E63ey\u1ECDr\u00ed.',
        'duplicateError': 'K\u00f2 \u1E63e\u00e9 \u1E63e \u00e0d\u00e0k\u1ECD \u00ec\u1E63\u1EB9\u0300l\u1EB9\u0300',
        'viewDuplicate': 'Wo \u00e0d\u00e0k\u1ECD',
    },
    'zu': {
        'duplicate': 'Phinda',
        'confirmDuplicate': 'Phinda umcimbi',
        'confirmDuplicateMessage': 'Ufuna ukwenza ikhophi ka-"{{name}}"? Ukumisa kuzokopishwa ngaphandle kwedatha yababambe iqhaza.',
        'duplicateSuccess': 'Umcimbi uphindwe',
        'duplicateSuccessMessage': '"{{name}}" udalwe ngempumelelo.',
        'duplicateError': 'Ayikwazanga ukuphinda umcimbi',
        'viewDuplicate': 'Buka ikhophi',
    },
    'nl': {
        'duplicate': 'Dupliceren',
        'confirmDuplicate': 'Evenement dupliceren',
        'confirmDuplicateMessage': 'Wilt u een kopie maken van "{{name}}"? De configuratie wordt gekopieerd zonder deelnemersgegevens.',
        'duplicateSuccess': 'Evenement gedupliceerd',
        'duplicateSuccessMessage': '"{{name}}" is succesvol aangemaakt.',
        'duplicateError': 'Kan evenement niet dupliceren',
        'viewDuplicate': 'Kopie bekijken',
    },
    'ln': {
        'duplicate': 'Kozongisa',
        'confirmDuplicate': 'Kozongisa likambo',
        'confirmDuplicateMessage': 'Olingi kosala kopi ya "{{name}}"? Configuration ekozongisama kozanga ba donnees ya ba participants.',
        'duplicateSuccess': 'Likambo ezongisami',
        'duplicateSuccessMessage': '"{{name}}" esalemi malamu.',
        'duplicateError': 'Ekoki te kozongisa likambo',
        'viewDuplicate': 'Tala kopi',
    },
    'bm': {
        'duplicate': 'Tila',
        'confirmDuplicate': 'Ka fen tila',
        'confirmDuplicateMessage': 'I b\'a fe ka "{{name}}" kopi do ke wa? Labenni bena tila k\'a soro mogow ka kunnafonin te.',
        'duplicateSuccess': 'Fen tilala',
        'duplicateSuccessMessage': '"{{name}}" dabora ka ne.',
        'duplicateError': 'A ma se ka fen tila',
        'viewDuplicate': 'Kopi laje',
    },
    'ig': {
        'duplicate': 'Megharia',
        'confirmDuplicate': 'Megharia mmemme',
        'confirmDuplicateMessage': 'I choro imeputa otu "{{name}}"? A ga-edetuo nhazi ya na-enweghi data ndi sonyere.',
        'duplicateSuccess': 'Emegharila mmemme',
        'duplicateSuccessMessage': 'Emeputala "{{name}}" nke oma.',
        'duplicateError': 'Enweghi ike imegharia mmemme',
        'viewDuplicate': 'Lee nke emegharia',
    },
    'ha': {
        'duplicate': 'Kwafi',
        'confirmDuplicate': 'Kwafi taron',
        'confirmDuplicateMessage': 'Kuna so ka yi kwafin "{{name}}"? Za a kwafi tsarin ba tare da bayanan mahalarta ba.',
        'duplicateSuccess': 'An kwafi taron',
        'duplicateSuccessMessage': 'An kirkiri "{{name}}" cikin nasara.',
        'duplicateError': 'Ba a iya kwafin taron ba',
        'viewDuplicate': 'Duba kwafi',
    },
}


def add_translations():
    updated = 0
    for lang, trans in TRANSLATIONS.items():
        filepath = os.path.join(LOCALES_DIR, lang, 'events.json')
        if not os.path.exists(filepath):
            print(f"  SKIP: {lang} (no events.json)")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'detail' not in data:
            print(f"  SKIP: {lang} (no 'detail' section)")
            continue

        if 'duplicate' in data['detail']:
            print(f"  SKIP: {lang} (already has duplicate keys)")
            continue

        data['detail'].update(trans)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')

        print(f"  OK: {lang} - added {len(trans)} keys")
        updated += 1

    print(f"\nUpdated {updated} files")


if __name__ == '__main__':
    add_translations()
