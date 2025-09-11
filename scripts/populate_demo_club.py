import os
import django

# Détection automatique du module settings
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.conf import settings

django.setup()

from django.contrib.auth import get_user_model
from competitions.models import Club, Practitioner, Event
from grades.models import Grade
from shop.models import Product
from finances.models import Transaction
from django.core.files import File
from competitions.models.discipline import Discipline
import datetime
from organizations.models import Organization

User = get_user_model()

# 1. Créer l'utilisateur démo
user, created = User.objects.get_or_create(
    username='demo_club',
    defaults={
        'email': 'demo_club@martialcomp.com',
        'is_active': True,
        'first_name': 'Démo',
        'last_name': 'Club',
    }
)
if created:
    user.set_password('demo1234')
    user.save()

# Créer ou récupérer l'organisation démo
org, _ = Organization.objects.get_or_create(name='Organisation Démo MartialComp')

# 2. Créer le club démo (optionnellement lié à l'organisation)
club, _ = Club.objects.get_or_create(
    name='Club Démo MartialComp',
    defaults={'owner': user, 'organization': org}
)

# Créer ou récupérer la discipline Karaté
karate, _ = Discipline.objects.get_or_create(name='Karaté')

# 3. Créer 5 membres avec grades différents
grades = ['Blanche', 'Jaune', 'Verte', 'Bleue', 'Noire']
genders = ['male', 'female', 'other', 'male', 'female']
practitioners = []
for i, grade_name in enumerate(grades):
    grade, _ = Grade.objects.get_or_create(name=grade_name, discipline=karate)
    p, _ = Practitioner.objects.get_or_create(
        first_name=f'Membre{i+1}',
        last_name=f'Démo',
        organization=org,
        birth_date=datetime.date(2000+i, 1, 1),
        gender=genders[i],
        defaults={'grade': grade, 'is_active': True, 'status': 'active'}
    )
    practitioners.append(p)

# 4. Créer quelques transactions
Transaction.objects.get_or_create(
    club=club,
    amount=50,
    type='cotisation',
    description='Cotisation annuelle Membre1',
)
Transaction.objects.get_or_create(
    club=club,
    amount=120,
    type='achat',
    description='Achat kimono',
)

# 5. Créer quelques produits (équipements) avec visuel
for prod_name, img in [('Kimono', 'kimono.png'), ('Ceinture noire', 'belt_black.png')]:
    prod, _ = Product.objects.get_or_create(
        name=prod_name,
        defaults={'description': f'Produit démo {prod_name}', 'price': 50}
    )
    # Ajout d'une image fictive si le champ existe
    if hasattr(prod, 'image'):
        from django.core.files.base import ContentFile
        prod.image.save(img, ContentFile(b'fakeimage'), save=True)

# 6. Créer 2-3 événements
for i in range(1, 4):
    Event.objects.get_or_create(
        club=club,
        name=f'Evénement Démo {i}',
        description='Evénement de démonstration',
    )

print('Compte démo et données créés !') 