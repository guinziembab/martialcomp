#!/usr/bin/env python3
"""
Auto-translate remaining PO entries using Google Translate via deep-translator.
Processes one language at a time, saves after each batch.
Logs progress to a file for monitoring.
"""
import sys
import os
import io
import time
import polib
from deep_translator import GoogleTranslator

BATCH_SIZE = 10
SAVE_EVERY = 100
DELAY = 0.2
LOG_FILE = 'translate_progress.log'

LANG_MAP = {
    'ko': 'ko', 'vi': 'vi', 'no': 'no',
    'ru': 'ru', 'yo': 'yo', 'zu': 'zu',
}


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    try:
        print(line, flush=True)
    except Exception:
        pass


def translate_one(translator, text):
    for attempt in range(3):
        try:
            r = translator.translate(text)
            if r and r.strip():
                return r
            return ''
        except Exception as e:
            if attempt < 2:
                time.sleep(1 + attempt)
            else:
                log(f"  FAIL after 3 tries: {str(e)[:60]}")
                return ''


def translate_language(lang_code):
    gc = LANG_MAP.get(lang_code, lang_code)
    po_path = f'locale/{lang_code}/LC_MESSAGES/django.po'

    if not os.path.exists(po_path):
        log(f"ERROR: {po_path} not found")
        return

    log(f"=== {lang_code.upper()} START ===")
    po = polib.pofile(po_path)
    entries = po.untranslated_entries()
    total = len(entries)
    log(f"{lang_code.upper()}: {total} entries to translate")

    if total == 0:
        log("Nothing to do!")
        return

    t = GoogleTranslator(source='fr', target=gc)
    ok = 0
    fail = 0
    t0 = time.time()

    for i, entry in enumerate(entries):
        if entry.msgid_plural:
            s = translate_one(t, entry.msgid)
            p = translate_one(t, entry.msgid_plural)
            if s and p:
                entry.msgstr_plural = {0: s, 1: p}
                ok += 1
            else:
                fail += 1
        else:
            r = translate_one(t, entry.msgid)
            if r:
                entry.msgstr = r
                ok += 1
            else:
                fail += 1

        # Save periodically
        if ok > 0 and ok % SAVE_EVERY == 0:
            po.save()
            elapsed = time.time() - t0
            rate = ok / elapsed * 60
            eta = (total - i - 1) / (rate / 60) / 60 if rate > 0 else 0
            log(f"  {lang_code.upper()} SAVE: {ok}/{total} ok, "
                f"{fail} fail, {rate:.0f}/min, ETA {eta:.1f}m")

        # Brief delay
        if i % BATCH_SIZE == 0 and i > 0:
            time.sleep(DELAY)

    po.save()
    elapsed = time.time() - t0
    remaining = len(polib.pofile(po_path).untranslated_entries())
    log(f"=== {lang_code.upper()} DONE: {ok} ok, {fail} fail, "
        f"{remaining} remain, {elapsed/60:.1f}min ===")


if __name__ == '__main__':
    # Clear log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Translation started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    if len(sys.argv) < 2:
        print("Usage: python auto_translate_po.py <lang|all>")
        sys.exit(1)

    lang = sys.argv[1].lower()
    if lang == 'all':
        for code in LANG_MAP:
            translate_language(code)
    elif lang in LANG_MAP:
        translate_language(lang)
    else:
        print(f"Unknown: {lang}. Available: {', '.join(LANG_MAP.keys())}")
