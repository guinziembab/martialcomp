#!/usr/bin/env python
"""
Script pour refactoriser les modèles de l'application competitions
afin d'intégrer la nouvelle application organizations.

Ce script va parcourir tous les fichiers de modèles dans competitions/models/
et effectuer les transformations nécessaires.
"""

import os
import re
import sys
from pathlib import Path
import ast
import shutil  # Ajout du module shutil pour la copie de fichiers

# Vérifier si astunparse et astor sont nécessaires
try:
    import astunparse
    import astor
except ImportError:
    # Ces modules ne sont pas utilisés dans le code actuel
    pass

# Chemin vers le dossier des modèles
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / 'competitions' / 'models'

# Liste des fichiers à traiter
model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith('.py')]

# Modèles à remplacer et leurs correspondances
replacements = {
    'Federation': 'Organization',
    'Club': 'Organization',
}

# Relations à mettre à jour
relations = {
    'federation': 'organization',
    'club': 'organization',
    'clubs': 'organizations',
    'federations': 'organizations',
}

# Imports à ajouter
imports_to_add = "from organizations.models import Organization, OrganizationMember, OrganizationRole\n"


def process_model_file(filepath):
    """Traite un fichier de modèle pour remplacer les références."""
    print(f"Traitement du fichier: {filepath}")
    
    # Correction: utiliser with_name pour créer un chemin de backup
    backup_path = filepath.with_name(f"{filepath.name}.bak")
    
    # Créer une sauvegarde du fichier original - utiliser shutil au lieu de la commande cp
    # qui pourrait ne pas fonctionner sous Windows
    shutil.copy2(filepath, backup_path)
    
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 1. Remplacer les imports
    modified_content = content
    
    # Vérifier si l'import de organizations est déjà présent
    if 'from organizations.models import' not in modified_content:
        # Ajouter l'import après les autres imports
        import_pattern = r'(from django\..*?\n|import .*?\n)+'
        imports_match = re.search(import_pattern, modified_content)
        if imports_match:
            end_of_imports = imports_match.end()
            modified_content = modified_content[:end_of_imports] + "\n" + imports_to_add + modified_content[end_of_imports:]
        else:
            # Si aucun import n'est trouvé, ajouter au début du fichier
            modified_content = imports_to_add + modified_content
    
    # 2. Remplacer les classes et champs de modèle
    for old_model, new_model in replacements.items():
        # Remplacer les classes de modèle
        class_pattern = rf'class\s+{old_model}\s*\('
        modified_content = re.sub(class_pattern, f'class {old_model}(', modified_content)  # Conserver le nom de classe
        
        # Ajouter un commentaire de compatibilité si la classe existe
        if re.search(class_pattern, modified_content):
            compatibility_comment = f"\n    # Cette classe est maintenue pour la compatibilité, mais utilise désormais {new_model}\n"
            class_end = re.search(class_pattern, modified_content).end()
            modified_content = modified_content[:class_end] + compatibility_comment + modified_content[class_end:]
        
        # Remplacer les champs ForeignKey et relations
        fk_pattern = rf"models\.ForeignKey\(\s*['\"]?{old_model}['\"]?\s*,"
        new_fk = f"models.ForeignKey('organizations.{new_model}', "
        modified_content = re.sub(fk_pattern, new_fk, modified_content)
        
        # Remplacer les champs ManyToMany
        mtm_pattern = rf"models\.ManyToManyField\(\s*['\"]?{old_model}['\"]?\s*,"
        new_mtm = f"models.ManyToManyField('organizations.{new_model}', "
        modified_content = re.sub(mtm_pattern, new_mtm, modified_content)
    
    # 3. Mettre à jour les noms de relations
    for old_rel, new_rel in relations.items():
        # Mise à jour des related_name
        related_name_pattern = rf"related_name=['\"]({old_rel}_\w+|{old_rel}s)['\"]"
        modified_content = re.sub(related_name_pattern, f"related_name='{new_rel}s'", modified_content)
        
        # Mise à jour des noms de champs
        field_pattern = rf"{old_rel}\s*=\s*models\."
        modified_content = re.sub(field_pattern, f"{new_rel} = models.", modified_content)
        
        # Mise à jour des verbose_name
        verbose_name_pattern = rf"verbose_name=_\(['\"]({old_rel.title()}|{old_rel})['\"]"
        if old_rel == 'federation':
            modified_content = re.sub(verbose_name_pattern, f"verbose_name=_('Organisation')", modified_content)
        elif old_rel == 'club':
            modified_content = re.sub(verbose_name_pattern, f"verbose_name=_('Organisation')", modified_content)
    
    # 4. Ajouter des champs de transition si nécessaire
    for old_rel, new_rel in relations.items():
        # Chercher des modèles qui ont déjà un champ pour l'ancien modèle
        has_old_field_pattern = rf"{old_rel}\s*=\s*models\.ForeignKey"
        if re.search(has_old_field_pattern, modified_content):
            # Vérifier si le nouveau champ existe déjà
            has_new_field_pattern = rf"{new_rel}\s*=\s*models\.ForeignKey"
            if not re.search(has_new_field_pattern, modified_content):
                # Ajouter un nouveau champ de transition
                transition_field = f"""
    # Champ de transition pour la migration vers Organization
    {new_rel} = models.ForeignKey(
        'organizations.Organization', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='{new_rel}s_{old_rel}_transition',
        verbose_name=_('Organisation')
    )
"""
                # Trouver où insérer le champ (après le dernier champ du modèle)
                last_field_pattern = r'(\s+\w+\s*=\s*models\.[A-Za-z]+\([^\)]+\)[^\n]*\n)(?=\s*[^\s])'
                last_field_match = list(re.finditer(last_field_pattern, modified_content))
                if last_field_match:
                    last_field_pos = last_field_match[-1].end()
                    modified_content = modified_content[:last_field_pos] + transition_field + modified_content[last_field_pos:]
    
    # 5. Ajouter des méthodes de compatibilité
    for old_model, new_model in replacements.items():
        if old_model.lower() in content:
            # Si la classe existe, ajouter des méthodes de compatibilité
            compatibility_methods = f"""
    @property
    def as_organization(self):
        \"\"\"Retourne l'organisation correspondante.\"\"\"
        from organizations.models import Organization
        return Organization.objects.filter(old_{old_model.lower()}_id=self.id).first()
        
    def save(self, *args, **kwargs):
        \"\"\"Surcharge de save pour synchroniser avec Organization.\"\"\"
        super().save(*args, **kwargs)
        
        # Synchroniser avec Organization
        from organizations.models import Organization
        org, created = Organization.objects.get_or_create(
            old_{old_model.lower()}_id=self.id,
            defaults={{
                'name': self.name,
                'organization_type': '{old_model.lower()}',
                'description': getattr(self, 'description', ''),
                'email': getattr(self, 'contact_email', ''),
                'phone': getattr(self, 'contact_phone', ''),
                'website': getattr(self, 'website', ''),
                'address': getattr(self, 'address', ''),
                'city': getattr(self, 'city', ''),
                'is_active': getattr(self, 'is_active', True),
                'created_by': getattr(self, 'owner', None)
            }}
        )
        
        # Mettre à jour les champs modifiables
        if not created:
            org.name = self.name
            org.description = getattr(self, 'description', '')
            org.email = getattr(self, 'contact_email', '')
            org.phone = getattr(self, 'contact_phone', '')
            org.website = getattr(self, 'website', '')
            org.address = getattr(self, 'address', '')
            org.city = getattr(self, 'city', '')
            org.is_active = getattr(self, 'is_active', True)
            org.save()
"""
            # Trouver où insérer les méthodes (avant la fin de la classe)
            class_pattern = rf'class\s+{old_model}\s*\([^{{]+{{(.*?)}}(?=\s*\n)'
            class_match = re.search(class_pattern, modified_content, re.DOTALL)
            if class_match:
                class_content = class_match.group(1)
                class_end = class_match.start() + len(class_match.group(0)) - 1
                modified_content = modified_content[:class_end] + compatibility_methods + modified_content[class_end:]
    
    # 6. Écrire les modifications dans le fichier
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    
    print(f"Modifications enregistrées dans: {filepath}")
    print(f"Sauvegarde disponible dans: {backup_path}")


