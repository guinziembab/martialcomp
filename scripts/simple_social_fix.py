#!/usr/bin/env python3
"""
Simple script to fix duplicate social apps directly in PostgreSQL
"""
import psycopg2

def fix_social_apps():
    """Fix duplicate social applications"""
    print("🔧 Fixing social apps duplication...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host='localhost',
            database='martialcomp_dev',
            user='postgres',
            password='password'
        )
        
        cursor = conn.cursor()
        
        # Check current apps
        cursor.execute("SELECT id, provider, name FROM socialaccount_socialapp ORDER BY id")
        apps = cursor.fetchall()
        
        print(f"📊 Found {len(apps)} social apps:")
        for app_id, provider, name in apps:
            print(f"  - ID: {app_id}, Provider: {provider}, Name: {name}")
        
        if len(apps) == 0:
            print("ℹ️  No social apps found")
            return True
        
        # Find duplicates
        providers_seen = set()
        to_delete = []
        
        for app_id, provider, name in apps:
            if provider in providers_seen:
                to_delete.append(app_id)
                print(f"  ❌ Marking for deletion: {provider} (ID: {app_id})")
            else:
                providers_seen.add(provider)
                print(f"  ✅ Keeping: {provider} (ID: {app_id})")
        
        # Delete duplicates
        for app_id in to_delete:
            try:
                # First delete from socialaccount_socialapp_sites (junction table)
                cursor.execute("DELETE FROM socialaccount_socialapp_sites WHERE socialapp_id = %s", (app_id,))
                
                # Then delete the app itself
                cursor.execute("DELETE FROM socialaccount_socialapp WHERE id = %s", (app_id,))
                
                conn.commit()
                print(f"  🗑️  Deleted app ID: {app_id}")
                
            except Exception as e:
                conn.rollback()
                print(f"  ⚠️  Error deleting app {app_id}: {e}")
        
        # Check result
        cursor.execute("SELECT id, provider, name FROM socialaccount_socialapp ORDER BY id")
        remaining_apps = cursor.fetchall()
        
        print(f"\n📋 Remaining apps ({len(remaining_apps)}):")
        for app_id, provider, name in remaining_apps:
            print(f"  - {provider}: {name} (ID: {app_id})")
        
        conn.close()
        print("✅ Social apps fix completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    fix_social_apps()