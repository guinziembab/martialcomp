"""
Override d'urgence pour désinscrire Practitioner de l'admin Django
Ce fichier est chargé après l'enregistrement des apps pour éviter l'erreur Discipline
"""

def unregister_practitioner():
    """Désinscrit le modèle Practitioner de l'admin Django"""
    try:
        from django.contrib import admin
        from apps.competitions.models import Practitioner
        
        if Practitioner in admin.site._registry:
            admin.site.unregister(Practitioner)
            print("✅ Practitioner désinscrit de l'admin Django")
        else:
            print("ℹ️ Practitioner déjà désinscrit de l'admin Django")
            
    except Exception as e:
        print(f"⚠️ Impossible de désinscrire Practitioner: {e}")

# Exécuter automatiquement lors de l'import
unregister_practitioner()