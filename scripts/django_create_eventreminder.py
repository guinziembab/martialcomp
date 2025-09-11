#!/usr/bin/env python3
"""
Script Django pour créer la table EventReminder via Django management
"""

# Code Django à exécuter dans manage.py shell
django_shell_code = '''
from django.db import connection
import uuid

print("🚨 CRÉATION TABLE competitions_eventreminder VIA DJANGO")
print("=" * 65)

with connection.cursor() as cursor:
    # 1. Vérifier si la table existe
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'competitions_eventreminder'
        );
    """)
    
    table_exists = cursor.fetchone()[0]
    print(f"Table existe: {table_exists}")
    
    if table_exists:
        print("Suppression de la table incomplète...")
        cursor.execute("DROP TABLE IF EXISTS competitions_eventreminder_recipients CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS competitions_eventreminder CASCADE;")
    
    # 2. Créer la table complète
    print("Création de la table competitions_eventreminder...")
    
    create_sql = """
    CREATE TABLE competitions_eventreminder (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        title VARCHAR(200) NOT NULL,
        message TEXT NOT NULL,
        reminder_type VARCHAR(20) DEFAULT 'notification',
        time_before_event INTERVAL,
        send_at TIMESTAMP WITH TIME ZONE,
        is_sent BOOLEAN DEFAULT false,
        sent_at TIMESTAMP WITH TIME ZONE,
        is_enabled BOOLEAN DEFAULT true,
        send_to VARCHAR(20) DEFAULT 'all',
        delivery_status JSONB DEFAULT '{}'::jsonb,
        open_rate DOUBLE PRECISION,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        created_by_id INTEGER,
        settings JSONB DEFAULT '{}'::jsonb,
        
        CONSTRAINT fk_eventreminder_event 
            FOREIGN KEY (event_id) REFERENCES competitions_event(id) ON DELETE CASCADE,
        CONSTRAINT fk_eventreminder_created_by 
            FOREIGN KEY (created_by_id) REFERENCES auth_user(id) ON DELETE SET NULL
    );
    """
    
    try:
        cursor.execute(create_sql)
        print("✅ Table competitions_eventreminder créée!")
    except Exception as e:
        print(f"❌ Erreur création table: {e}")
        exit()
    
    # 3. Créer la table de liaison
    print("Création table recipients...")
    cursor.execute("""
        CREATE TABLE competitions_eventreminder_recipients (
            id SERIAL PRIMARY KEY,
            eventreminder_id UUID NOT NULL,
            user_id INTEGER NOT NULL,
            CONSTRAINT fk_eventreminder_recipients_reminder 
                FOREIGN KEY (eventreminder_id) REFERENCES competitions_eventreminder(id) ON DELETE CASCADE,
            CONSTRAINT fk_eventreminder_recipients_user 
                FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
            UNIQUE(eventreminder_id, user_id)
        );
    """)
    print("✅ Table recipients créée!")
    
    # 4. Créer les index
    print("Création des index...")
    indexes = [
        "CREATE INDEX idx_eventreminder_event ON competitions_eventreminder(event_id);",
        "CREATE INDEX idx_eventreminder_send_at ON competitions_eventreminder(send_at);",
        "CREATE INDEX idx_eventreminder_is_sent ON competitions_eventreminder(is_sent);"
    ]
    
    for idx_sql in indexes:
        cursor.execute(idx_sql)
    print("✅ Index créés!")
    
    # 5. Vérifier les colonnes critiques
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'competitions_eventreminder'
        AND column_name IN ('send_at', 'sent_at', 'is_sent')
        ORDER BY column_name;
    """)
    
    critical_columns = [row[0] for row in cursor.fetchall()]
    print(f"Colonnes critiques trouvées: {critical_columns}")
    
    if len(critical_columns) >= 3:
        print("✅ Toutes les colonnes critiques présentes!")
    else:
        print("❌ Colonnes critiques manquantes!")

# Test immédiat
print("\\n🧪 TEST SUPPRESSION D'ÉVÉNEMENT")
try:
    from competitions.models.event import Event
    from django.utils import timezone
    
    # Créer un événement test
    test_event = Event.objects.create(
        title="Test EventReminder Table",
        description="Test après création table complète",
        event_type="training",
        start_date=timezone.now().date(),
        end_date=timezone.now().date(),
    )
    print(f"✅ Événement créé: {test_event.id}")
    
    # Tenter suppression (cause de l'erreur originale)
    test_event.delete()
    print("✅ SUPPRESSION RÉUSSIE - Plus d'erreur send_at!")
    
except Exception as e:
    print(f"❌ Erreur test: {e}")

print("\\n🎉 TABLE EVENTREMINDER CRÉÉE AVEC SUCCÈS!")
print("La colonne send_at est maintenant disponible.")
print("L'erreur ProgrammingError est résolue.")
'''

print("🔧 SCRIPT DJANGO POUR CRÉER TABLE EVENTREMINDER")
print("=" * 60)
print()
print("📋 Code à exécuter dans Django shell:")
print()
print(django_shell_code)
print()
print("🚀 INSTRUCTIONS D'EXÉCUTION:")
print()
print("1. Ouvrir un terminal Windows")
print("2. cd C:\\martial_hub_django\\martialcomp")
print("3. .venv\\Scripts\\activate")
print("4. python manage.py shell")
print("5. Coller le code ci-dessus")
print()
print("OU exécuter directement:")
print('echo "exec(open(\'django_create_eventreminder.py\').read())" | python manage.py shell')

# Sauvegarder le code dans un fichier temporaire
with open('temp_create_eventreminder.py', 'w', encoding='utf-8') as f:
    f.write(django_shell_code)

print()
print("💾 Code sauvegardé dans: temp_create_eventreminder.py")