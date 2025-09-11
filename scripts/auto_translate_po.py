#!/usr/bin/env python3
"""
Auto-translate PO files (FR -> PT) with placeholder safety.
Prefers DeepL (DEEPL_API_KEY), falls back to googletrans.

Usage examples:
  python scripts/auto_translate_po.py locale/pt/LC_MESSAGES/django.po --source fr --target PT-PT --prefer-deepl
  python scripts/auto_translate_po.py --glob "locale/pt/LC_MESSAGES/*.po" --source fr --target PT-PT --prefer-deepl

Notes:
  - Protects placeholders like %(name)s, %s, {0}, etc.
  - Respects existing translations unless --overwrite is provided.
  - Handles plural forms (nplurals=2 for Portuguese).
"""

import os
import re
import time
import glob as pyglob
import argparse
from typing import Dict, List, Tuple

import polib


def build_placeholder_map(text: str) -> Tuple[str, Dict[str, str]]:
    patterns = [
        r"%\([A-Za-z0-9_]+\)[sd]?",   # %(name)s, %(count)d
        r"%[sd]",                     # %s, %d
        r"\{[^}]+\}",               # {0}, {name}
        r"\$[A-Za-z_][A-Za-z0-9_]*",  # $var
    ]
    placeholder_map: Dict[str, str] = {}

    def replacer(match):
        original = match.group(0)
        token = f"__PH_{len(placeholder_map)}__"
        placeholder_map[token] = original
        return token

    combined = re.compile("|".join(patterns))
    protected = combined.sub(replacer, text)
    return protected, placeholder_map


def restore_placeholders(text: str, placeholder_map: Dict[str, str]) -> str:
    for token, original in placeholder_map.items():
        text = text.replace(token, original)
    return text


class TranslatorEngine:
    def __init__(self, prefer_deepl: bool = True):
        self.use_deepl = False
        self.deepl = None
        self.google = None  # googletrans (deprecated on Python>=3.13)
        self.deep_translator = None  # deep_translator.GoogleTranslator

        if prefer_deepl and os.getenv("DEEPL_API_KEY"):
            try:
                import deepl  # type: ignore
                self.deepl = deepl.Translator(os.environ["DEEPL_API_KEY"])
                self.use_deepl = True
            except Exception:
                self.use_deepl = False

        if not self.use_deepl:
            # Try deep_translator first (compatible with Python 3.13)
            try:
                from deep_translator import GoogleTranslator as _DTGoogle  # type: ignore
                self.deep_translator = _DTGoogle
            except Exception:
                self.deep_translator = None

        if not self.use_deepl and self.deep_translator is None:
            # Fallback to googletrans for older environments (may fail on Python 3.13)
            try:
                from googletrans import Translator  # type: ignore
                self.google = Translator()
            except Exception as exc:
                raise RuntimeError(
                    "No translation engine available. Provide DEEPL_API_KEY or install 'deep-translator'."
                ) from exc

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return text

        protected, ph_map = build_placeholder_map(text)

        if self.use_deepl:
            # DeepL expects PT-PT or PT-BR; default to PT-PT when PT is given
            deepl_target = target_lang.upper()
            if deepl_target == "PT":
                deepl_target = "PT-PT"
            result = self.deepl.translate_text(
                protected,
                source_lang=source_lang.upper(),
                target_lang=deepl_target,
            )
            translated = str(result.text)
        elif self.deep_translator is not None:
            # deep_translator expects ISO-639-1 like 'fr', 'pt'
            dest_lang = target_lang.lower()
            if dest_lang.startswith("pt"):
                dest_lang = "pt"
            src_lang = source_lang.lower()
            translated = self.deep_translator(source=src_lang, target=dest_lang).translate(protected)
        else:
            # googletrans fallback (may be incompatible on Python 3.13)
            dest_lang = target_lang.lower()
            if dest_lang.startswith("pt"):
                dest_lang = "pt"
            src_lang = source_lang.lower()
            result = self.google.translate(protected, src=src_lang, dest=dest_lang)
            translated = str(result.text)

        return restore_placeholders(translated, ph_map)