def create_migration_file():
    """Crée un fichier de migration pour synchroniser les données."""
    migrations_dir = BASE_DIR / 'competitions' / 'migrations'
    
    # Vérifier si le répertoire existe, sinon le créer
    if not migrations_dir.exists():
        print(f"Création du répertoire de migrations: {migrations_dir}")
        migrations_dir.mkdir(parents=True, exist_ok=True)
    
    # Déterminer le numéro de migration suivant
    existing_migrations = [f for f in os.listdir(migrations_dir) if f.endswith('.py') and f[0].isdigit()]
    if existing_migrations:
        last_number = max(int(f.split('_')[0]) for f in existing_migrations)
        next_number = last_number + 1
    else:
        next_number = 1
    
    # Créer le nom du fichier de migration
    migration_filename = f"{next_number:04d}_migrate_to_organizations.py"
    migration_path = migrations_dir / migration_filename
    
    # Contenu de la migration
    migration_content = """# Generated by refactor_models.py
from django.db import migrations
from django.utils import timezone


def forwards_func(apps, schema_editor):
    \"\"\"Migre les données des modèles Club et Federation vers Organization.\"\"\"
    Organization = apps.get_model('organizations', 'Organization')
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')
    
    # Migrer les clubs
    Club = apps.get_model('competitions', 'Club')
    for club in Club.objects.all():
        # Créer l'organisation
        org, created = Organization.objects.get_or_create(
            old_club_id=club.id,
            defaults={
                'name': club.name,
                'organization_type': 'club',
                'description': getattr(club, 'description', ''),
                'email': getattr(club, 'contact_email', ''),
                'phone': getattr(club, 'contact_phone', ''),
                'website': getattr(club, 'website', ''),
                'address': getattr(club, 'address', ''),
                'city': getattr(club, 'city', ''),
                'is_active': getattr(club, 'is_active', True),
                'created_by': getattr(club, 'owner', None)
            }
        )
        
        # Ajouter le propriétaire comme membre si défini
        if created and club.owner:
            OrganizationMember.objects.create(
                organization=org,
                user=club.owner,
                role='owner',
                title='Propriétaire',
                join_date=timezone.now().date(),
                can_manage_members=True,
                can_edit_organization=True,
                can_manage_competitions=True,
                is_active=True
            )
    
    # Migrer les fédérations
    Federation = apps.get_model('competitions', 'Federation')
    for federation in Federation.objects.all():
        # Créer l'organisation
        org, created = Organization.objects.get_or_create(
            old_federation_id=federation.id,
            defaults={
                'name': federation.name,
                'organization_type': 'national_federation',
                'description': getattr(federation, 'description', ''),
                'email': getattr(federation, 'contact_email', ''),
                'phone': getattr(federation, 'contact_phone', ''),
                'website': getattr(federation, 'website', ''),
                'address': getattr(federation, 'address', ''),
                'country': getattr(federation, 'country', ''),
                'city': getattr(federation, 'city', ''),
                'is_active': getattr(federation, 'is_active', True),
                'created_by': getattr(federation, 'owner', None)
            }
        )
        
        # Ajouter le propriétaire comme membre si défini
        if created and hasattr(federation, 'owner') and federation.owner:
            OrganizationMember.objects.create(
                organization=org,
                user=federation.owner,
                role='owner',
                title='Administrateur Fédéral',
                join_date=timezone.now().date(),
                can_manage_members=True,
                can_edit_organization=True,
                can_manage_competitions=True,
                is_active=True
            )
    
    # Mettre à jour les références de compétition
    Competition = apps.get_model('competitions', 'Competition')
    for competition in Competition.objects.all():
        if hasattr(competition, 'organizing_club_id') and competition.organizing_club_id:
            org = Organization.objects.filter(old_club_id=competition.organizing_club_id).first()
            if org and hasattr(competition, 'organizing_organization'):
                competition.organizing_organization = org
                competition.save(update_fields=['organizing_organization'])
        
        if hasattr(competition, 'federation_id') and competition.federation_id:
            org = Organization.objects.filter(old_federation_id=competition.federation_id).first()
            if org and hasattr(competition, 'sanctioning_organization'):
                competition.sanctioning_organization = org
                competition.save(update_fields=['sanctioning_organization'])


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0001_initial'),  # Remplacez par votre dernière migration
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
"""
    
    # Écrire le fichier de migration
    with open(migration_path, 'w', encoding='utf-8') as file:
        file.write(migration_content)
    
    print(f"Fichier de migration créé: {migration_path}")


