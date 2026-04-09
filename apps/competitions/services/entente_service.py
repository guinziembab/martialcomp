# -*- coding: utf-8 -*-
"""
Sprint 2 - REQ-06: Service de gestion des ententes (prêt de joueurs).
Permet à un club de prêter un pratiquant à un autre club pour une compétition.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.competitions.models.combat import Entente, MembreEquipe, Equipe


class EntenteService:
    """
    Service pour gérer les ententes (prêt de joueurs entre clubs).
    """

    @staticmethod
    def verifier_eligibilite_entente(competition, pratiquant, club_origine, club_accueil):
        """
        Vérifie si une entente est possible pour ce pratiquant.

        Returns:
            tuple: (eligible: bool, message: str)
        """
        # Vérifier que le pratiquant appartient bien au club d'origine
        if pratiquant.club != club_origine:
            return False, _("Le pratiquant n'appartient pas au club d'origine spécifié")

        # Vérifier qu'il n'y a pas déjà une entente active pour ce pratiquant
        entente_existante = Entente.objects.filter(
            competition=competition,
            pratiquant=pratiquant,
            status__in=['pending', 'approved']
        ).exists()
        if entente_existante:
            return False, _("Ce pratiquant a déjà une entente en cours pour cette compétition")

        # Vérifier que le pratiquant n'est pas déjà inscrit avec son club d'origine
        deja_inscrit = MembreEquipe.objects.filter(
            equipe__competition=competition,
            pratiquant=pratiquant,
            equipe__club=club_origine,
            equipe__is_active=True
        ).exists()
        if deja_inscrit:
            return False, _("Ce pratiquant est déjà inscrit avec son club d'origine")

        # Vérifier la configuration des ententes de la compétition
        try:
            team_config = competition.team_configuration
            max_ententes = team_config.max_ententes_par_equipe
        except Exception:
            max_ententes = 2  # Valeur par défaut

        # Compter les ententes déjà approuvées pour le club d'accueil
        ententes_club_accueil = Entente.objects.filter(
            competition=competition,
            club_accueil=club_accueil,
            status='approved'
        ).count()

        if ententes_club_accueil >= max_ententes:
            return False, _("Le club d'accueil a atteint le maximum d'ententes autorisées ({max})").format(max=max_ententes)

        return True, _("Entente autorisée")

    @staticmethod
    @transaction.atomic
    def creer_demande_entente(competition, pratiquant, club_origine, club_accueil,
                               demandeur, equipe_accueil=None, role='titulaire', raison=''):
        """
        Crée une demande d'entente.

        Args:
            competition: La compétition concernée
            pratiquant: Le pratiquant à prêter
            club_origine: Club d'origine du pratiquant
            club_accueil: Club qui accueille le pratiquant
            demandeur: Utilisateur qui fait la demande
            equipe_accueil: Équipe d'accueil (optionnel)
            role: 'titulaire' ou 'remplacant'
            raison: Motif de l'entente

        Returns:
            Entente: L'entente créée

        Raises:
            ValidationError: Si l'entente n'est pas autorisée
        """
        # Vérifier l'éligibilité
        eligible, message = EntenteService.verifier_eligibilite_entente(
            competition, pratiquant, club_origine, club_accueil
        )
        if not eligible:
            raise ValidationError(message)

        # Déterminer le statut initial
        try:
            team_config = competition.team_configuration
            needs_validation = team_config.entente_validation_required
        except Exception:
            needs_validation = False

        # Créer l'entente
        entente = Entente.objects.create(
            competition=competition,
            pratiquant=pratiquant,
            club_origine=club_origine,
            club_accueil=club_accueil,
            equipe_accueil=equipe_accueil,
            demandeur=demandeur,
            role=role,
            raison=raison,
            status='pending' if needs_validation else 'approved',
            date_validation=None if needs_validation else timezone.now()
        )

        # Si pas de validation requise, intégrer directement le pratiquant
        if not needs_validation and equipe_accueil:
            EntenteService._integrer_membre_entente(entente)

        return entente

    @staticmethod
    @transaction.atomic
    def approuver_entente(entente, validateur, commentaire=''):
        """
        Approuve une demande d'entente.

        Args:
            entente: L'entente à approuver
            validateur: Utilisateur qui valide
            commentaire: Commentaire optionnel

        Returns:
            Entente: L'entente mise à jour
        """
        if entente.status != 'pending':
            raise ValidationError(_("Cette entente n'est pas en attente de validation"))

        entente.status = 'approved'
        entente.validateur = validateur
        entente.date_validation = timezone.now()
        entente.commentaire_validation = commentaire
        entente.save()

        # Intégrer le pratiquant dans l'équipe si spécifiée
        if entente.equipe_accueil:
            EntenteService._integrer_membre_entente(entente)

        return entente

    @staticmethod
    @transaction.atomic
    def refuser_entente(entente, validateur, commentaire=''):
        """
        Refuse une demande d'entente.
        """
        if entente.status != 'pending':
            raise ValidationError(_("Cette entente n'est pas en attente de validation"))

        entente.status = 'rejected'
        entente.validateur = validateur
        entente.date_validation = timezone.now()
        entente.commentaire_validation = commentaire
        entente.save()

        return entente

    @staticmethod
    @transaction.atomic
    def annuler_entente(entente, raison=''):
        """
        Annule une entente approuvée.
        Retire le pratiquant de l'équipe d'accueil.
        """
        if entente.status not in ['pending', 'approved']:
            raise ValidationError(_("Cette entente ne peut pas être annulée"))

        # Retirer le membre de l'équipe s'il y était
        if entente.equipe_accueil:
            MembreEquipe.objects.filter(
                equipe=entente.equipe_accueil,
                pratiquant=entente.pratiquant,
                is_entente=True
            ).delete()

        entente.status = 'cancelled'
        entente.commentaire_validation = raison
        entente.save()

        return entente

    @staticmethod
    def _integrer_membre_entente(entente):
        """
        Intègre le pratiquant en entente dans l'équipe d'accueil.
        """
        if not entente.equipe_accueil:
            return None

        # Vérifier si déjà membre
        membre_existant = MembreEquipe.objects.filter(
            equipe=entente.equipe_accueil,
            pratiquant=entente.pratiquant
        ).first()

        if membre_existant:
            membre_existant.is_entente = True
            membre_existant.club_origine = entente.club_origine
            membre_existant.role = entente.role
            membre_existant.save()
            return membre_existant

        # Créer le nouveau membre
        membre = MembreEquipe.objects.create(
            equipe=entente.equipe_accueil,
            pratiquant=entente.pratiquant,
            role=entente.role,
            is_entente=True,
            club_origine=entente.club_origine
        )
        return membre

    @staticmethod
    def assigner_equipe(entente, equipe):
        """
        Assigne une équipe d'accueil à une entente approuvée.
        """
        if entente.status != 'approved':
            raise ValidationError(_("L'entente doit être approuvée pour assigner une équipe"))

        if equipe.club != entente.club_accueil:
            raise ValidationError(_("L'équipe doit appartenir au club d'accueil"))

        entente.equipe_accueil = equipe
        entente.save()

        EntenteService._integrer_membre_entente(entente)

        return entente

    @staticmethod
    def get_ententes_competition(competition, status=None):
        """
        Récupère les ententes d'une compétition.

        Args:
            competition: La compétition
            status: Filtre optionnel sur le statut

        Returns:
            QuerySet: Les ententes filtrées
        """
        queryset = Entente.objects.filter(competition=competition)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.select_related(
            'pratiquant', 'club_origine', 'club_accueil',
            'equipe_accueil', 'demandeur', 'validateur'
        )

    @staticmethod
    def get_ententes_club(club, competition=None):
        """
        Récupère les ententes sortantes et entrantes d'un club.
        """
        ententes_sortantes = Entente.objects.filter(club_origine=club)
        ententes_entrantes = Entente.objects.filter(club_accueil=club)

        if competition:
            ententes_sortantes = ententes_sortantes.filter(competition=competition)
            ententes_entrantes = ententes_entrantes.filter(competition=competition)

        return {
            'sortantes': ententes_sortantes.select_related('pratiquant', 'club_accueil'),
            'entrantes': ententes_entrantes.select_related('pratiquant', 'club_origine')
        }
