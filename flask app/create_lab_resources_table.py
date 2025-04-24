import sqlite3
import os
import sys
from datetime import datetime

def create_lab_resources_table():
    """Create the lab_resources table if it doesn't exist"""
    try:
        # Connect to the database
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        print("Creating lab_resources table...")
        
        # Create the lab_resources table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lab_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT DEFAULT 'Admin'
        )
        """)
        
        conn.commit()
        print("Lab resources table created successfully!")
        
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
            print(f"Found {count} existing resources. Skipping sample data creation.")
        
        print("Finished lab_resources table setup.")
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating lab resources table: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

if __name__ == "__main__":
    create_lab_resources_table() 