def main():
    """Fonction principale qui exécute le script."""
    print(f"Analyse et correction des modèles dans: {MODELS_DIR}")
    print(f"Nombre de fichiers à traiter: {len(model_files)}")
    
    # Vérifier si le répertoire des modèles existe
    if not MODELS_DIR.exists():
        print(f"Erreur: Le répertoire {MODELS_DIR} n'existe pas.")
        return 1
    
    # Traiter chaque fichier
    for filename in model_files:
        filepath = MODELS_DIR / filename
        try:
            process_model_file(filepath)
        except Exception as e:
            print(f"Erreur lors du traitement du fichier {filepath}: {str(e)}")
    
    # Créer le fichier de migration
    try:
        create_migration_file()
    except Exception as e:
        print(f"Erreur lors de la création du fichier de migration: {str(e)}")
    
    print("\nRefactorisation terminée !")
    print("Étapes suivantes :")
    print("1. Vérifiez les modifications apportées aux modèles")
    print("2. Exécutez 'python manage.py makemigrations competitions' pour créer les migrations nécessaires")
    print("3. Exécutez 'python manage.py migrate' pour appliquer les migrations")
    print("4. Testez l'application pour vous assurer que tout fonctionne correctement")
    return 0


if __name__ == "__main__":
    sys.exit(main())