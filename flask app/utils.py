from fuzzywuzzy import process, fuzz
from dbhelper import get_student_activity_breakdown, create_reservation
from sqlite3 import connect, Row
from flask import jsonify
from datetime import datetime
import sqlite3
import time

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

# Define intents and their associated keywords
INTENTS = {
    "reservation": ["reservation", "book", "schedule", "reserve", "time slot", "make a booking", "book a lab", "help me for reserving", "i want to reserve"],
    "sit_in_rules": ["sit-in", "sit in", "lab rules", "rules", "guidelines", "lab policies", "lab regulations"],
    "greeting": ["hi", "hello", "hey", "good morning", "good afternoon", "greetings", "what's up"],
    "cancel_reservation": ["cancel reservation", "delete reservation", "remove reservation", "how to cancel", "cancel my booking", "cancel my slot"],
    "update_profile": ["update profile", "change profile", "edit profile", "modify profile", "update my info", "change my details"],
    "lab_availability": ["lab availability", "lab schedule", "lab hours", "when is the lab open", "lab timings", "lab open hours"],
    "announcements": ["announcements", "news", "updates", "latest news", "what's new", "any updates"],
    "logout": ["logout", "sign out", "log out", "how to logout", "exit", "sign off"],
    "help": ["help", "support", "assistance", "what can you do", "how can you help", "need help"],
    "activity_breakdown": ["activity breakdown", "my activity", "semester activity", "what have i done", "my reservations", "show my activity", "activity this sem", "activity this semester"],
    "capabilities": ["what can you do", "your capabilities", "what are your features", "what do you do", "your functions"],
    "unknown": ["unknown", "not sure", "no idea", "don't know"],
}

# Define responses for each intent
RESPONSES = {
     "reservation": {
        "initial": "Let's make a reservation! Please provide the following details:",
        "ask_lab": "Which laboratory would you like to reserve? Here are the available labs:\n1. Lab A\n2. Lab B\n3. Lab C",
        "ask_purpose": "What is the purpose of your reservation? Here are the options:\n1. Research\n2. Meeting\n3. Coding\n4. Assignment Work\n5. Project Development",
        "ask_date": "What date would you like to reserve? (Please provide the date in YYYY-MM-DD format, and it must be today or a future date.)",
        "ask_time_in": "What time will you start? (Please provide the time in HH:MM format.)",
        "ask_time_out": "What time will you end? (Please provide the time in HH:MM format.)",
        "confirm": "Your reservation has been processed. Check the 'Reservations' section and click 'View Reservations' to see your booking.",
        "no_details": "Sorry, I didn't understand your reservation request. Please provide more details.",
    },
    "sit_in_rules": """
        Sit-In Laboratory Rules:
        1. No games, personal devices, or inappropriate content.
        2. Do not alter computer settings or delete files.
        3. Follow seating arrangements and deposit bags at the counter.
        4. No food, drinks, or smoking in the lab.
        5. Disturbances may lead to removal or security intervention.
        6. Handle equipment with care – Report any damages or issues immediately to the instructor.
        7. Use headphones for audio – Keep noise levels low to avoid disturbing others.
        8. Log out after use – Ensure you log out from all accounts and close applications before leaving.
    """,
    "greeting": "Hello! How can I assist you today?",
    "cancel_reservation": "To cancel a reservation, go to the 'Reservations' section, click 'View Reservations', and if there is a pending request, you can cancel your booking there.",
    "update_profile": "To update your profile, go to the 'Profile' section and click 'Edit Profile'.",
    "lab_availability": "The lab is available from 8:00 AM to 8:00 PM on weekdays.",
    "announcements": "You can view the latest announcements in the 'Announcements' section.",
    "logout": "To log out, click the 'Logout' button in the top-right corner of the dashboard.",
    "help": "How can I assist you? You can ask me about reservations, lab rules, profile updates, and more.",
    "activity_breakdown": "Here is your activity breakdown for the semester:",
    "capabilities": """
        Here's what I can do:
        - Help you make or cancel reservations.
        - Provide information about lab rules and availability.
        - Show your activity breakdown for the semester.
        - Update your profile.
        - Log you out of the system.
        - Provide announcements and updates.
        Just ask me anything related to these topics!
    """,
    "unknown": "Sorry, I have no knowledge beyond that. Just ask me about Sit-In related topics, and I will answer.",
}


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

