import sqlite3
import os
from datetime import datetime

def seed_lab_resources():
    """Add sample lab resources to the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Check if lab_resources table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lab_resources'")
        if not cursor.fetchone():
            print("Creating lab_resources table...")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                link TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL
            )
            """)
            conn.commit()
        
        # Check if any resources exist, add sample resources if none
        cursor.execute("SELECT COUNT(*) FROM lab_resources")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Adding sample lab resources...")
            
            sample_resources = [
                (
                    "Python Programming Guide",
                    "A comprehensive guide for Python programming with examples and best practices for beginners.",
                    "https://docs.python.org/3/tutorial/",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "System Admin"
                ),
                (
                    "Java Development Kit",
                    "Official guide for Java Development Kit (JDK) installation and setup for various operating systems.",
                    "https://www.oracle.com/java/technologies/javase-downloads.html",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "System Admin"
                ),
                (
                    "Web Development Fundamentals",
                    "Learn HTML, CSS, and JavaScript with interactive tutorials and projects for beginners.",
                    "https://developer.mozilla.org/en-US/docs/Web",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "System Admin"
                ),
                (
                    "Database Management Systems",
                    "Introduction to database concepts, SQL queries, and database design principles.",
                    "https://www.w3schools.com/sql/",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "System Admin"
                ),
                (
                    "Git Version Control",
                    "Learn how to use Git for version control and collaboration in software projects.",
                    "https://git-scm.com/doc",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "System Admin"
                )
            ]
            
            cursor.executemany('''
            INSERT INTO lab_resources (title, content, link, created_at, created_by)
            VALUES (?, ?, ?, ?, ?)
            ''', sample_resources)
            
            conn.commit()
            print(f"Added {len(sample_resources)} sample resources.")
        else:
            print(f"Found {count} existing resources. No need to add samples.")
        
        # Display current resources
        cursor.execute("SELECT id, title FROM lab_resources")
        resources = cursor.fetchall()
        print("\nCurrent lab resources:")
        for resource in resources:
            print(f"ID: {resource[0]}, Title: {resource[1]}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error seeding lab resources: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

if __name__ == "__main__":
    seed_lab_resources() 