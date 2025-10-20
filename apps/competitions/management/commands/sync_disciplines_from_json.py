"""
Management command to sync Discipline records from a JSON dump (exported in development)
into the current environment (e.g., production), ensuring French and English descriptions
are populated.

Usage examples:
  - Basic (uses default input path if present):
      python manage.py sync_disciplines_from_json --settings=config.settings.production

  - Specify input file explicitly:
      python manage.py sync_disciplines_from_json \
        --input=disciplines_dev.clean.json \
        --settings=config.settings.production

  - Dry run (no DB changes):
      python manage.py sync_disciplines_from_json --dry-run --settings=config.settings.production

  - Disable translation and copy FR -> EN when EN is missing:
      python manage.py sync_disciplines_from_json --no-translate --copy-fr-to-en \
        --settings=config.settings.production

Notes:
  - The command accepts both a clean Django dump (list of {"model","pk","fields"})
    and a dump polluted with log lines before/after the JSON array. It will attempt to
    extract the first JSON array found in the file.
  - If description_en is missing and translation is enabled, the command will attempt to
    translate French -> English using DeepL if a DEEPL_API_KEY is present. If translation
    cannot be performed, it can copy FR to EN as a fallback when --copy-fr-to-en is set.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Q


def _read_json_array_from_file(path: str) -> List[Any]:
    """Read a file and return the first JSON array contained within it.

    This function is robust to files that include log lines before/after the JSON.
    """
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    # Locate the first '[' and the last ']' to extract the JSON array
    start_index = content.find("[")
    end_index = content.rfind("]")
    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise ValueError(
            f"Could not find a JSON array in file: {path}. Make sure it contains a JSON list."
        )

    array_text = content[start_index : end_index + 1].strip()

    try:
        data = json.loads(array_text)
        if not isinstance(data, list):
            raise ValueError("Top-level JSON entity is not a list")
        return data
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse JSON array from {path}: {exc}") from exc


def _get_translator_if_available():
    """Return a DeepL translator instance if available and configured, else None."""
    try:
        # deepl_translate.py is at repo root; manage.py typically adds project root to sys.path
        from deepl_translate import DeepLTranslator  # type: ignore

        translator = DeepLTranslator()
        # If no API key, translator will be effectively a no-op; return it anyway
        return translator
    except Exception:
        return None


class Command(BaseCommand):
    help = (
        "Sync competitions.Discipline entries from a development JSON export. "
        "Ensures FR/EN descriptions are populated."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--input",
            dest="input_path",
            default=None,
            help=(
                "Path to JSON file. Defaults to 'disciplines_dev.clean.json' if present "
                "else 'disciplines_dev.json' in the project root."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Preview changes without modifying the database.",
        )
        parser.add_argument(
            "--no-translate",
            action="store_true",
            dest="no_translate",
            help="Do not attempt EN translation; only use existing values.",
        )
        parser.add_argument(
            "--copy-fr-to-en",
            action="store_true",
            dest="copy_fr_to_en",
            help="If EN is missing, copy FR text to EN as fallback.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Process at most N disciplines (for testing).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        from apps.competitions.models import Discipline  # imported here to avoid early imports

        input_path = options.get("input_path")
        dry_run: bool = bool(options.get("dry_run"))
        no_translate: bool = bool(options.get("no_translate"))
        copy_fr_to_en: bool = bool(options.get("copy_fr_to_en"))
        limit: Optional[int] = options.get("limit")

        # Resolve default input path if not provided
        if not input_path:
            if os.path.exists("disciplines_dev.clean.json"):
                input_path = "disciplines_dev.clean.json"
            else:
                input_path = "disciplines_dev.json"

        self.stdout.write(self.style.HTTP_INFO(f"Reading: {input_path}"))
        data = _read_json_array_from_file(input_path)

        # Attempt to get a translator if allowed
        translator = None if no_translate else _get_translator_if_available()
        if translator is None and not no_translate:
            self.stdout.write(
                self.style.WARNING(
                    "DeepL translator not available or not configured. "
                    "Set DEEPL_API_KEY to enable EN translation."
                )
            )

        processed = 0
        created = 0
        updated = 0
        skipped = 0

        # Support two formats:
        #  - Django dumpdata format: {"model": "competitions.discipline", "pk": X, "fields": {...}}
        #  - Simplified format: direct discipline dictionaries with expected keys
        def extract_fields(item: Dict[str, Any]) -> Dict[str, Any]:
            if "fields" in item and isinstance(item["fields"], dict):
                return item["fields"]
            return item

        def find_existing_discipline(
            base_qs,
            name_value: Optional[str],
            name_fr_value: Optional[str],
            country_origin_value: Optional[str],
            description_fr_value: Optional[str],
        ):
            """Locate an existing Discipline robustly despite translations/duplicates.

            Matching strategy:
              1) Try exact case-insensitive match on name_fr (if provided and field exists)
              2) Else try exact case-insensitive match on name
              3) If multiple, narrow with country_origin
              4) If still multiple, narrow with description/description_fr
              5) Fallback to first by smallest id
            """
            qs = base_qs
            candidates = []

            # Step 1: match by name_fr when available on model and input
            if name_fr_value and hasattr(Discipline, "name_fr"):
                candidates = list(qs.filter(name_fr__iexact=name_fr_value))

            # Step 2: fallback to name when no candidates yet
            if not candidates and name_value:
                candidates = list(qs.filter(name__iexact=name_value))

            if len(candidates) <= 1:
                return candidates[0] if candidates else None

            # Step 3: narrow by country_origin
            if country_origin_value and hasattr(Discipline, "country_origin"):
                narrowed = [c for c in candidates if (c.country_origin or "").strip() == country_origin_value]
                if len(narrowed) == 1:
                    return narrowed[0]
                if len(narrowed) > 1:
                    candidates = narrowed

            # Step 4: narrow by description_fr/description
            def norm(s: Optional[str]) -> str:
                return " ".join((s or "").split())

            if description_fr_value:
                narrowed = []
                for c in candidates:
                    c_desc = getattr(c, "description_fr", None) or getattr(c, "description", None)
                    if norm(c_desc) == norm(description_fr_value):
                        narrowed.append(c)
                if len(narrowed) == 1:
                    return narrowed[0]
                if len(narrowed) > 1:
                    candidates = narrowed

            # Step 5: deterministic fallback
            return sorted(candidates, key=lambda x: x.id)[0]

        for item in data:
            fields = extract_fields(item)

            # Base identifiers
            name: Optional[str] = fields.get("name")
            if not name:
                skipped += 1
                continue

            name_fr: Optional[str] = fields.get("name_fr")
            name_en: Optional[str] = fields.get("name_en")

            # Descriptions (prefer FR-specific when available)
            description_fr: Optional[str] = fields.get("description_fr") or fields.get("description")
            description_en: Optional[str] = fields.get("description_en")

            # Normalize whitespace
            def normalize_text(text: Optional[str]) -> Optional[str]:
                if text is None:
                    return None
                trimmed = " ".join(str(text).split())
                return trimmed if trimmed else None

            name = normalize_text(name)
            name_fr = normalize_text(name_fr)
            name_en = normalize_text(name_en)
            description_fr = normalize_text(description_fr)
            description_en = normalize_text(description_en)

            # If EN description missing and translation is available, try to translate FR -> EN
            if not description_en and description_fr and translator and getattr(translator, "api_key", None):
                try:
                    translated_list = translator.translate_texts([description_fr], target_lang="EN", source_lang="FR")
                    if translated_list and translated_list[0]:
                        description_en = normalize_text(translated_list[0])
                except Exception as translate_exc:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Translation failed for '{name}': {translate_exc}. Will apply fallback policy."
                        )
                    )

            # If still missing EN and user requested FR->EN copy, copy FR text
            if not description_en and description_fr and copy_fr_to_en:
                description_en = description_fr

            # Prepare optional scalar fields
            country_origin: Optional[str] = normalize_text(fields.get("country_origin"))
            is_active = fields.get("is_active", True)
            try:
                minimum_age = int(fields.get("minimum_age", 0))
            except Exception:
                minimum_age = 0

            processed += 1
            if limit and processed > limit:
                break

            # Locate existing object robustly to avoid MultipleObjectsReturned with modeltranslation
            existing = find_existing_discipline(
                Discipline.objects.all(),
                name_value=name,
                name_fr_value=name_fr,
                country_origin_value=country_origin,
                description_fr_value=description_fr,
            )

            was_created = False
            if existing is None:
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] CREATE: {name}")
                    continue
                # Create new object with safe defaults
                obj = Discipline(
                    name=name_fr or name or "",
                    description=description_fr or "",
                )
                was_created = True
            else:
                obj = existing

            # Apply optional fields safely (work with/without modeltranslation)
            changed = False

            def set_if_attr(model_obj: Any, field_name: str, value: Any) -> None:
                nonlocal changed
                if value is None:
                    return
                if hasattr(model_obj, field_name):
                    if getattr(model_obj, field_name) != value:
                        setattr(model_obj, field_name, value)
                        changed = True

            # Localized names
            set_if_attr(obj, "name_fr", name_fr or name)
            set_if_attr(obj, "name_en", name_en)

            # Descriptions
            set_if_attr(obj, "description_fr", description_fr)
            set_if_attr(obj, "description_en", description_en)

            # Other simple fields
            set_if_attr(obj, "country_origin", country_origin)
            set_if_attr(obj, "is_active", bool(is_active))
            set_if_attr(obj, "minimum_age", minimum_age)

            if dry_run:
                status = "CREATE" if was_created else ("UPDATE" if changed else "UNCHANGED")
                self.stdout.write(f"[DRY-RUN] {status}: {name}")
                # No save in dry-run
                continue

            # Persist changes
            obj.save()
            if was_created:
                created += 1
            elif changed:
                updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Synced: {obj.name} (created={was_created}, updated={changed})"
                )
            )

        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("Summary"))
        self.stdout.write(self.style.HTTP_INFO(f"  processed: {processed}"))
        self.stdout.write(self.style.HTTP_INFO(f"  created:   {created}"))
        self.stdout.write(self.style.HTTP_INFO(f"  updated:   {updated}"))
        self.stdout.write(self.style.HTTP_INFO(f"  skipped:   {skipped}"))
