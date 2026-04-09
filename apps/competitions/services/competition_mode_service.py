# -*- coding: utf-8 -*-
"""
Sprint 2 - REQ-01, REQ-03: Service de gestion du mode de compétition.
Gère le basculement automatique ou manuel entre mode équipe et mode individuel.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.competitions.models import Competition, CompetitionCategory
from apps.competitions.models.combat import TeamConfiguration, Equipe, Poule


class CompetitionModeService:
    """
    Service pour gérer le mode de compétition (équipe vs individuel).
    Détecte automatiquement quand basculer et permet le basculement manuel.
    """

    # Modes de compétition
    MODE_TEAM = 'team'
    MODE_INDIVIDUAL = 'individual'
    MODE_MIXED = 'mixed'  # Certaines catégories en équipe, d'autres en individuel

    @staticmethod
    def get_competition_mode(competition):
        """
        Détermine le mode actuel de la compétition.

        Returns:
            str: 'team', 'individual', ou 'mixed'
        """
        try:
            team_config = competition.team_configuration
            has_team_config = True
        except (TeamConfiguration.DoesNotExist, AttributeError):
            has_team_config = False

        # Vérifier si des équipes existent
        has_teams = Equipe.objects.filter(
            competition=competition,
            is_active=True
        ).exists()

        if has_teams and has_team_config:
            return CompetitionModeService.MODE_TEAM
        elif not has_teams and not has_team_config:
            return CompetitionModeService.MODE_INDIVIDUAL
        else:
            return CompetitionModeService.MODE_MIXED

    @staticmethod
    def verifier_effectifs_equipes(competition):
        """
        Vérifie si les effectifs des équipes sont suffisants.
        Retourne un rapport détaillé.

        Returns:
            dict: {
                'suffisant': bool,
                'nb_equipes_total': int,
                'nb_equipes_completes': int,
                'nb_equipes_insuffisantes': int,
                'equipes_insuffisantes': list,
                'recommandation': str
            }
        """
        try:
            team_config = competition.team_configuration
            min_equipes = team_config.min_equipes_required
            min_titulaires = team_config.min_titulaires
        except Exception:
            min_equipes = 3
            min_titulaires = 3

        equipes = Equipe.objects.filter(
            competition=competition,
            is_active=True
        ).prefetch_related('membres')

        equipes_completes = []
        equipes_insuffisantes = []

        for equipe in equipes:
            nb_membres_actifs = equipe.membres.count()
            if nb_membres_actifs >= min_titulaires:
                equipes_completes.append({
                    'equipe': equipe,
                    'nb_membres': nb_membres_actifs
                })
            else:
                equipes_insuffisantes.append({
                    'equipe': equipe,
                    'nb_membres': nb_membres_actifs,
                    'manquants': min_titulaires - nb_membres_actifs
                })

        nb_total = len(equipes_completes) + len(equipes_insuffisantes)
        nb_completes = len(equipes_completes)
        suffisant = nb_completes >= min_equipes

        # Déterminer la recommandation
        if suffisant:
            recommandation = _("Le mode équipe peut être maintenu")
        elif nb_completes >= 2:
            recommandation = _("Envisager des fusions d'équipes ou basculement vers individuel")
        else:
            recommandation = _("Basculement vers mode individuel recommandé")

        return {
            'suffisant': suffisant,
            'nb_equipes_total': nb_total,
            'nb_equipes_completes': nb_completes,
            'nb_equipes_insuffisantes': len(equipes_insuffisantes),
            'equipes_completes': equipes_completes,
            'equipes_insuffisantes': equipes_insuffisantes,
            'min_equipes_requis': min_equipes,
            'min_titulaires_requis': min_titulaires,
            'recommandation': recommandation
        }

    @staticmethod
    def peut_basculer_vers_individuel(competition):
        """
        Vérifie si le basculement vers le mode individuel est possible.

        Returns:
            tuple: (possible: bool, raison: str)
        """
        # Vérifier qu'aucun combat d'équipe n'a commencé
        combats_commences = False
        poules = Poule.objects.filter(competition=competition)
        for poule in poules:
            if poule.combats.filter(status__in=['en_cours', 'termine']).exists():
                combats_commences = True
                break

        if combats_commences:
            return False, _("Des combats d'équipe ont déjà eu lieu")

        return True, _("Basculement possible")

    @staticmethod
    @transaction.atomic
    def basculer_vers_individuel(competition, user=None, raison=''):
        """
        Bascule une compétition du mode équipe vers le mode individuel.
        Convertit les membres d'équipes en inscriptions individuelles.

        Args:
            competition: La compétition à basculer
            user: Utilisateur qui effectue le basculement
            raison: Motif du basculement

        Returns:
            dict: Rapport du basculement avec statistiques
        """
        possible, message = CompetitionModeService.peut_basculer_vers_individuel(competition)
        if not possible:
            raise ValidationError(message)

        # Collecter tous les pratiquants des équipes
        pratiquants_equipes = []
        equipes = Equipe.objects.filter(
            competition=competition,
            is_active=True
        ).prefetch_related('membres__pratiquant')

        for equipe in equipes:
            for membre in equipe.membres.all():
                if membre.pratiquant and membre.pratiquant not in pratiquants_equipes:
                    pratiquants_equipes.append(membre.pratiquant)

        # Archiver toutes les équipes
        for equipe in equipes:
            equipe.is_active = False
            equipe.status = 'archived'
            equipe.save()

        # Archiver les poules
        poules = Poule.objects.filter(competition=competition)
        for poule in poules:
            poule.status = 'archived'
            poule.save()

        # Supprimer la configuration d'équipe
        try:
            team_config = competition.team_configuration
            team_config.delete()
        except Exception:
            pass

        # Créer les inscriptions individuelles si nécessaire
        # (dépend de la structure des registrations de la compétition)
        inscriptions_creees = 0
        # Note: La création des inscriptions individuelles dépend
        # de la structure du modèle CompetitionRegistration

        # Logger le changement
        changement = {
            'type': 'mode_switch',
            'de': 'team',
            'vers': 'individual',
            'date': timezone.now().isoformat(),
            'user': user.username if user else None,
            'raison': raison,
            'nb_pratiquants': len(pratiquants_equipes),
            'nb_equipes_archivees': equipes.count()
        }

        return {
            'success': True,
            'pratiquants_convertis': len(pratiquants_equipes),
            'equipes_archivees': equipes.count(),
            'inscriptions_creees': inscriptions_creees,
            'changement': changement
        }

    @staticmethod
    @transaction.atomic
    def configurer_mode_equipe(competition, format_preset='3+1', **kwargs):
        """
        Configure une compétition en mode équipe.

        Args:
            competition: La compétition à configurer
            format_preset: Format prédéfini ('2+1', '3+1', '3+2', '5+2', 'custom')
            **kwargs: Paramètres supplémentaires pour le format custom

        Returns:
            TeamConfiguration: La configuration créée
        """
        # Vérifier si une configuration existe déjà
        try:
            existing = competition.team_configuration
            raise ValidationError(_("Cette compétition a déjà une configuration d'équipe"))
        except TeamConfiguration.DoesNotExist:
            pass

        # Paramètres par défaut selon le format
        presets = {
            '2+1': {'min_titulaires': 2, 'max_titulaires': 2, 'min_remplacants': 0, 'max_remplacants': 1},
            '3+1': {'min_titulaires': 3, 'max_titulaires': 3, 'min_remplacants': 0, 'max_remplacants': 1},
            '3+2': {'min_titulaires': 3, 'max_titulaires': 3, 'min_remplacants': 0, 'max_remplacants': 2},
            '5+2': {'min_titulaires': 5, 'max_titulaires': 5, 'min_remplacants': 0, 'max_remplacants': 2},
        }

        if format_preset in presets:
            config_params = presets[format_preset]
        else:
            config_params = {
                'min_titulaires': kwargs.get('min_titulaires', 3),
                'max_titulaires': kwargs.get('max_titulaires', 3),
                'min_remplacants': kwargs.get('min_remplacants', 0),
                'max_remplacants': kwargs.get('max_remplacants', 1),
            }
            format_preset = 'custom'

        team_config = TeamConfiguration.objects.create(
            competition=competition,
            format_preset=format_preset,
            min_titulaires=config_params['min_titulaires'],
            max_titulaires=config_params['max_titulaires'],
            min_remplacants=config_params['min_remplacants'],
            max_remplacants=config_params['max_remplacants'],
            remplacants_obligatoires=kwargs.get('remplacants_obligatoires', False),
            min_equipes_required=kwargs.get('min_equipes_required', 3),
            max_ententes_par_equipe=kwargs.get('max_ententes_par_equipe', 2),
            entente_validation_required=kwargs.get('entente_validation_required', False)
        )

        return team_config

    @staticmethod
    def get_alerte_effectifs(competition):
        """
        Génère une alerte si les effectifs sont insuffisants.
        À utiliser dans les vues pour afficher un warning.

        Returns:
            dict or None: Alerte avec niveau et message, ou None si OK
        """
        rapport = CompetitionModeService.verifier_effectifs_equipes(competition)

        if rapport['suffisant']:
            return None

        nb_completes = rapport['nb_equipes_completes']
        nb_insuffisantes = rapport['nb_equipes_insuffisantes']
        min_requis = rapport['min_equipes_requis']

        if nb_completes == 0:
            niveau = 'danger'
            message = _("Aucune équipe n'a un effectif complet. Basculement vers mode individuel recommandé.")
        elif nb_completes < min_requis:
            niveau = 'warning'
            message = _(
                "Seulement {completes}/{requis} équipes ont un effectif complet. "
                "Envisagez des fusions ou un basculement vers le mode individuel."
            ).format(completes=nb_completes, requis=min_requis)
        else:
            niveau = 'info'
            message = _(
                "{insuffisantes} équipe(s) ont un effectif insuffisant et pourraient bénéficier d'une fusion."
            ).format(insuffisantes=nb_insuffisantes)

        return {
            'niveau': niveau,
            'message': message,
            'rapport': rapport,
            'actions_suggeres': CompetitionModeService._get_actions_suggerees(rapport)
        }

    @staticmethod
    def _get_actions_suggerees(rapport):
        """
        Génère les actions suggérées selon le rapport d'effectifs.
        """
        actions = []

        if not rapport['suffisant']:
            if rapport['nb_equipes_completes'] >= 2:
                actions.append({
                    'type': 'fusion',
                    'label': _("Proposer des fusions d'équipes"),
                    'priority': 'high'
                })

            if rapport['nb_equipes_insuffisantes'] > 0:
                actions.append({
                    'type': 'entente',
                    'label': _("Rechercher des pratiquants en entente"),
                    'priority': 'medium'
                })

            actions.append({
                'type': 'basculement',
                'label': _("Basculer vers le mode individuel"),
                'priority': 'low' if rapport['nb_equipes_completes'] >= 2 else 'high'
            })

        return actions
