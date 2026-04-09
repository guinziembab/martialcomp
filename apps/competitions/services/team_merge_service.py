# -*- coding: utf-8 -*-
"""
Sprint 2 - REQ-07: Service de gestion des fusions d'équipes.
Permet de fusionner deux équipes insuffisantes en une seule équipe.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.competitions.models.combat import TeamMerge, Equipe, MembreEquipe


class TeamMergeService:
    """
    Service pour gérer les fusions d'équipes.
    Permet de créer, approuver et exécuter des fusions.
    """

    @staticmethod
    def verifier_eligibilite_fusion(equipe_demandeur, equipe_cible):
        """
        Vérifie si une fusion est possible entre deux équipes.

        Returns:
            tuple: (eligible: bool, message: str)
        """
        # Vérifier que les équipes sont actives
        if not equipe_demandeur.is_active:
            return False, _("L'équipe demandeur n'est plus active")
        if not equipe_cible.is_active:
            return False, _("L'équipe cible n'est plus active")

        # Vérifier qu'elles sont dans la même compétition
        if equipe_demandeur.poule.competition != equipe_cible.poule.competition:
            return False, _("Les équipes doivent être dans la même compétition")

        # Vérifier qu'il n'y a pas déjà une fusion en cours
        fusion_existante = TeamMerge.objects.filter(
            equipe_demandeur__in=[equipe_demandeur, equipe_cible],
            equipe_cible__in=[equipe_demandeur, equipe_cible],
            status__in=['pending', 'approved']
        ).exists()
        if fusion_existante:
            return False, _("Une fusion est déjà en cours pour l'une de ces équipes")

        # Vérifier que les deux équipes sont du même club ou de clubs différents
        # selon les règles métier (ici on autorise les deux cas)

        # Vérifier la taille combinée des équipes
        try:
            competition = equipe_demandeur.poule.competition
            team_config = competition.team_configuration
            max_membres = team_config.max_titulaires + team_config.max_remplacants
        except Exception:
            max_membres = 5  # Valeur par défaut

        membres_total = (
            equipe_demandeur.membres.count() +
            equipe_cible.membres.count()
        )

        if membres_total > max_membres:
            return False, _(
                "L'équipe fusionnée aurait trop de membres ({total} > {max})"
            ).format(total=membres_total, max=max_membres)

        return True, _("Fusion autorisée")

    @staticmethod
    @transaction.atomic
    def creer_demande_fusion(equipe_demandeur, equipe_cible, demandeur,
                              raison='', nom_equipe_proposee=''):
        """
        Crée une demande de fusion entre deux équipes.

        Args:
            equipe_demandeur: Équipe qui initie la fusion
            equipe_cible: Équipe avec laquelle fusionner
            demandeur: Utilisateur qui fait la demande
            raison: Motif de la fusion
            nom_equipe_proposee: Nom suggéré pour l'équipe fusionnée

        Returns:
            TeamMerge: La demande de fusion créée
        """
        # Vérifier l'éligibilité
        eligible, message = TeamMergeService.verifier_eligibilite_fusion(
            equipe_demandeur, equipe_cible
        )
        if not eligible:
            raise ValidationError(message)

        competition = equipe_demandeur.competition

        # Générer un nom par défaut si non fourni
        if not nom_equipe_proposee:
            nom_equipe_proposee = f"{equipe_demandeur.nom} / {equipe_cible.nom}"

        fusion = TeamMerge.objects.create(
            competition=competition,
            equipe_demandeur=equipe_demandeur,
            equipe_cible=equipe_cible,
            demandeur=demandeur,
            raison=raison,
            nom_equipe_proposee=nom_equipe_proposee,
            status='pending'
        )

        return fusion

    @staticmethod
    @transaction.atomic
    def approuver_fusion(fusion, validateur, commentaire=''):
        """
        Approuve une demande de fusion (sans l'exécuter).
        """
        if fusion.status != 'pending':
            raise ValidationError(_("Cette demande n'est pas en attente"))

        fusion.status = 'approved'
        fusion.validateur = validateur
        fusion.date_validation = timezone.now()
        fusion.commentaire_validation = commentaire
        fusion.save()

        return fusion

    @staticmethod
    @transaction.atomic
    def refuser_fusion(fusion, validateur, commentaire=''):
        """
        Refuse une demande de fusion.
        """
        if fusion.status != 'pending':
            raise ValidationError(_("Cette demande n'est pas en attente"))

        fusion.status = 'rejected'
        fusion.validateur = validateur
        fusion.date_validation = timezone.now()
        fusion.commentaire_validation = commentaire
        fusion.save()

        return fusion

    @staticmethod
    @transaction.atomic
    def executer_fusion(fusion, nom_equipe_finale=None):
        """
        Exécute une fusion approuvée.
        Crée une nouvelle équipe et y transfère tous les membres.

        Args:
            fusion: La demande de fusion approuvée
            nom_equipe_finale: Nom final de l'équipe (optionnel)

        Returns:
            Equipe: L'équipe résultante de la fusion
        """
        if fusion.status != 'approved':
            raise ValidationError(_("La fusion doit être approuvée avant exécution"))

        equipe_demandeur = fusion.equipe_demandeur
        equipe_cible = fusion.equipe_cible

        # Nom de l'équipe résultante
        nom_final = nom_equipe_finale or fusion.nom_equipe_proposee

        # Créer la nouvelle équipe fusionnée
        equipe_fusionnee = Equipe.objects.create(
            nom=nom_final,
            competition=fusion.competition,
            club=equipe_demandeur.club,  # Le club du demandeur hérite
            is_fusion=True,
            status='active'
        )

        # Transférer les membres de l'équipe demandeur
        for membre in equipe_demandeur.membres.all():
            MembreEquipe.objects.create(
                equipe=equipe_fusionnee,
                pratiquant=membre.pratiquant,
                role=membre.role,
                is_entente=membre.is_entente,
                club_origine=membre.club_origine,
                equipe_avant_fusion=equipe_demandeur,
                a_combattu=membre.a_combattu
            )

        # Transférer les membres de l'équipe cible
        for membre in equipe_cible.membres.all():
            # Vérifier qu'il n'est pas déjà dans la nouvelle équipe
            if not equipe_fusionnee.membres.filter(pratiquant=membre.pratiquant).exists():
                MembreEquipe.objects.create(
                    equipe=equipe_fusionnee,
                    pratiquant=membre.pratiquant,
                    role=membre.role,
                    is_entente=membre.is_entente,
                    club_origine=membre.club_origine or equipe_cible.club,
                    equipe_avant_fusion=equipe_cible,
                    a_combattu=membre.a_combattu
                )

        # Archiver les anciennes équipes
        equipe_demandeur.archive(merged_into=equipe_fusionnee)
        equipe_cible.archive(merged_into=equipe_fusionnee)

        # Mettre à jour la fusion
        fusion.equipe_resultante = equipe_fusionnee
        fusion.status = 'completed'
        fusion.date_fusion = timezone.now()
        fusion.save()

        return equipe_fusionnee

    @staticmethod
    @transaction.atomic
    def annuler_fusion(fusion, raison=''):
        """
        Annule une demande de fusion (si pas encore exécutée).
        """
        if fusion.status == 'completed':
            raise ValidationError(_("Impossible d'annuler une fusion déjà exécutée"))

        fusion.status = 'cancelled'
        fusion.commentaire_validation = raison
        fusion.save()

        return fusion

    @staticmethod
    @transaction.atomic
    def defaire_fusion(fusion):
        """
        Défait une fusion déjà exécutée (rollback).
        Réactive les équipes d'origine et supprime l'équipe fusionnée.

        WARNING: Cette opération est dangereuse et ne devrait être utilisée
        que si aucun combat n'a eu lieu avec l'équipe fusionnée.
        """
        if fusion.status != 'completed':
            raise ValidationError(_("Cette fusion n'a pas été exécutée"))

        equipe_fusionnee = fusion.equipe_resultante
        equipe_demandeur = fusion.equipe_demandeur
        equipe_cible = fusion.equipe_cible

        # Vérifier qu'aucun combat n'a eu lieu
        combats_joues = equipe_fusionnee.combats_equipe1.filter(
            status__in=['en_cours', 'termine']
        ).exists() or equipe_fusionnee.combats_equipe2.filter(
            status__in=['en_cours', 'termine']
        ).exists()

        if combats_joues:
            raise ValidationError(
                _("Impossible de défaire la fusion: des combats ont déjà eu lieu")
            )

        # Réactiver les équipes d'origine
        equipe_demandeur.is_active = True
        equipe_demandeur.status = 'active'
        equipe_demandeur.merged_into = None
        equipe_demandeur.save()

        equipe_cible.is_active = True
        equipe_cible.status = 'active'
        equipe_cible.merged_into = None
        equipe_cible.save()

        # Supprimer les membres transférés
        equipe_fusionnee.membres.all().delete()

        # Supprimer l'équipe fusionnée
        equipe_fusionnee.delete()

        # Mettre à jour la fusion
        fusion.equipe_resultante = None
        fusion.status = 'cancelled'
        fusion.commentaire_validation = _("Fusion annulée (rollback)")
        fusion.date_fusion = None
        fusion.save()

        return fusion

    @staticmethod
    def get_fusions_competition(competition, status=None):
        """
        Récupère les demandes de fusion d'une compétition.
        """
        queryset = TeamMerge.objects.filter(competition=competition)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.select_related(
            'equipe_demandeur', 'equipe_cible', 'equipe_resultante',
            'demandeur', 'validateur'
        )

    @staticmethod
    def get_equipes_fusionnables(competition):
        """
        Retourne les équipes qui peuvent potentiellement fusionner.
        (Équipes avec effectif insuffisant)
        """
        try:
            team_config = competition.team_configuration
            min_membres = team_config.min_titulaires
        except Exception:
            min_membres = 3

        equipes = Equipe.objects.filter(
            competition=competition,
            is_active=True
        ).prefetch_related('membres')

        equipes_insuffisantes = []
        for equipe in equipes:
            nb_membres = equipe.membres.count()
            if nb_membres < min_membres:
                equipes_insuffisantes.append({
                    'equipe': equipe,
                    'nb_membres': nb_membres,
                    'manquants': min_membres - nb_membres
                })

        return equipes_insuffisantes
