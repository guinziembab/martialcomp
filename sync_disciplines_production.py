#!/usr/bin/env python3
"""
Script de synchronisation des disciplines de développement vers la production
Aligne les données de disciplines entre l'environnement de développement et la production
"""

import os
import sys
import json
from datetime import datetime

# Configuration pour la production
PRODUCTION_PATH = "/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH = "/var/www/vhosts/martialcomp.com/apps/martialcomp/venv"

def setup_django():
    """Configure Django pour la production"""
    sys.path.insert(0, PRODUCTION_PATH)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    
    import django
    django.setup()
    
    from apps.competitions.models import Discipline
    return Discipline

def load_dev_disciplines():
    """Charge les disciplines depuis le fichier de développement"""
    dev_file = "disciplines_dev.clean.json"
    
    if not os.path.exists(dev_file):
        print(f"❌ Fichier {dev_file} non trouvé")
        return None
    
    with open(dev_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filtrer les disciplines principales (exclure les tests)
    disciplines = []
    for item in data:
        if item['model'] == 'competitions.discipline':
            fields = item['fields']
            # Exclure les disciplines de test
            if not fields['name'].startswith('Karaté Technique Test'):
                disciplines.append(fields)
    
    return disciplines

def sync_disciplines():
    """Synchronise les disciplines"""
    print("🔄 SYNCHRONISATION DES DISCIPLINES")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configuration Django
    Discipline = setup_django()
    
    # Charger les données de développement
    print("1️⃣ Chargement des données de développement...")
    dev_disciplines = load_dev_disciplines()
    
    if not dev_disciplines:
        print("❌ Impossible de charger les données de développement")
        return False
    
    print(f"✅ {len(dev_disciplines)} disciplines chargées depuis le développement")
    print()
    
    # Analyser l'état actuel de la production
    print("2️⃣ Analyse de l'état actuel de la production...")
    prod_disciplines = Discipline.objects.all()
    prod_names = {d.name for d in prod_disciplines}
    
    print(f"📊 Production actuelle: {prod_disciplines.count()} disciplines")
    for discipline in prod_disciplines:
        print(f"   - {discipline.name}")
    print()
    
    # Identifier les disciplines à ajouter/mettre à jour
    print("3️⃣ Identification des modifications...")
    
    to_add = []
    to_update = []
    to_keep = []
    
    for dev_disc in dev_disciplines:
        name = dev_disc['name']
        
        if name in prod_names:
            # Vérifier si mise à jour nécessaire
            try:
                existing = Discipline.objects.get(name=name)
                if (existing.description != dev_disc['description'] or 
                    existing.country_origin != dev_disc['country_origin']):
                    to_update.append((existing, dev_disc))
                else:
                    to_keep.append(name)
            except Discipline.DoesNotExist:
                to_add.append(dev_disc)
        else:
            to_add.append(dev_disc)
    
    print(f"✅ À ajouter: {len(to_add)} disciplines")
    print(f"✅ À mettre à jour: {len(to_update)} disciplines")
    print(f"✅ À conserver: {len(to_keep)} disciplines")
    print()
    
    # Afficher les détails
    if to_add:
        print("📝 Nouvelles disciplines à ajouter:")
        for disc in to_add:
            print(f"   + {disc['name']} ({disc['country_origin']})")
        print()
    
    if to_update:
        print("🔄 Disciplines à mettre à jour:")
        for existing, dev_disc in to_update:
            print(f"   ~ {dev_disc['name']}")
        print()
    
    # Demander confirmation
    print("⚠️  ATTENTION: Cette opération va modifier la base de données de production!")
    print("Voulez-vous continuer? (y/N): ", end="")
    
    try:
        response = input().strip().lower()
        if response not in ['y', 'yes', 'oui']:
            print("❌ Opération annulée par l'utilisateur")
            return False
    except KeyboardInterrupt:
        print("\n❌ Opération annulée par l'utilisateur")
        return False
    
    # Exécuter les modifications
    print()
    print("4️⃣ Exécution des modifications...")
    
    # Ajouter les nouvelles disciplines
    added_count = 0
    for disc in to_add:
        try:
            Discipline.objects.create(
                name=disc['name'],
                description=disc['description'],
                country_origin=disc['country_origin'],
                is_active=disc['is_active'],
                minimum_age=disc.get('minimum_age', 0)
            )
            print(f"   ✅ Ajouté: {disc['name']}")
            added_count += 1
        except Exception as e:
            print(f"   ❌ Erreur ajout {disc['name']}: {e}")
    
    # Mettre à jour les disciplines existantes
    updated_count = 0
    for existing, dev_disc in to_update:
        try:
            existing.description = dev_disc['description']
            existing.country_origin = dev_disc['country_origin']
            existing.is_active = dev_disc['is_active']
            existing.minimum_age = dev_disc.get('minimum_age', 0)
            existing.save()
            print(f"   ✅ Mis à jour: {dev_disc['name']}")
            updated_count += 1
        except Exception as e:
            print(f"   ❌ Erreur mise à jour {dev_disc['name']}: {e}")
    
    print()
    print("5️⃣ Résumé de la synchronisation...")
    print(f"✅ Disciplines ajoutées: {added_count}")
    print(f"✅ Disciplines mises à jour: {updated_count}")
    print(f"✅ Disciplines conservées: {len(to_keep)}")
    
    # Vérification finale
    final_count = Discipline.objects.count()
    print(f"📊 Total final en production: {final_count} disciplines")
    
    print()
    print("🎉 Synchronisation terminée avec succès!")
    return True

def main():
    """Fonction principale"""
    try:
        success = sync_disciplines()
        if success:
            print("\n✅ La production est maintenant alignée avec le développement")
        else:
            print("\n❌ La synchronisation a échoué")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors de la synchronisation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()