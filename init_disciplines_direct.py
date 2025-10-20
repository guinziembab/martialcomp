#!/usr/bin/env python
"""
Script direct pour initialiser les disciplines
Sans passer par Django management command
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Ignorer l'erreur de channels pour l'instant
try:
    # Temporairement retirer channels de INSTALLED_APPS s'il cause problème
    from django.conf import settings
    if 'channels' in settings.INSTALLED_APPS:
        apps_list = list(settings.INSTALLED_APPS)
        apps_list.remove('channels')
        settings.INSTALLED_APPS = apps_list
except:
    pass

try:
    django.setup()
    print("✅ Django configuré")
except Exception as e:
    print(f"Configuration Django: {e}")
    print("Tentative avec configuration minimale...")
    
    # Configuration minimale
    from django.conf import settings
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'apps.competitions',
            'apps.organizations',
        ],
        SECRET_KEY='temporary-secret-key',
        USE_TZ=True,
    )
    django.setup()

# Importer après setup
from django.db import transaction
from apps.competitions.models import Discipline

def init_disciplines():
    """Initialiser les disciplines par défaut"""
    default_disciplines = [
        'Karaté', 'Judo', 'Taekwondo', 'Ju-Jitsu', 'Aïkido',
        'Kung Fu', 'Muay Thai', 'Krav Maga', 'Capoeira', 'MMA',
        'Boxe', 'Kickboxing', 'Sambo', 'Hapkido', 'Kendo'
    ]
    
    created = 0
    existing = 0
    
    try:
        with transaction.atomic():
            for name in default_disciplines:
                discipline, was_created = Discipline.objects.get_or_create(
                    name=name,
                    defaults={'is_active': True}
                )
                if was_created:
                    created += 1
                    print(f'✅ Created: {name}')
                else:
                    existing += 1
                    # Ensure existing disciplines are active
                    if not discipline.is_active:
                        discipline.is_active = True
                        discipline.save()
                        print(f'⚠️  Activated existing discipline: {name}')
        
        print(f'\n📊 Summary: {created} created, {existing} existing, {created + existing} total active disciplines')
        return True
        
    except Exception as e:
        print(f'❌ Error initializing disciplines: {e}')
        return False


if __name__ == '__main__':
    print("🥋 Initialisation des disciplines MartialComp")
    print("-" * 50)
    
    success = init_disciplines()
    
    if success:
        print("\n✅ Disciplines initialisées avec succès!")
        
        # Afficher toutes les disciplines actives
        print("\n📋 Disciplines actives:")
        try:
            for disc in Discipline.objects.filter(is_active=True):
                print(f"   - {disc.name}")
        except:
            pass
    else:
        print("\n❌ Échec de l'initialisation des disciplines")
        sys.exit(1)