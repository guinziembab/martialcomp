#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour modifier directement le template et remplacer primary_teaching_place par teaching_place
"""
import os

template_file = "competitions/templates/onboarding/coach/profile.html"

if not os.path.exists(template_file):
    print(f"Le fichier {template_file} n'existe pas.")
    exit(1)

# Lire le contenu du template
with open(template_file, "r", encoding="utf-8") as f:
    content = f.read()

# Sauvegarder l'original
with open(f"{template_file}.direct.bak", "w", encoding="utf-8") as f:
    f.write(content)
    
print(f"Sauvegarde du template original créée: {template_file}.direct.bak")

# Chercher le bloc contenant le champ primary_teaching_place
teaching_place_section = """                            <div class="col-md-6">
                                {{ profile_form.primary_teaching_place|as_crispy_field }}
                            </div>"""

# Remplacer par le nouveau champ teaching_place
new_section = """                            <div class="col-md-6">
                                {{ profile_form.teaching_place|as_crispy_field }}
                            </div>"""

# Appliquer le remplacement
if teaching_place_section in content:
    modified_content = content.replace(teaching_place_section, new_section)
    
    # Écrire le contenu modifié
    with open(template_file, "w", encoding="utf-8") as f:
        f.write(modified_content)
    
    print(f"✓ Template mis à jour avec succès: primary_teaching_place remplacé par teaching_place")
else:
    print("Le bloc contenant primary_teaching_place n'a pas été trouvé dans le template")
    print("Essai d'une méthode alternative...")
    
    # Essai d'une méthode alternative avec moins de contexte
    if "{{ profile_form.primary_teaching_place|as_crispy_field }}" in content:
        alt_modified = content.replace(
            "{{ profile_form.primary_teaching_place|as_crispy_field }}", 
            "{{ profile_form.teaching_place|as_crispy_field }}"
        )
        
        # Écrire le contenu modifié
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(alt_modified)
        
        print(f"✓ Template mis à jour avec la méthode alternative")
    else:
        print("Impossible de trouver primary_teaching_place dans le template")

print("\nModification du template terminée. Essayez de redémarrer votre serveur Django.")