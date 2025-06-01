#!/usr/bin/env python3
"""
Direct SQLite script to add missing practitioner_created_id column to competitions_organizationqrcodescan table.
This script connects directly to SQLite without Django dependencies.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

def main():
    # SQLite database path
    script_dir = Path(__file__).parent
    db_path = script_dir / 'db.sqlite3'
    
    print(f"[{datetime.now()}] Starting practitioner_created_id column addition...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"❌ ERROR: Database file {db_path} does not exist!")
        return False
    
    try:
        # Connect to SQLite
        print("Connecting to SQLite database...")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='competitions_organizationqrcodescan';
        """)
        
        table_exists = cursor.fetchone()
        if not table_exists:
            print("❌ ERROR: Table competitions_organizationqrcodescan does not exist!")
            return False
        
        print("✅ Table competitions_organizationqrcodescan found")
        
        # Check current table structure
        cursor.execute("PRAGMA table_info(competitions_organizationqrcodescan);")
        columns = cursor.fetchall()
        
        print("Current table structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Check if the column already exists
        column_names = [col[1] for col in columns]
        if 'practitioner_created_id' in column_names:
            print("✅ Column practitioner_created_id already exists!")
            return True
        
        # Add the missing column
        print("Adding practitioner_created_id column...")
        cursor.execute("""
            ALTER TABLE competitions_organizationqrcodescan 
            ADD COLUMN practitioner_created_id INTEGER;
        """)
        
        # Commit the changes
        conn.commit()
        print("✅ Successfully added practitioner_created_id column!")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(competitions_organizationqrcodescan);")
        new_columns = cursor.fetchall()
        
        new_column_names = [col[1] for col in new_columns]
        if 'practitioner_created_id' in new_column_names:
            print("✅ Column verified successfully!")
            print("Updated table structure:")
            for col in new_columns:
                if col[1] == 'practitioner_created_id':
                    print(f"  + {col[1]} ({col[2]}) - NEWLY ADDED")
                else:
                    print(f"    {col[1]} ({col[2]})")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ SQLite Error: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n✅ Script completed successfully at {datetime.now()}")
        print("You can now test the account deletion functionality.")
        sys.exit(0)
    else:
        print(f"\n❌ Script failed at {datetime.now()}")
        sys.exit(1)