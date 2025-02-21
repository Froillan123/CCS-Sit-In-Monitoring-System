from fuzzywuzzy import process, fuzz
from dbhelper import get_student_activity_breakdown, create_reservation
from sqlite3 import connect, Row
from datetime import datetime
import sqlite3
import regex 
from requests.exceptions import RequestException
import requests

API_KEY = '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'

import json

with open("intents.json", "r") as file:
    intents_data = json.load(file)
    INTENTS = intents_data["INTENTS"]

# Load responses from response.json
with open("response.json", "r") as file:
    responses_data = json.load(file)
    RESPONSES = responses_data["RESPONSES"]

database = "student.db"
def getprocess(sql: str, params=()) -> list:
    db = connect(database)
    db.row_factory = Row
    cursor = db.cursor()
    try:
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        db.close()


# Purpose options for reservations
PURPOSE_OPTIONS = {
    "1": "Research",
    "2": "Meeting",
    "3": "Coding",
    "4": "Assignment Work",
    "5": "Project Development",
}

# List of all activity types
ALL_ACTIVITY_TYPES = ["Research", "Meeting", "Coding", "Assignment Work", "Project Development"]

# Reservation flow state
RESERVATION_STATE = {
    "step": None,
    "lab_id": None,
    "purpose": None,
    "reservation_date": None,
    "time_in": None,
    "time_out": None,
}

def detect_intent(message):
    """
    Detects the intent of the user's message using fuzzy matching.
    """
    message = message.lower()
    best_match = {"intent": "unknown", "score": 0}

    # First, check for exact matches
    for intent, keywords in INTENTS.items():
        if message in keywords:
            return intent

    # Check for specific keyword phrases first (before fuzzy matching)
    if "delete history" in message:
        return "delete_chat_history"

    # Use fuzzy matching if no exact match found
    for intent, keywords in INTENTS.items():
        keyword_string = " ".join(keywords)
        score = fuzz.token_set_ratio(message, keyword_string) + fuzz.partial_ratio(message, keyword_string)
        print(f"Fuzzy matching score for {intent}: {score}")  # Debugging output for matching score
        if score > best_match["score"]:
            best_match["intent"] = intent
            best_match["score"] = score

    # Adjust fuzzy matching score threshold to better match the correct intent
    if best_match["score"] < 80:  # Increased threshold to 80 for stronger matches
        if "make me a program" in message or "hello world" in message:
            return "program_request"
        
        print("No fuzzy match found, returning 'unknown'")  # Debugging
        return "unknown"
    
    print(f"Best fuzzy match found: {best_match['intent']} with score {best_match['score']}")  # Debugging
    return best_match["intent"]


def get_total_session(idno: str) -> dict:
    sql = "SELECT sessions_left FROM students WHERE idno = ?"
    session = getprocess(sql, (idno,))
    return session[0] if session else None

def get_student_session_history(student_idno: str, limit: int = 30) -> list:
    sql = """
        SELECT * FROM session_history
        WHERE student_idno = ?
        ORDER BY id DESC
        LIMIT ?
    """
    return getprocess(sql, (student_idno, limit))

def get_student_session_history(student_idno: str, limit: int = 30) -> list:
    sql = """
        SELECT * FROM session_history
        WHERE student_idno = ?
        ORDER BY id DESC
        LIMIT ?
    """
    return getprocess(sql, (student_idno, limit))

def get_student_weekly_usage(student_idno: str) -> dict:
    sql = """
        SELECT strftime('%w', login_time) AS day, COUNT(*) AS session_count
        FROM session_history
        WHERE student_idno = ? AND strftime('%w', login_time) BETWEEN '0' AND '6'
        GROUP BY day
        ORDER BY day;
    """
    usage_data = getprocess(sql, (student_idno,))
    
    day_mapping = {
        '0': 'Sunday',
        '1': 'Monday',
        '2': 'Tuesday',
        '3': 'Wednesday',
        '4': 'Thursday',
        '5': 'Friday',
        '6': 'Saturday'
    }
    
    return {day_mapping.get(row['day'], 0): row['session_count'] for row in usage_data}

