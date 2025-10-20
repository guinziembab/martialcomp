#!/usr/bin/env python3
"""
Ajoute les traductions restantes identifiées par l'utilisateur
"""

# Traductions manquantes identifiées
ADDITIONAL_TRANSLATIONS = {
    # Onglet Compétitions
    "Interface d'Organisation Professionnelle": "Professional Organization Interface",
    "Gérez vos compétitions et événements depuis l'interface dédiée aux organisateurs": "Manage your competitions and events from the dedicated organizer interface",
    "Aperçu Compétitions": "Competitions Overview",
    "Upcoming competitions": "Upcoming competitions",
    
    # Onglet Pratiquants
    "Customer management": "Customer management",
    "Aucun pratiquant": "No practitioners",
    "Commencez par ajouter vos premiers membres": "Start by adding your first members",
    "Statistiques membres": "Member statistics",
    "Actifs ce mois": "Active this month",
    "Nouveaux ce mois": "New this month",
    "Répartition par grade": "Distribution by grade",
    "Beginners": "Beginners",
    "Intermediaries": "Intermediaries",
    "Avancés": "Advanced",
    "Non défini": "Not defined",
}

import os

po_file = 'locale/en/LC_MESSAGES/django.po'

print(f"Vérification de {len(ADDITIONAL_TRANSLATIONS)} traductions...")
print()

# Vérifier lesquelles existent déjà
with open(po_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

to_add = {}
already_exists = []

for fr, en in ADDITIONAL_TRANSLATIONS.items():
    if f'msgid "{fr}"' not in content:
        to_add[fr] = en
    else:
        already_exists.append(fr)

print(f"✅ Déjà présentes: {len(already_exists)}")
for s in already_exists:
    print(f"   - {s}")

print()
print(f"➕ À ajouter: {len(to_add)}")
for fr in to_add.keys():
    print(f"   - {fr}")

if to_add:
    print()
    print(f"Ajout de {len(to_add)} traductions...")
    
    with open(po_file, 'a', encoding='utf-8') as f:
        f.write('\n# Dashboard Club - Traductions restantes\n')
        for fr, en in sorted(to_add.items()):
            f.write(f'\nmsgid "{fr}"\n')
            f.write(f'msgstr "{en}"\n')
    
    print(f"✅ {len(to_add)} traductions ajoutées!")
else:
    print()
    print("✅ Toutes les traductions existent déjà!")

print()
print("Compilation en cours...")
