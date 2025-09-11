#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Solution définitive pour permettre la saisie libre du club d'enseignement
"""
import os

# Créer un nouveau champ CharField dans le modèle
model_file = "competitions/models/coach_profile.py"

if not os.path.exists(model_file):
    print(f"Le fichier {model_file} n'existe pas.")
    exit(1)

# Lire le contenu du modèle
with open(model_file, "r", encoding="utf-8") as f:
    model_content = f.read()

# Créer une sauvegarde
with open(f"{model_file}.final.bak", "w", encoding="utf-8") as f:
    f.write(model_content)

print(f"Sauvegarde créée dans {model_file}.final.bak")

# Remplacer le champ ForeignKey par un CharField libre
old_field = """    primary_teaching_place = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_coaches',
        verbose_name=_("Club d'enseignement principal")
    )"""

new_field = """    primary_teaching_place = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_coaches',
        verbose_name=_("Club enregistré (interne)")
    )
    
    # Champ texte libre pour la saisie du lieu d'enseignement
    club_name = models.CharField(
        _("Lieu d'enseignement"),
        max_length=200,
        blank=True,
        help_text=_("Nom de votre club, dojo ou lieu d'enseignement")
    )"""

# Mettre à jour le modèle
if old_field in model_content:
    modified_model = model_content.replace(old_field, new_field)
    
    # Écrire le contenu modifié
    with open(model_file, "w", encoding="utf-8") as f:
        f.write(modified_model)
    
    print("✓ Modèle mis à jour avec le champ club_name")
else:
    print("Champ primary_teaching_place non trouvé dans le format attendu")

# Mettre à jour le template
template_file = "competitions/templates/onboarding/coach/profile.html"

if not os.path.exists(template_file):
    print(f"Le fichier {template_file} n'existe pas.")
    exit(1)

# Lire le contenu du template
with open(template_file, "r", encoding="utf-8") as f:
    template_content = f.read()

# Créer une sauvegarde
with open(f"{template_file}.final.bak", "w", encoding="utf-8") as f:
    f.write(template_content)

print(f"Sauvegarde créée dans {template_file}.final.bak")

# Remplacer le champ primary_teaching_place par club_name
if "profile_form.primary_teaching_place|as_crispy_field" in template_content:
    modified_template = template_content.replace(
        "profile_form.primary_teaching_place|as_crispy_field",
        "profile_form.club_name|as_crispy_field"
    )
    
    # Écrire le contenu modifié
    with open(template_file, "w", encoding="utf-8") as f:
        f.write(modified_template)
    
    print("✓ Template mis à jour pour utiliser club_name")
else:
    print("Référence à primary_teaching_place non trouvée dans le template")

# Mettre à jour le formulaire pour inclure le champ club_name
forms_file = "competitions/forms/onboarding.py"

if not os.path.exists(forms_file):
    print(f"Le fichier {forms_file} n'existe pas.")
    exit(1)

# Lire le contenu du formulaire
with open(forms_file, "r", encoding="utf-8") as f:
    forms_content = f.read()

# Créer une sauvegarde
with open(f"{forms_file}.final.bak", "w", encoding="utf-8") as f:
    f.write(forms_content)

print(f"Sauvegarde créée dans {forms_file}.final.bak")

# Remplacer primary_teaching_place par club_name dans le formulaire
if "'primary_teaching_place'" in forms_content or '"primary_teaching_place"' in forms_content:
    modified_forms = forms_content.replace(
        "'primary_teaching_place'",
        "'club_name'"
    ).replace(
        '"primary_teaching_place"',
        '"club_name"'
    )
    
    # Écrire le contenu modifié
    with open(forms_file, "w", encoding="utf-8") as f:
        f.write(modified_forms)
    
    print("✓ Formulaire mis à jour pour utiliser club_name")
else:
    print("Référence à primary_teaching_place non trouvée dans le formulaire")

# Créer une migration pour le nouveau champ
migrations_dir = "competitions/migrations"
os.makedirs(migrations_dir, exist_ok=True)

# Trouver le numéro de la prochaine migration
import glob
migration_files = glob.glob(f"{migrations_dir}/[0-9]*.py")
migration_numbers = [int(os.path.basename(f).split('_')[0]) for f in migration_files]
next_number = max(migration_numbers) + 1 if migration_numbers else 1

# Trouver la dernière migration
last_migration = None
if migration_numbers:
    last_number = max(migration_numbers)
    for f in migration_files:
        if os.path.basename(f).startswith(f"{last_number:04d}_"):
            last_migration = os.path.basename(f).replace('.py', '')
            break

if not last_migration:
    last_migration = "0001_initial"

print(f"Dernière migration: {last_migration}")

# Créer la migration
migration_file = f"{migrations_dir}/{next_number:04d}_add_club_name_field.py"
migration_content = f"""# Generated manually
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '{last_migration}'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachprofile',
            name='club_name',
            field=models.CharField(
                blank=True,
                default='',
                help_text="Nom de votre club, dojo ou lieu d'enseignement",
                max_length=200,
                verbose_name="Lieu d'enseignement"
            ),
        ),
        migrations.AlterField(
            model_name='coachprofile',
            name='primary_teaching_place',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='primary_coaches',
                to='competitions.club',
                verbose_name='Club enregistré (interne)'
            ),
        ),
    ]
"""

with open(migration_file, "w", encoding="utf-8") as f:
    f.write(migration_content)

print(f"✓ Migration créée: {migration_file}")

# Créer un script SQL pour ajouter directement la colonne
sql_file = "add_club_name.sql"
sql_content = """-- Script SQL pour ajouter la colonne club_name
ALTER TABLE competitions_coachprofile ADD COLUMN club_name VARCHAR(200) DEFAULT '';
"""

with open(sql_file, "w", encoding="utf-8") as f:
    f.write(sql_content)

print(f"✓ Script SQL créé: {sql_file}")

print("\nTous les fichiers ont été mis à jour pour utiliser le champ club_name.")
print("Veuillez exécuter la commande:")
print("python manage.py migrate")
print("\nPuis redémarrez votre serveur Django.")