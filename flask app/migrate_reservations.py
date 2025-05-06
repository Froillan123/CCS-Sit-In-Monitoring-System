#!/usr/bin/env python
import sqlite3
from dbhelper import (
    create_reservations_table, 
    create_reservation_notifications_table,
    migrate_reservations_data
)

def drop_old_tables():
    """Drop the old student_reservation and logged_out_student_reservation tables"""
    try:
        print("Dropping old reservation tables...")
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Check if tables exist before dropping
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('student_reservation', 'logged_out_student_reservation')")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        if 'student_reservation' in table_names:
            cursor.execute('DROP TABLE IF EXISTS student_reservation')
            print("Dropped student_reservation table")
        
        if 'logged_out_student_reservation' in table_names:
            cursor.execute('DROP TABLE IF EXISTS logged_out_student_reservation')
            print("Dropped logged_out_student_reservation table")
        
        conn.commit()
        print("Old tables dropped successfully")
        return True
    except Exception as e:
        print(f"Error dropping old tables: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def run_migration():
    """Run the full migration process"""
    print("Starting reservation system migration...")
    
    # Step 1: Create the new reservations table
    print("\nStep 1: Creating new reservations table...")
    if create_reservations_table():
        print("✓ New reservations table created successfully")
    else:
        print("✗ Failed to create new reservations table")
        return False
    
    # Step 2: Migrate data from old tables to new table
    print("\nStep 2: Migrating data from old tables...")
    if migrate_reservations_data():
        print("✓ Data migration completed successfully")
    else:
        print("✗ Failed to migrate data")
        return False
    
    # Step 3: Create the new notifications table with correct foreign key
    print("\nStep 3: Creating new notifications table...")
    if create_reservation_notifications_table():
        print("✓ New notifications table created successfully")
    else:
        print("✗ Failed to create new notifications table")
        return False
    
    # Step 4: Drop the old tables
    print("\nStep 4: Dropping old tables...")
    if drop_old_tables():
        print("✓ Old tables dropped successfully")
    else:
        print("✗ Failed to drop old tables")
        # This step can fail but we still continue
    
    print("\nMigration completed successfully!")
    return True

if __name__ == "__main__":
    # Run the migration when script is executed directly
    run_migration() 