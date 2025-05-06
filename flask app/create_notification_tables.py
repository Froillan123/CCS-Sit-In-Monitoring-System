#!/usr/bin/env python
"""
Script to create the reservation notification tables
This script can be run directly to ensure the notification tables are created with proper foreign keys.
"""
import sqlite3

def create_notification_tables():
    """Create the notification tables with proper foreign keys"""
    try:
        print("Creating notification tables...")
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # First check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reservation_notifications'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("Notification table already exists, dropping to recreate...")
            cursor.execute('DROP TABLE IF EXISTS reservation_notifications')
        
        # Create the reservation notifications table
        cursor.execute('''
        CREATE TABLE reservation_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_idno TEXT NOT NULL,
            reservation_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_idno) REFERENCES students(idno),
            FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
        )''')
        
        # Create index for faster queries
        cursor.execute('CREATE INDEX idx_notification_student ON reservation_notifications(student_idno)')
        cursor.execute('CREATE INDEX idx_notification_is_read ON reservation_notifications(is_read)')
        
        conn.commit()
        print("Reservation notification tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating notification tables: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Run when executed directly
    success = create_notification_tables()
    if success:
        print("✓ Notification tables created successfully!")
    else:
        print("✗ Failed to create notification tables.") 