# Flexible time parsing
def parse_time(time_str):
    """
    Parses a time string in various formats (e.g., "4 PM", "4:00 PM", "16:00") into a datetime.time object.
    """
    time_formats = ["%I:%M %p", "%I %p", "%H:%M"]
    for fmt in time_formats:
        try:
            return datetime.strptime(time_str.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError("Invalid time format")

from fuzzywuzzy import process
from datetime import datetime

def handle_reservation(message, session):
    """
    Handles reservation-related prompts with more flexible input handling.
    """
    global RESERVATION_STATE

    # Check if the user wants to ask about reservations
    if "can i ask about reservation" in message.lower() or "ask about reservation" in message.lower():
        # Provide the available labs
        sql = "SELECT id, lab_name FROM laboratories WHERE status = 'Available'"
        labs = getprocess(sql)
        if not labs:
            return "No labs are currently available for reservation."
        
        session["available_labs"] = {str(i + 1): lab for i, lab in enumerate(labs)}
        lab_list = "\n".join([f"{i+1}. {lab['lab_name']}" for i, lab in enumerate(labs)])
        return f"Sure! Which laboratory would you like to reserve? Here are the available labs:\n{lab_list}\nIf you change your mind later, just type 'Make me a reservation'."

    # If user has not started the reservation flow yet
    if RESERVATION_STATE["step"] is None:
        # Fetch available labs from the database
        sql = "SELECT id, lab_name FROM laboratories WHERE status = 'Available'"
        labs = getprocess(sql)
        if not labs:
            return "No labs are currently available for reservation."
        
        session["available_labs"] = {str(i + 1): lab for i, lab in enumerate(labs)}
        lab_list = "\n".join([f"{i+1}. {lab['lab_name']}" for i, lab in enumerate(labs)])
        RESERVATION_STATE["step"] = "ask_lab"
        return f"Which laboratory would you like to reserve? Here are the available labs:\n{lab_list}"

    elif RESERVATION_STATE["step"] == "ask_lab":
        user_input = message.strip().lower()
        available_labs = session.get("available_labs", {})
        lab_names = [lab["lab_name"].lower() for lab in available_labs.values()]

        match, score = process.extractOne(user_input, lab_names)
        if score >= 80:  # If fuzzy match score is high enough, select the matched lab
            selected_lab = available_labs[[k for k, v in available_labs.items() if v["lab_name"].lower() == match][0]]
        elif user_input in available_labs:
            selected_lab = available_labs[user_input]
        else:
            lab_list = "\n".join([f"{num}. {lab['lab_name']}" for num, lab in available_labs.items()])
            return f"Invalid selection. Please choose a lab name or number from the list:\n{lab_list}"

        RESERVATION_STATE["lab_id"] = selected_lab["id"]
        RESERVATION_STATE["step"] = "ask_purpose"
        return RESPONSES["reservation"]["ask_purpose"]

    elif RESERVATION_STATE["step"] == "ask_purpose":
        # Allow flexible purpose input (fuzzy matching)
        purpose_options = list(PURPOSE_OPTIONS.values())
        match, score = process.extractOne(message.strip().lower(), purpose_options)

        if score >= 80:
            RESERVATION_STATE["purpose"] = match
        else:
            purpose_list = "\n".join([f"{num}. {purpose}" for num, purpose in PURPOSE_OPTIONS.items()])
            return f"Invalid selection. Please choose a purpose from the list:\n{purpose_list}"

        RESERVATION_STATE["reservation_date"] = datetime.now().date()
        RESERVATION_STATE["step"] = "ask_time_in"
        return RESPONSES["reservation"]["ask_time_in"]

    elif RESERVATION_STATE["step"] == "ask_time_in":
        try:
            # Parse the time input flexibly
            time_in = parse_time(message.strip())

            # Check if the time is within the allowed range (8:00 AM to 8:00 PM)
            if time_in < datetime.strptime("08:00", "%H:%M").time() or time_in > datetime.strptime("20:00", "%H:%M").time():
                return "Reservations are only allowed between 8:00 AM and 8:00 PM. Please provide a valid time."

            RESERVATION_STATE["time_in"] = time_in.strftime("%H:%M")
            RESERVATION_STATE["step"] = "ask_time_out"
            return RESPONSES["reservation"]["ask_time_out"]
        except ValueError:
            return "Invalid time format. Please provide the time in a recognizable format (e.g., '4 PM', '16:00')."

    elif RESERVATION_STATE["step"] == "ask_time_out":
        try:
            # Parse the time input flexibly
            time_out = parse_time(message.strip())

            # Calculate the duration of the reservation
            time_in = datetime.strptime(RESERVATION_STATE["time_in"], "%H:%M").time()
            duration = (datetime.combine(datetime.today(), time_out) - datetime.combine(datetime.today(), time_in)).seconds / 3600

            # Check if the duration exceeds 3 hours
            if duration > 3:
                return "Reservations are limited to a maximum of 3 hours. Please provide a valid end time."

            # Check if the end time is within the allowed range (8:00 AM to 8:00 PM)
            if time_out < datetime.strptime("08:00", "%H:%M").time() or time_out > datetime.strptime("20:00", "%H:%M").time():
                return "Reservations are only allowed between 8:00 AM and 8:00 PM. Please provide a valid end time."

            RESERVATION_STATE["time_out"] = time_out.strftime("%H:%M")

            # Submit the reservation
            student_idno = session.get('student_idno')
            student_name = f"{session.get('student_firstname', '')} {session.get('student_midname', '')} {session.get('student_lastname', '')}".strip()

            if create_reservation(
                student_idno=student_idno,
                student_name=student_name,
                lab_id=RESERVATION_STATE["lab_id"],
                purpose=RESERVATION_STATE["purpose"],
                reservation_date=RESERVATION_STATE["reservation_date"].strftime("%Y-%m-%d"),
                time_in=RESERVATION_STATE["time_in"],
                time_out=RESERVATION_STATE["time_out"]
            ):
                # Reset the reservation state
                RESERVATION_STATE = {
                    "step": None,
                    "lab_id": None,
                    "purpose": None,
                    "reservation_date": None,
                    "time_in": None,
                    "time_out": None,
                }
                return "Your reservation has been processed. Check the 'Reservations' section and click 'View Reservations' to see your booking."
            else:
                return "Failed to create the reservation. Please try again."
        except ValueError:
            return "Invalid time format. Please provide the time in a recognizable format (e.g., '4 PM', '16:00')."

    else:
        return RESPONSES["reservation"]["no_details"]



def get_response(message, session):
    """
    Main function to generate a response based on the detected intent or reservation flow.
    """
    global RESERVATION_STATE

    # If the user is in the middle of a reservation flow, handle it directly
    if RESERVATION_STATE["step"] is not None:
        return handle_reservation(message, session)

    # Otherwise, detect the intent and respond accordingly
    intent = detect_intent(message)
    print(f"Detected Intent: {intent}, Message: {message}")  # Debugging output

    # Handle specific intents
    if intent == "session_left":
        sessions_left = get_total_session(session.get('student_idno'))
        return "You have " + str(sessions_left) + " sessions left."

    elif intent == "session_history":
        session_history = get_student_session_history(session.get('student_idno'))
        formatted_history = "\n".join(f"Session ID: {row['id']}, Date: {row['login_time']}" for row in session_history)
        return RESPONSES["session_history"].format(history=formatted_history if formatted_history else "No session history available.")

    elif intent == "weekly_usage":
        weekly_usage = get_student_weekly_usage(session.get('student_idno'))
        formatted_usage = "\n".join(f"{day}: {count} sessions" for day, count in weekly_usage.items())
        return RESPONSES["weekly_usage"].format(usage=formatted_usage if formatted_usage else "No sessions recorded this week.")

    elif intent == "reservation":
        # Only start the reservation flow if the message is a strong match
        if "reservation" in message.lower() or "book" in message.lower() or "reserve" in message.lower():
            return handle_reservation(message, session)
        else:
            return "If you'd like to make a reservation, please say 'I want to reserve a lab' or 'Book a lab'."

    elif intent == "activity_breakdown":
        # Fetch activity breakdown data
        activity_data = get_student_activity_breakdown(session.get('student_idno'))
        if activity_data:
            response = RESPONSES["activity_breakdown"] + "\n"
            for activity in ALL_ACTIVITY_TYPES:
                count = activity_data.get(activity, 0)  # Get count or default to 0
                response += f"{activity} - {count}\n"
            return response
        else:
            return "You have no activity recorded for this semester."

    elif intent == "delete_chat_history":
        student_idno = session.get('student_idno')
        if delete_chat_history(student_idno):
            return RESPONSES["delete_chat_history"]  # Return the success message from the RESPONSES dictionary
        else:
            return "There was an error while trying to delete your chat history. Please try again."

    elif intent in RESPONSES:
        return RESPONSES[intent]
    
    else:
        # If intent doesn't match, use fallback to external API
        print("No matching intent found, calling external API...")  # Debugging
        return call_external_api(message)
    

def ask_for_confirmation_to_reserve():
    """
    Ask the user to confirm if they would like to continue with making a reservation.
    """
    return "Yes, can I make your reservation? Please say 'yes' to continue."



def delete_chat_history(student_idno):
    """
    Deletes the chat history for the given student_idno from the database.
    """
    try:
        # Connect to the database
        conn = sqlite3.connect("student.db")  # Adjust the path to your actual database file
        cursor = conn.cursor()
        
        # Delete chat history for the student_idno
        cursor.execute("DELETE FROM chat_history WHERE student_idno = ?", (student_idno,))
        
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        
        return True  # Successful deletion
    except Exception as e:
        print(f"Error deleting chat history: {e}")
        return False  # If there's an error during the deletion process


def call_external_api(message):
    try:
        response = requests.post("https://api.openrouter.com/your-endpoint", json={"message": message})
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except RequestException as e:
        print(f"Error calling external API: {e}")
        return "Sorry, there was an issue connecting to the external API. Please try again later."