def should_translate(entry: polib.POEntry, overwrite: bool) -> bool:
    if overwrite:
        return True
    if entry.obsolete:
        return False
    if entry.fuzzy:
        return True
    if entry.msgid_plural:
        return any(not v for v in entry.msgstr_plural.values())
    return not entry.translated()


def translate_entry(
    entry: polib.POEntry,
    engine: TranslatorEngine,
    src: str,
    tgt: str,
    sleep_s: float,
) -> bool:
    changed = False
    if entry.msgid_plural:
        if 0 not in entry.msgstr_plural:
            entry.msgstr_plural[0] = ""
        if 1 not in entry.msgstr_plural:
            entry.msgstr_plural[1] = ""

        singular = engine.translate(entry.msgid, src, tgt)
        plural = engine.translate(entry.msgid_plural, src, tgt)

        if singular and entry.msgstr_plural.get(0) != singular:
            entry.msgstr_plural[0] = singular
            changed = True
        if plural and entry.msgstr_plural.get(1) != plural:
            entry.msgstr_plural[1] = plural
            changed = True
        if changed:
            entry.flags = [f for f in entry.flags if f != "fuzzy"]
        if sleep_s:
            time.sleep(sleep_s)
    else:
        translated = engine.translate(entry.msgid, src, tgt)
        if translated and entry.msgstr != translated:
            entry.msgstr = translated
            entry.flags = [f for f in entry.flags if f != "fuzzy"]
            changed = True
        if sleep_s:
            time.sleep(sleep_s)
    return changed


def process_file(
    path: str,
    source: str,
    target: str,
    overwrite: bool,
    rate_limit: int,
    prefer_deepl: bool,
    max_entries: int | None = None,
) -> Tuple[int, int]:
    po = polib.pofile(path)
    engine = TranslatorEngine(prefer_deepl=prefer_deepl)
    sleep_s = 60.0 / rate_limit if rate_limit > 0 else 0.0

    changed_count = 0
    total_considered = 0
    processed = 0
    for entry in po:
        if should_translate(entry, overwrite):
            total_considered += 1
            if translate_entry(entry, engine, source, target, sleep_s):
                changed_count += 1
            processed += 1
            if max_entries is not None and processed >= max_entries:
                break

    if changed_count > 0:
        meta = po.metadata or {}
        meta["X-Translated-By"] = "auto-script"
        meta["Language"] = target.lower()
        po.metadata = meta
        po.save(path)
    return changed_count, total_considered


def main():
    parser = argparse.ArgumentParser(
        description="Auto-translate .po files FR -> PT with placeholder protection."
    )
    parser.add_argument("input", nargs="*", help="PO file paths")
    parser.add_argument("--glob", help="Glob pattern (e.g., locale/pt/LC_MESSAGES/*.po)")
    parser.add_argument("--source", default="fr", help="Source language (default: fr)")
    parser.add_argument(
        "--target", default="pt", help="Target language (e.g., pt, PT-PT, PT-BR)"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Rewrite even already translated entries"
    )
    parser.add_argument(
        "--rate-per-minute", type=int, default=90, help="Requests per minute limit"
    )
    parser.add_argument(
        "--prefer-deepl", action="store_true", help="Prefer DeepL if available"
    )
    parser.add_argument(
        "--max-entries", type=int, default=None, help="Limit number of entries to process"
    )
    args = parser.parse_args()

    files: List[str] = []
    if args.glob:
        files.extend(pyglob.glob(args.glob))
    files.extend(args.input)
    files = [f for f in files if f.endswith(".po")]

    if not files:
        print("No .po files provided. Use a path or --glob.")
        return

    total_changed = 0
    total_considered = 0
    for f in files:
        changed, considered = process_file(
            f,
            args.source,
            args.target,
            args.overwrite,
            args.rate_per_minute,
            args.prefer_deepl,
            args.max_entries,
        )
        print(f"[{f}] changed: {changed} / candidates: {considered}")
        total_changed += changed
        total_considered += considered

    print(f"TOTAL changed: {total_changed} / candidates: {total_considered}")


if __name__ == "__main__":
    main()
