"""
Script pour ajouter le champ is_migrated au modèle Club
"""
import os
import re

def add_is_migrated_field():
    file_path = "competitions/models/club.py"
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si le champ existe déjà
    if 'is_migrated' in content:
        print("Le champ is_migrated existe déjà")
        return
    
    # Trouver l'endroit où ajouter le champ (après is_active)
    pattern = r'(\s+is_active\s*=\s*models\.BooleanField\([^)]+\))'
    
    # Créer le nouveau champ
    new_field = '\n    \n    # Multi-tenant migration field\n    is_migrated = models.BooleanField(_("Migré vers multi-tenant"), default=False)\n    tenant = models.ForeignKey(\n        "multitenant.Tenant", \n        on_delete=models.SET_NULL, \n        null=True, \n        blank=True,\n        related_name="migrated_clubs", \n        verbose_name=_("Tenant associé")\n    )\n    migration_date = models.DateTimeField(_("Date de migration"), null=True, blank=True)'
    
    # Remplacer en ajoutant le nouveau champ après is_active
    replacement = r'\1' + new_field
    
    new_content = re.sub(pattern, replacement, content)
    
    # Écrire le fichier modifié
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Champs is_migrated, tenant et migration_date ajoutés au modèle Club")
    print("\nN'oubliez pas d'exécuter :")
    print("  python manage.py makemigrations")
    print("  python manage.py migrate")

if __name__ == "__main__":
    add_is_migrated_field()