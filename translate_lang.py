#!/usr/bin/env python3
"""
Translate a single PO language with threading-based timeout.
Works on Windows (no SIGALRM needed).
Usage: python translate_lang.py <lang_code>
"""
import sys
import os
import time
import threading
import polib
from deep_translator import GoogleTranslator

SAVE_EVERY = 100
TIMEOUT_SECS = 10


def log(log_file, msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def translate_with_timeout(translator, text, timeout=TIMEOUT_SECS):
    """Translate with a thread-based timeout."""
    result = [None]
    error = [None]

    def worker():
        try:
            result[0] = translator.translate(text)
        except Exception as e:
            error[0] = e

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        # Thread still running = timed out
        return None
    if error[0]:
        return None
    return result[0]


def safe_translate(translator, text):
    """Translate with retries and timeout."""
    for attempt in range(3):
        r = translate_with_timeout(translator, text)
        if r is not None and r.strip():
            return r
        if attempt < 2:
            # Recreate translator on failure (fresh connection)
            time.sleep(1 + attempt)
    return ''


def main():
    if len(sys.argv) < 2:
        print("Usage: python translate_lang.py <lang_code>")
        sys.exit(1)

    lang = sys.argv[1].lower()
    log_file = f'translate_progress_{lang}.log'
    po_path = f'locale/{lang}/LC_MESSAGES/django.po'

    if not os.path.exists(po_path):
        print(f"ERROR: {po_path} not found")
        sys.exit(1)

    def _log(msg):
        log(log_file, msg)

    _log(f"=== {lang.upper()} START (timeout={TIMEOUT_SECS}s) ===")
    po = polib.pofile(po_path)
    entries = po.untranslated_entries()
    total = len(entries)
    _log(f"{lang.upper()}: {total} entries to translate")

    if total == 0:
        _log("Nothing to do!")
        return

    translator = GoogleTranslator(source='fr', target=lang)
    ok = 0
    fail = 0
    timeout_count = 0
    t0 = time.time()

    for i, entry in enumerate(entries):
        if entry.msgid_plural:
            s = safe_translate(translator, entry.msgid)
            p = safe_translate(translator, entry.msgid_plural)
            if s and p:
                entry.msgstr_plural = {0: s, 1: p}
                ok += 1
            else:
                fail += 1
        else:
            r = safe_translate(translator, entry.msgid)
            if r:
                entry.msgstr = r
                ok += 1
            else:
                fail += 1
                # Recreate translator if too many failures
                if fail % 10 == 0:
                    translator = GoogleTranslator(
                        source='fr', target=lang
                    )
                    time.sleep(2)

        # Save periodically
        if ok > 0 and ok % SAVE_EVERY == 0:
            po.save()
            elapsed = time.time() - t0
            rate = ok / elapsed * 60 if elapsed > 0 else 0
            remain = total - i - 1
            eta = remain / (rate / 60) / 60 if rate > 0 else 0
            _log(
                f"  {lang.upper()} SAVE: {ok}/{total} ok, "
                f"{fail} fail, {rate:.0f}/min, ETA {eta:.1f}m"
            )

        # Brief delay every 10 entries
        if i > 0 and i % 10 == 0:
            time.sleep(0.2)

    # Final save
    po.save()
    elapsed = time.time() - t0
    remaining = len(
        polib.pofile(po_path).untranslated_entries()
    )
    _log(
        f"=== {lang.upper()} DONE: {ok} ok, {fail} fail, "
        f"{remaining} remain, {elapsed/60:.1f}min ==="
    )


if __name__ == '__main__':
    main()
