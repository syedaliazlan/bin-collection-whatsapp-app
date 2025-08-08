import os
import sys
import requests
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration & Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

GREENAPI_INSTANCE_ID = os.getenv('GREENAPI_INSTANCE_ID')
GREENAPI_API_TOKEN = os.getenv('GREENAPI_API_TOKEN')
WHATSAPP_GROUP_CHAT_ID = os.getenv('WHATSAPP_GROUP_CHAT_ID')

# --- Database Models ---
class Resident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

class AppState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_person_index = db.Column(db.Integer, default=-1)

# --- Bin Collection Logic (hardcoded) ---
BIN_SCHEDULE = [
    {"type": "General waste", "color": "grey"},
    {"type": "Paper/card and Glass/cans/plastics", "color": "red and yellow"}
]

def get_current_bin_type(date):
    week_number = date.isocalendar()[1]
    return BIN_SCHEDULE[week_number % 2]

def get_next_person_and_update_state(db_session):
    residents = db_session.query(Resident).order_by(Resident.id).all()
    if not residents:
        print("Error: No residents found in the database. Cannot assign duty.")
        return None

    state = db_session.query(AppState).first()
    if not state:
        state = AppState(last_person_index=-1)
        db_session.add(state)
        db_session.commit()

    next_index = (state.last_person_index + 1) % len(residents)
    person = residents[next_index]
    state.last_person_index = next_index
    db_session.commit()
    return person

# --- WhatsApp Integration ---
def send_whatsapp_message(message):
    url = f"https://7105.api.greenapi.com/waInstance{GREENAPI_INSTANCE_ID}/sendMessage/{GREENAPI_API_TOKEN}"
    payload = {
        "chatId": WHATSAPP_GROUP_CHAT_ID,
        "message": message,
        "linkPreview": False
    }
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Message sent successfully. Response: {response.text.encode('utf8')}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")
        if 'response' in locals() and response:
            print(f"Response content: {response.text.encode('utf8')}")

# --- Main reminder logic for cron job ---
def main(reminder_type):
    try:
        with app.app_context():
            print("Starting cron job main function...")
            
            # Check if there are any residents before proceeding
            residents = db.session.query(Resident).order_by(Resident.id).all()
            if not residents:
                print("No residents found. Exiting cron job.")
                return

            if reminder_type == 'take-out':
                person = get_next_person_and_update_state(db.session)
                bin_type = get_current_bin_type(datetime.now())
                if person and bin_type:
                    message = (f"Hello {person.name}! It's your turn to take out the bins. "
                               f"Tomorrow is {bin_type['type']} collection day. "
                               f"Please put the {bin_type['color']} bins out tonight. Thanks!")
                    print(f"Sending 'take-out' reminder: {message}")
                    send_whatsapp_message(message)
            
            elif reminder_type == 'bring-in':
                state = db.session.query(AppState).first()
                if not state:
                    print("App state not initialized. Exiting cron job.")
                    return
                
                # We need to get residents again here in case the first call failed
                residents = db.session.query(Resident).order_by(Resident.id).all()
                if not residents:
                    print("No residents found. Exiting cron job.")
                    return
                
                person = residents[state.last_person_index]
                bin_type = get_current_bin_type(datetime.now())
                message = (f"Hey {person.name}, hope your day is going well! "
                           f"Just a friendly reminder to please bring in the {bin_type['color']} bins tonight. Thank you!")
                print(f"Sending 'bring-in' reminder: {message}")
                send_whatsapp_message(message)
    
    except Exception as e:
        print(f"An unexpected error occurred during cron job execution: {e}", file=sys.stderr)
        # Re-raise the exception to ensure it's logged by Render's system
        raise

    print("Cron job finished.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Error: A reminder type ('take-out' or 'bring-in') must be specified as a command-line argument.")
