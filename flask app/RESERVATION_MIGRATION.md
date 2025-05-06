# Reservation System Migration Guide

This document explains the changes made to consolidate the reservation system in the CCS-Sit-In-Monitoring-System.

## What Changed

The system previously had two separate tables for managing reservations:
1. `student_reservation` - For tracking student lab reservations
2. `logged_out_student_reservation` - For archiving completed reservations

These have been consolidated into a single `reservations` table that can handle both sit-ins and reservations, simplifying the system's architecture.

## New Schema

The new `reservations` table has the following structure:

```sql
CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_idno TEXT NOT NULL,
    student_name TEXT NOT NULL,
    lab_id INTEGER NOT NULL,
    computer_id INTEGER,
    computer_number INTEGER,
    purpose TEXT NOT NULL,
    reservation_date TEXT NOT NULL,
    time_slot TEXT,
    login_time TEXT,
    logout_time TEXT,
    status TEXT DEFAULT 'Pending', -- Pending, Approved, Rejected, Logged Out
    reservation_type TEXT NOT NULL, -- 'sit-in' or 'reservation'
    session_number INTEGER,
    points_awarded INTEGER DEFAULT 0,
    feedback_submitted INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_idno) REFERENCES students(idno),
    FOREIGN KEY (lab_id) REFERENCES laboratories(id),
    FOREIGN KEY (computer_id) REFERENCES lab_computers(id)
)
```

The notification table has also been updated to reference the new `reservations` table.

## Key Features

- **Reservation Types**: Each record has a `reservation_type` field that distinguishes between 'sit-in' and 'reservation'
- **Simplified Status Tracking**: All reservations use the same status field with values: 'Pending', 'Approved', 'Rejected', 'Logged Out'
- **No Automatic Status Changes**: The system no longer automatically changes reservation status based on time
- **Consolidated API**: All operations now use the same set of functions for both sit-ins and reservations

## Running the Migration

To migrate your existing database to the new system:

1. Run the migration script:
   ```
   python migrate_reservations.py
   ```

2. Create the notification tables:
   ```
   python create_notification_tables.py
   ```

## Important Functions

The following functions have been updated to work with the consolidated table:

- `create_reservation()` - Creates a new reservation in the consolidated table
- `get_student_reservations()` - Gets all reservations for a student
- `update_computer_status()` - Updates computer status in lab
- `logout_student()` - Logs out a student from their reservation

## API Endpoints 

The API endpoints have been updated:

- `/create_reservation` - Creates a new reservation
- `/get_currentsitin` - Gets current sit-ins and approved reservations
- `/api/update_reservation_status` - Updates reservation status
- `/logout-student/<reservation_id>` - Logs out a student from a reservation

## UI Changes

The reservation-related UI should continue to function as before, but with a more consistent display of reservation types.

## Troubleshooting

If you encounter issues:

1. Check the application logs for detailed error messages
2. Verify database integrity by examining the `reservations` table schema
3. Ensure all foreign key references are valid
4. Re-run the migration script if needed 