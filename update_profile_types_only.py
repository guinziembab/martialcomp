#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour mettre à jour uniquement les types de profil dans le modèle CoachProfile
"""
import os

# Chemin du fichier modèle
coach_model_file = "competitions/models/coach_profile.py"

if not os.path.exists(coach_model_file):
    print(f"Le fichier {coach_model_file} n'existe pas.")
    exit(1)

# Lire le contenu du fichier
with open(coach_model_file, "r", encoding="utf-8") as f:
    coach_model_content = f.read()

# Créer une sauvegarde
with open(f"{coach_model_file}.bak2", "w", encoding="utf-8") as f:
    f.write(coach_model_content)

print(f"Sauvegarde créée dans {coach_model_file}.bak2")

# Rechercher et remplacer les types de profil
old_profile_types = """    PROFILE_TYPES = [
        ('traditional', _('Traditionaliste Éclectique')),
        ('innovative', _('Innovateur Synthétique')),
        ('researcher', _('Chercheur Perpétuel')),
        ('pragmatic', _('Expert Pragmatique')),
    ]"""

new_profile_types = """    PROFILE_TYPES = [
        ('traditional', _('Enseignant Traditionnel')),
        ('competitive', _('Entraîneur de Compétition')),
        ('wellness', _('Spécialiste Bien-être et Santé')),
        ('children', _('Spécialiste Pédagogie Enfants')),
        ('master', _('Maître / Expert Technique')),
        ('fitness', _('Coach Préparation Physique')),
        ('multidisciplinary', _('Expert Multi-disciplines')),
    ]"""

# Appliquer le remplacement
if old_profile_types in coach_model_content:
    modified_content = coach_model_content.replace(old_profile_types, new_profile_types)
    
    # Mettre à jour la longueur maximale du champ profile_type pour accommoder 'multidisciplinary'
    modified_content = modified_content.replace(
        "max_length=20,",
        "max_length=30,"
    )
    
    # Modifier le commentaire et la valeur par défaut pour le type de profil
    modified_content = modified_content.replace(
        'help_text=_("Approche pédagogique dominante du coach")',
        'help_text=_("Orientation principale de votre enseignement")'
    )
    
    # Améliorer la description du champ primary_teaching_place
    modified_content = modified_content.replace(
        'verbose_name=_("Lieu d\'enseignement principal")',
        'verbose_name=_("Club d\'enseignement principal")'
    )
    
    # Écrire le contenu modifié
    with open(coach_model_file, "w", encoding="utf-8") as f:
        f.write(modified_content)
    
    print("✓ Types de profil coach mis à jour dans le modèle")
    print("✓ Libellé 'Club d'enseignement principal' appliqué")
    print("✓ Modification de la description du type de profil")
    print("✓ Augmentation de la taille max pour le type de profil")
else:
    print("Les types de profil actuels ne correspondent pas au format attendu.")
    print("Vérifiez manuellement le fichier et adaptez le script.")

print("\nVeuillez redémarrer votre serveur Django pour voir les changements:")