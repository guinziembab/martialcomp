"""
Management command pour importer les tutoriels depuis MartialComp_Tutoriels.html
Usage: python manage.py import_tutorials
"""
import json
import os
import re
from html import unescape

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# Mapping emojis → FontAwesome
SECTION_ICONS = {
    1: 'fa-rocket',
    2: 'fa-home',
    3: 'fa-trophy',
    4: 'fa-edit',
    5: 'fa-fist-raised',
    6: 'fa-chart-bar',
    7: 'fa-medal',
    8: 'fa-khanda',
    9: 'fa-landmark',
    10: 'fa-coins',
    11: 'fa-calendar-alt',
    12: 'fa-users',
    13: 'fa-tasks',
    14: 'fa-shopping-cart',
    15: 'fa-bolt',
}

# Mapping audience badges
AUDIENCE_MAP = {
    'tous': 'all',
    'all': 'all',
    'responsable club': 'club',
    'club': 'club',
    'coach': 'coach',
    'administrateur': 'admin',
    'admin': 'admin',
    'responsable federation': 'federation',
    'federation': 'federation',
    'juge': 'judge',
    'juge/arbitre': 'judge',
    'arbitre': 'judge',
    'pratiquant': 'practitioner',
    'famille': 'practitioner',
    'parent/tuteur': 'practitioner',
}

FORMAT_MAP = {
    'video': 'video',
    'guide': 'guide',
    'guide pas a pas': 'guide',
    'interactif': 'interactive',
}


