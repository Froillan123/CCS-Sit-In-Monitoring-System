import sqlite3
from datetime import datetime
import traceback

def reset_all_lab_schedules():
    """Drop and recreate lab_schedules table structure without inserting any data."""
    try:
        print("INFO: Starting to reset lab schedules table structure")
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        
        # Drop the lab_schedules table if it exists
        cursor.execute('DROP TABLE IF EXISTS lab_schedules')
        print("INFO: lab_schedules table dropped")
        
        # Create the lab_schedules table again
        cursor.execute('''
        CREATE TABLE lab_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')),
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            subject_code TEXT,
            subject_name TEXT,
            status TEXT DEFAULT 'Available' CHECK(status IN ('Available', 'Reserved', 'Unavailable')),
            reason TEXT,
            FOREIGN KEY (lab_id) REFERENCES laboratories(id)
        )''')
        print("INFO: lab_schedules table recreated")
        
        conn.commit()
        print("SUCCESS: Successfully recreated lab_schedules table structure")
        return {"success": True, "message": "Lab schedules table structure recreated successfully. No schedules were inserted."}
    except Exception as e:
        print(f"ERROR: Error resetting lab schedules table: {str(e)}")
        print(traceback.format_exc())
        if 'conn' in locals() and conn:
            conn.rollback()
        return {"success": False, "message": f"Failed to reset lab schedules table: {str(e)}"}
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    # This allows the script to be run directly
    result = reset_all_lab_schedules()
    print(result) 