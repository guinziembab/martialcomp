#!/usr/bin/env python
"""Analyser le rendu du formulaire PractitionerForm"""

import os
import sys
import django

# Configuration Django
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.competitions.forms.practitioners import PractitionerForm
from apps.competitions.models import Practitioner

User = get_user_model()

print("=== Analyse du rendu du formulaire PractitionerForm ===\n")

# Créer une requête
user = User.objects.get(username='bguinziemba')
factory = RequestFactory()
request = factory.get('/')
request.user = user

# Créer le formulaire
form = PractitionerForm(request=request)

print("1. Analyse du champ 'gender':")
gender_field = form.fields['gender']
print(f"   Type de champ: {type(gender_field).__name__}")
print(f"   Widget: {type(gender_field.widget).__name__}")
print(f"   Required: {gender_field.required}")
print(f"   Choices: {list(gender_field.choices)[:10]}")  # Limiter à 10 pour la lisibilité

print("\n2. HTML du champ gender:")
gender_html = str(form['gender'])
print(gender_html[:500])

print("\n3. Analyse des choix du modèle:")
print(f"   GENDER_CHOICES du modèle: {Practitioner.GENDER_CHOICES}")

print("\n4. Test de validation avec différentes valeurs:")
test_values = ['M', 'F', 'male', 'female', 'other', 'homme', 'femme']
for value in test_values:
    test_form = PractitionerForm(data={
        'first_name': 'Test',
        'last_name': 'Test',
        'birth_date': '2000-01-01',
        'gender': value
    }, request=request)
    
    # Valider uniquement le champ gender
    test_form.is_valid()
    if 'gender' in test_form.errors:
        print(f"   '{value}': ✗ Invalide - {test_form.errors['gender'][0]}")
    else:
        print(f"   '{value}': ✓ Valide")

print("\n5. Vérifier si le problème vient de la traduction:")
from django.utils.translation import activate, get_language
current_lang = get_language()
print(f"   Langue actuelle: {current_lang}")

# Tester avec différentes langues
for lang in ['fr', 'en']:
    activate(lang)
    form = PractitionerForm(request=request)
    gender_choices = list(form.fields['gender'].choices)[:5]
    print(f"\n   Choix en {lang}: {gender_choices}")

# Restaurer la langue
activate(current_lang)