class Command(BaseCommand):
    help = 'Importe les tutoriels depuis docs/MartialComp_Tutoriels.html'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Supprimer tous les tutoriels existants avant import'
        )

    def handle(self, *args, **options):
        html_path = os.path.join(settings.BASE_DIR, 'docs', 'MartialComp_Tutoriels.html')
        if not os.path.exists(html_path):
            self.stderr.write(self.style.ERROR(f'Fichier non trouve: {html_path}'))
            return

        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        if options['clear']:
            Tutorial.objects.all().delete()
            TutorialSection.objects.all().delete()
            self.stdout.write(self.style.WARNING('Tous les tutoriels supprimes.'))

        sections_data = self.parse_sections(html)

        total_sections = 0
        total_tutorials = 0

        for sec_data in sections_data:
            section, created = TutorialSection.objects.get_or_create(
                order=sec_data['order'],
                defaults={
                    'title_fr': sec_data['title'],
                    'title': sec_data['title'],
                    'icon': sec_data['icon'],
                    'is_active': True,
                }
            )
            if not created:
                section.title_fr = sec_data['title']
                section.title = sec_data['title']
                section.icon = sec_data['icon']
                section.save()

            total_sections += 1

            for tut_data in sec_data['tutorials']:
                tutorial, created = Tutorial.objects.get_or_create(
                    section=section,
                    number=tut_data['number'],
                    defaults={
                        'title_fr': tut_data['title'],
                        'title': tut_data['title'],
                        'audience': tut_data['audience'],
                        'format': tut_data['format'],
                        'duration': tut_data['duration'],
                        'steps_fr': json.dumps(tut_data['steps'], ensure_ascii=False),
                        'steps': json.dumps(tut_data['steps'], ensure_ascii=False),
                        'tip_fr': tut_data['tip'],
                        'tip': tut_data['tip'],
                        'order': tut_data['number'],
                        'is_active': True,
                    }
                )
                if not created:
                    tutorial.title_fr = tut_data['title']
                    tutorial.title = tut_data['title']
                    tutorial.audience = tut_data['audience']
                    tutorial.format = tut_data['format']
                    tutorial.duration = tut_data['duration']
                    tutorial.steps_fr = json.dumps(tut_data['steps'], ensure_ascii=False)
                    tutorial.steps = json.dumps(tut_data['steps'], ensure_ascii=False)
                    tutorial.tip_fr = tut_data['tip']
                    tutorial.tip = tut_data['tip']
                    tutorial.save()

                total_tutorials += 1

        self.stdout.write(self.style.SUCCESS(
            f'Import termine: {total_sections} sections, {total_tutorials} tutoriels'
        ))

    def parse_sections(self, html):
        """Parse le HTML et extrait les sections et tutoriels"""
        sections = []

        # Split par sec-group
        sec_blocks = re.split(r'<section\s+class="sec-group"', html)

        for block in sec_blocks[1:]:  # Skip le premier (avant la premiere section)
            sec_data = self.parse_section_block(block)
            if sec_data:
                sections.append(sec_data)

        return sections

    def parse_section_block(self, block):
        """Parse un bloc de section"""
        # Titre de section: <h2 class="sec-title">1. Onboarding & Premiers Pas</h2>
        title_match = re.search(r'<h2\s+class="sec-title">\s*(\d+)\.\s*(.+?)\s*</h2>', block)
        if not title_match:
            return None

        sec_num = int(title_match.group(1))
        sec_title = self.clean_text(title_match.group(2))

        section = {
            'order': sec_num,
            'title': sec_title,
            'icon': SECTION_ICONS.get(sec_num, 'fa-book'),
            'tutorials': [],
        }

        # Parse les tutoriels dans cette section
        tut_blocks = re.split(r'<div\s+class="tut-card"', block)

        for tut_block in tut_blocks[1:]:
            tut_data = self.parse_tutorial_block(tut_block, sec_num)
            if tut_data:
                section['tutorials'].append(tut_data)

        return section

    def parse_tutorial_block(self, block, sec_num):
        """Parse un bloc de tutoriel"""
        # ID: <span class="tut-id" ...>1.1</span>
        id_match = re.search(r'class="tut-id"[^>]*>(\d+)\.(\d+)</span>', block)
        if not id_match:
            return None

        tut_number = int(id_match.group(2))

        # Titre: <h3 class="tut-title">...</h3>
        title_match = re.search(r'<h3\s+class="tut-title">\s*(.+?)\s*</h3>', block)
        title = self.clean_text(title_match.group(1)) if title_match else f'Tutoriel {sec_num}.{tut_number}'

        # Format badge
        format_match = re.search(r'class="tut-badge format">(\w+)', block)
        tut_format = 'guide'
        if format_match:
            raw = format_match.group(1).lower().strip()
            tut_format = FORMAT_MAP.get(raw, 'guide')

        # Duration badge
        duration_match = re.search(r'class="tut-badge duration">[^<]*?(\d+\s*min)', block)
        duration = duration_match.group(1) if duration_match else '3 min'

        # Audience badge
        audience_match = re.search(r'class="tut-badge audience">[^<]*?👤\s*(.+?)</span>', block)
        audience = 'all'
        if audience_match:
            raw = audience_match.group(1).lower().strip()
            audience = AUDIENCE_MAP.get(raw, 'all')

        # Steps
        steps = []
        step_pattern = re.finditer(
            r'<div\s+class="step-title">\s*(.+?)\s*</div>\s*'
            r'<div\s+class="step-desc">\s*(.+?)\s*</div>',
            block,
            re.DOTALL
        )
        for step_match in step_pattern:
            step_title = self.clean_text(step_match.group(1))
            step_desc = self.clean_text(step_match.group(2))
            steps.append(f"{step_title} : {step_desc}")

        # Tip
        tip_match = re.search(r'class="tut-tip"[^>]*>.*?Astuce\s*:?\s*</strong>\s*(.+?)\s*</div>', block, re.DOTALL)
        tip = self.clean_text(tip_match.group(1)) if tip_match else ''

        return {
            'number': tut_number,
            'title': title,
            'audience': audience,
            'format': tut_format,
            'duration': duration,
            'steps': steps,
            'tip': tip,
        }

    def clean_text(self, text):
        """Nettoie le texte HTML"""
        text = re.sub(r'<[^>]+>', '', text)
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
