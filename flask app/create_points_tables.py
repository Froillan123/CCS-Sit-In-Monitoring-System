#!/usr/bin/env python
"""
Script to create the necessary tables for the student points system.
Run this script once to set up the points system in your database.
"""

from dbhelper import create_points_tables
import sqlite3

def setup_points_system():
    print("Setting up student points system...")
    
    # First check if tables already exist
    conn = sqlite3.connect('student.db')
    cursor = conn.cursor()
    
    # Check if student_points table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='student_points'
    """)
    student_points_exists = cursor.fetchone() is not None
    
    # Check if points_history table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='points_history'
    """)
    points_history_exists = cursor.fetchone() is not None
    
    if student_points_exists and points_history_exists:
        print("Points system tables already exist.")
    else:
        # Create the tables
        success = create_points_tables()
        if success:
            print("Points system tables created successfully!")
        else:
            print("Failed to create points system tables.")
    
    # Check if reservations table has points_awarded column
    cursor.execute("PRAGMA table_info(reservations)")
    columns = cursor.fetchall()
    has_points_awarded = any(col[1] == 'points_awarded' for col in columns)
    
    if not has_points_awarded:
        print("Adding points_awarded column to reservations table...")
        cursor.execute("ALTER TABLE reservations ADD COLUMN points_awarded INTEGER DEFAULT 0")
        conn.commit()
        print("Added points_awarded column.")
    
    # Now initialize points for all students who don't have records
    cursor.execute("""
        INSERT INTO student_points (student_idno, points)
        SELECT idno, 0 FROM students s
        WHERE NOT EXISTS (
            SELECT 1 FROM student_points sp
            WHERE sp.student_idno = s.idno
        )
    """)
    
    students_initialized = cursor.rowcount
    conn.commit()
    
    # Check for existing points_history entries and mark reservations accordingly
    print("Marking reservations with awarded points...")
    cursor.execute("""
        UPDATE reservations
        SET points_awarded = 1
        WHERE id IN (
            SELECT r.id
            FROM reservations r
            JOIN points_history ph ON r.student_idno = ph.student_idno
            WHERE ph.reason LIKE 'Reward for lab session%'
            AND ph.awarded_at BETWEEN r.login_time AND COALESCE(r.logout_time, datetime('now', 'localtime'))
        )
    """)
    
    reservations_marked = cursor.rowcount
    conn.commit()
    
    print(f"Initialized points for {students_initialized} students.")
    print(f"Marked {reservations_marked} reservations as having points awarded.")
    
    # Create the lab_resources table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lab_resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        link TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    
    conn.close()
    
    print("Setup complete!")

if __name__ == "__main__":
    setup_points_system() 