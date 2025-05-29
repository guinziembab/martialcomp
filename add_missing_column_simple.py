"""
Simple script to add missing practitioner_created_id column using Django's database connection.
Run with: python manage.py shell < add_missing_column_simple.py
"""

from django.db import connection
from datetime import datetime

print(f"[{datetime.now()}] Adding practitioner_created_id column...")

try:
    with connection.cursor() as cursor:
        # Check if table exists
        if connection.vendor == 'postgresql':
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'competitions_organizationqrcodescan'
                );
            """)
            table_exists = cursor.fetchone()[0]
        else:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='competitions_organizationqrcodescan';
            """)
            table_exists = bool(cursor.fetchone())
        
        if not table_exists:
            print("❌ Table competitions_organizationqrcodescan does not exist!")
        else:
            print("✅ Table found, checking if column exists...")
            
            # Check if column exists
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'competitions_organizationqrcodescan' 
                        AND column_name = 'practitioner_created_id'
                    );
                """)
                column_exists = cursor.fetchone()[0]
            else:
                cursor.execute("PRAGMA table_info(competitions_organizationqrcodescan);")
                columns = cursor.fetchall()
                column_exists = 'practitioner_created_id' in [col[1] for col in columns]
            
            if column_exists:
                print("✅ Column practitioner_created_id already exists!")
            else:
                print("Adding practitioner_created_id column...")
                
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        ALTER TABLE competitions_organizationqrcodescan 
                        ADD COLUMN practitioner_created_id BIGINT DEFAULT NULL;
                    """)
                else:
                    cursor.execute("""
                        ALTER TABLE competitions_organizationqrcodescan 
                        ADD COLUMN practitioner_created_id INTEGER;
                    """)
                
                print("✅ Successfully added practitioner_created_id column!")

except Exception as e:
    print(f"❌ Error: {e}")

print(f"[{datetime.now()}] Script completed.")