def get_student_activity_breakdown(student_idno):
    """
    Fetch activity breakdown data from the database and ensure all activity types are included.
    """
    # Initialize activity data with all activity types set to 0
    activity_data = {activity: 0 for activity in ALL_ACTIVITY_TYPES}

    # Fetch data from the database
    sql = """
        SELECT purpose, COUNT(*) as count 
        FROM reservations 
        WHERE student_idno = ?
        GROUP BY purpose
    """
    results = getprocess(sql, (student_idno,))

    # Update activity_data with counts from the database
    for row in results:
        activity_data[row['purpose']] = row['count']

    return activity_data

def detect_intent(message):
    """
    Detects the intent of the user's message using fuzzy matching.
    """
    message = message.lower()
    best_match = {"intent": "unknown", "score": 0}

    # Use process.extractOne to find the best match across all keywords
    for intent, keywords in INTENTS.items():
        # Combine all keywords for the intent into a single string for matching
        keyword_string = " ".join(keywords)
        score = fuzz.token_set_ratio(message, keyword_string)
        if score > best_match["score"]:
            best_match["intent"] = intent
            best_match["score"] = score

    # If the score is too low, consider it as an unknown intent
    if best_match["score"] < 40:  # Lowered threshold for better matching
        return "unknown"
    return best_match["intent"]

def handle_reservation(message, session):
    """
    Handles reservation-related prompts.
    """
    global RESERVATION_STATE

    if RESERVATION_STATE["step"] is None:
        # Fetch available labs from the database
        sql = "SELECT id, lab_name FROM laboratories WHERE status = 'Available'"
        labs = getprocess(sql)
        if not labs:
            return "No labs are currently available for reservation."

        # Store the list of available labs in the session for later reference
        session["available_labs"] = {str(i + 1): lab for i, lab in enumerate(labs)}

        # Format the list of available labs with numbers
        lab_list = "\n".join([f"{i+1}. {lab['lab_name']}" for i, lab in enumerate(labs)])
        RESERVATION_STATE["step"] = "ask_lab"
        return f"Which laboratory would you like to reserve? Here are the available labs:\n{lab_list}"

    elif RESERVATION_STATE["step"] == "ask_lab":
        # Validate the selected lab number
        selected_lab_number = message.strip()
        available_labs = session.get("available_labs", {})

        if selected_lab_number not in available_labs:
            # Re-prompt the user with the list of available labs
            lab_list = "\n".join([f"{num}. {lab['lab_name']}" for num, lab in available_labs.items()])
            return f"Invalid selection. Please choose a number from the list:\n{lab_list}"

        # Get the selected lab's ID and name
        selected_lab = available_labs[selected_lab_number]
        RESERVATION_STATE["lab_id"] = selected_lab["id"]
        RESERVATION_STATE["step"] = "ask_purpose"
        return RESPONSES["reservation"]["ask_purpose"]

    elif RESERVATION_STATE["step"] == "ask_purpose":
        # Validate the selected purpose number
        selected_purpose_number = message.strip()
        if selected_purpose_number not in PURPOSE_OPTIONS:
            # Re-prompt the user with the list of purpose options
            purpose_list = "\n".join([f"{num}. {purpose}" for num, purpose in PURPOSE_OPTIONS.items()])
            return f"Invalid selection. Please choose a number from the list:\n{purpose_list}"

        # Get the selected purpose
        RESERVATION_STATE["purpose"] = PURPOSE_OPTIONS[selected_purpose_number]
        RESERVATION_STATE["step"] = "ask_date"
        return RESPONSES["reservation"]["ask_date"]

    elif RESERVATION_STATE["step"] == "ask_date":
        try:
            reservation_date = datetime.strptime(message.strip(), "%Y-%m-%d").date()
            if reservation_date < datetime.now().date():
                return "Invalid date. Please provide a date that is today or in the future."
            RESERVATION_STATE["reservation_date"] = reservation_date
            RESERVATION_STATE["step"] = "ask_time_in"
            return RESPONSES["reservation"]["ask_time_in"]
        except ValueError:
            return "Invalid date format. Please provide the date in YYYY-MM-DD format."

    elif RESERVATION_STATE["step"] == "ask_time_in":
        RESERVATION_STATE["time_in"] = message.strip()
        RESERVATION_STATE["step"] = "ask_time_out"
        return RESPONSES["reservation"]["ask_time_out"]

    elif RESERVATION_STATE["step"] == "ask_time_out":
        RESERVATION_STATE["time_out"] = message.strip()

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
            return "Your reservation has been processed. Check the 'Reservations' section and click 'View Reservations' to see your booking. and refresh the page."
        else:
            return "Failed to create the reservation. Please try again."

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
    print(f"Detected Intent: {intent}, Message: {message}")  # Debugging

    if intent == "reservation":
        return handle_reservation(message, session)
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
    elif intent in RESPONSES:
        return RESPONSES[intent]
    else:
        return RESPONSES["unknown"]