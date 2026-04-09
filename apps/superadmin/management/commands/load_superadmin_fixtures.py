# -*- coding: utf-8 -*-
"""
Commande de management pour charger les fixtures Super Admin.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction

from apps.superadmin.models import MembershipProfile, ServiceStatus


class Command(BaseCommand):
    """Charge les données initiales pour l'application Super Admin."""

    help = 'Charge les profils de membership initiaux et les statuts de services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force le rechargement même si des données existent déjà',
        )

    def handle(self, *args, **options):
        force = options['force']

        self.stdout.write(self.style.NOTICE('Chargement des fixtures Super Admin...'))

        # Vérifier si des données existent déjà
        profiles_exist = MembershipProfile.objects.filter(is_global=True).exists()
        services_exist = ServiceStatus.objects.exists()

        if profiles_exist and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Des profils globaux existent déjà. '
                    'Utilisez --force pour recharger.'
                )
            )
        else:
            if force and profiles_exist:
                self.stdout.write('Suppression des profils globaux existants...')
                MembershipProfile.objects.filter(is_global=True).delete()

            self._load_profiles()

        if services_exist and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Des statuts de services existent déjà. '
                    'Utilisez --force pour recharger.'
                )
            )
        else:
            if force and services_exist:
                self.stdout.write('Suppression des statuts de services existants...')
                ServiceStatus.objects.all().delete()

            self._load_services()

        self.stdout.write(self.style.SUCCESS('Fixtures Super Admin chargées avec succès!'))

    @transaction.atomic
    def _load_profiles(self):
        """Charge les profils de membership."""
        self.stdout.write('Création des profils de membership globaux...')

        profiles_data = [
            {
                'name': 'Dojo Essentials',
                'slug': 'dojo-essentials',
                'description': 'Profil de base pour les clubs débutants.',
                'profile_type': 'subscription',
                'validity_type': 'duration',
                'validity_duration': 365,
                'is_global': True,
                'pricing_model': 'per_member',
                'price': '2.99',
                'max_participants': 50,
                'feature_overrides': {
                    'competition_creation': False,
                    'advanced_scoring': False,
                    'basic_registration': True,
                    'results_display': True,
                },
            },
            {
                'name': "Master's Circle",
                'slug': 'masters-circle',
                'description': 'Profil intermédiaire pour les clubs établis.',
                'profile_type': 'subscription',
                'validity_type': 'duration',
                'validity_duration': 365,
                'is_global': True,
                'pricing_model': 'per_member',
                'price': '5.99',
                'max_participants': 200,
                'feature_overrides': {
                    'competition_creation': True,
                    'advanced_scoring': True,
                    'basic_registration': True,
                    'results_display': True,
                    'export_data': True,
                },
            },
            {
                'name': 'Grand Champion Suite',
                'slug': 'grand-champion-suite',
                'description': 'Profil premium pour les grandes fédérations.',
                'profile_type': 'subscription',
                'validity_type': 'duration',
                'validity_duration': 365,
                'is_global': True,
                'pricing_model': 'per_member',
                'price': '9.99',
                'max_participants': 0,
                'feature_overrides': {
                    'competition_creation': True,
                    'advanced_scoring': True,
                    'real_time_combat': True,
                    'api_access': True,
                    'white_label': True,
                },
            },
            {
                'name': 'Pack Compétition Standard',
                'slug': 'pack-competition-standard',
                'description': 'Accès complet à une compétition pour participants externes.',
                'profile_type': 'event',
                'validity_type': 'event_bound',
                'is_global': True,
                'pricing_model': 'per_member',
                'price': '15.00',
                'feature_overrides': {
                    'basic_registration': True,
                    'results_display': True,
                    'qr_code_access': True,
                },
            },
            {
                'name': 'Participant Externe',
                'slug': 'participant-externe',
                'description': 'Accès basique pour participants externes.',
                'profile_type': 'event',
                'validity_type': 'event_bound',
                'is_global': True,
                'pricing_model': 'per_member',
                'price': '10.00',
                'feature_overrides': {
                    'basic_registration': True,
                    'results_display': True,
                },
            },
            {
                'name': 'Délégation Invitée',
                'slug': 'delegation-invitee',
                'description': 'Accès gratuit pour délégations invitées.',
                'profile_type': 'event',
                'validity_type': 'event_bound',
                'is_global': True,
                'pricing_model': 'free',
                'price': '0.00',
                'requires_approval': True,
                'feature_overrides': {
                    'basic_registration': True,
                    'results_display': True,
                },
            },
        ]

        for data in profiles_data:
            profile, created = MembershipProfile.objects.get_or_create(
                slug=data['slug'],
                defaults=data
            )
            status = 'créé' if created else 'existant'
            self.stdout.write(f'  - {profile.name}: {status}')

    @transaction.atomic
    def _load_services(self):
        """Charge les statuts de services."""
        self.stdout.write('Création des statuts de services...')

        services = ['web', 'database', 'redis', 'celery', 'celery_beat', 'nginx']

        for service_name in services:
            service, created = ServiceStatus.objects.get_or_create(
                service_name=service_name,
                defaults={'status': 'unknown'}
            )
            status = 'créé' if created else 'existant'
            self.stdout.write(f'  - {service.get_service_name_display()}: {status}')
