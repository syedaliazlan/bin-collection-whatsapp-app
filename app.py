import os
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- HTML Templates (for simplicity, kept as strings) ---
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bin Collection App</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-xl p-8">
        <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">Bin Collection Reminder</h1>
        <p class="text-gray-600 mb-4 text-center">This app automates bin collection reminders for your household using WhatsApp. Residents take turns in a fair rotation.</p>

        <div class="flex justify-center space-x-4 mb-8">
            <a href="{{ url_for('setup') }}" class="bg-indigo-600 text-white font-semibold py-2 px-6 rounded-lg shadow-md hover:bg-indigo-700 transition duration-300">
                Manage Residents
            </a>
            <a href="{{ url_for('schedule') }}" class="bg-green-600 text-white font-semibold py-2 px-6 rounded-lg shadow-md hover:bg-green-700 transition duration-300">
                View Schedule
            </a>
        </div>

        <div class="mb-6">
            <h2 class="text-xl font-semibold mb-2 text-gray-700">Current Residents:</h2>
            {% if residents %}
                <ul class="list-disc list-inside bg-gray-50 p-4 rounded-md">
                    {% for resident in residents %}
                        <li class="text-gray-700">{{ resident.name }}</li>
                    {% endfor %}
                </ul>
            {% else %}
                <p class="text-gray-500 italic">No residents have been added yet. Please go to the setup page to add them.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

SETUP_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setup Bin Collection App</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-xl mx-auto bg-white rounded-lg shadow-xl p-8">
        <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">App Setup</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="mb-4">
                {% for category, message in messages %}
                    <div class="p-3 rounded-md {{ 'bg-red-100 text-red-700' if category == 'error' else 'bg-green-100 text-green-700' }}">
                        {{ message }}
                    </div>
                {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="mb-8 p-4 bg-gray-50 rounded-md">
            <h2 class="text-xl font-semibold mb-2 text-gray-700">Bin Schedule</h2>
            <p class="text-gray-600">The schedule is fixed: General waste on even weeks, Recycling on odd weeks. Both are collected on Fridays.</p>
        </div>

        <div class="mb-8">
            <h2 class="text-xl font-semibold mb-2 text-gray-700">Add a New Resident</h2>
            <form action="{{ url_for('setup') }}" method="post" class="flex flex-col gap-4">
                <input type="text" name="name" placeholder="Enter resident's name" required class="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <button type="submit" name="add_resident" class="bg-green-500 text-white font-semibold py-3 rounded-lg shadow-md hover:bg-green-600 transition duration-300">
                    Add Resident
                </button>
            </form>
        </div>

        <div class="mb-8">
            <h2 class="text-xl font-semibold mb-2 text-gray-700">Current Residents</h2>
            {% if residents %}
                <ul class="list-disc list-inside bg-gray-50 p-4 rounded-md">
                    {% for resident in residents %}
                        <li class="text-gray-700 flex justify-between items-center">
                            <span>{{ resident.name }}</span>
                            <form action="{{ url_for('setup') }}" method="post" class="inline-block">
                                <input type="hidden" name="resident_id" value="{{ resident.id }}">
                                <button type="submit" name="remove_resident" class="text-red-500 hover:text-red-700 font-bold ml-4">
                                    &times;
                                </button>
                            </form>
                        </li>
                    {% endfor %}
                </ul>
            {% else %}
                <p class="text-gray-500 italic">No residents added yet.</p>
            {% endif %}
        </div>
        
        <div class="flex flex-col gap-4">
            <form action="{{ url_for('setup') }}" method="post">
                <button type="submit" name="clear_residents" class="w-full bg-red-500 text-white font-semibold py-3 rounded-lg shadow-md hover:bg-red-600 transition duration-300">
                    Clear All Residents
                </button>
            </form>
            <a href="{{ url_for('home') }}" class="w-full text-center bg-gray-300 text-gray-800 font-semibold py-3 rounded-lg shadow-md hover:bg-gray-400 transition duration-300">
                Back to Home
            </a>
        </div>
    </div>
</body>
</html>
"""

SCHEDULE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bin Collection Schedule</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-xl p-8">
        <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">Bin Collection Schedule</h1>
        
        {% if schedule %}
            <div class="mb-6">
                <h2 class="text-xl font-semibold mb-2 text-gray-700">Upcoming Collections:</h2>
                <ul class="list-none space-y-4">
                    {% for item in schedule %}
                    <li class="p-4 rounded-md shadow-sm border border-gray-200">
                        <p class="text-lg font-medium text-gray-800">
                            <span class="font-bold">{{ item.date.strftime('%A, %d %B %Y') }}</span>
                            <br>
                            <span class="text-sm text-gray-500">Bin Type:</span>
                            <span class="font-bold text-lg">{{ item.bin_type }}</span>
                        </p>
                        <p class="text-gray-600">
                            <span class="text-sm text-gray-500">Responsible Person:</span>
                            <span class="font-bold text-lg">{{ item.person }}</span>
                        </p>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        {% else %}
            <p class="text-gray-500 italic text-center">No residents have been added yet, so a schedule cannot be generated.</p>
        {% endif %}
        
        <div class="flex justify-center space-x-4 mt-8">
            <a href="{{ url_for('home') }}" class="bg-indigo-600 text-white font-semibold py-2 px-6 rounded-lg shadow-md hover:bg-indigo-700 transition duration-300">
                Back to Home
            </a>
        </div>
    </div>
</body>
</html>
"""

TEST_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Reminder Output</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-xl p-8">
        <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">Test Reminder Output</h1>
        <p class="text-gray-600 mb-4 text-center">This is a simulated message. No message was sent to WhatsApp.</p>

        <div class="mb-6 p-4 bg-gray-50 rounded-md">
            <h2 class="text-xl font-semibold mb-2 text-gray-700">Simulated Message:</h2>
            <p class="text-gray-800">{{ message }}</p>
        </div>
        
        <div class="flex justify-center space-x-4 mt-8">
            <a href="{{ url_for('home') }}" class="bg-indigo-600 text-white font-semibold py-2 px-6 rounded-lg shadow-md hover:bg-indigo-700 transition duration-300">
                Back to Home
            </a>
        </div>
    </div>
</body>
</html>
"""
# --- Configuration & Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/bin_app_db')
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
COLLECTION_DAY = 4 # Friday

def get_current_bin_type(date):
    week_number = date.isocalendar()[1]
    return BIN_SCHEDULE[week_number % 2]

def get_next_person_and_update_state(db_session):
    residents = db_session.query(Resident).order_by(Resident.id).all()
    if not residents:
        return None

    state = db_session.query(AppState).first()
    if not state:
        state = AppState(last_person_index=-1)
        db_session.add(state)
        db_session.commit()

    next_index = (state.last_person_index + 1) % len(residents)
    person = residents[next_index]
    state.last_person_index = next_index
    db.session.commit()
    return person

def get_person_for_test(db_session, offset):
    residents = db_session.query(Resident).order_by(Resident.id).all()
    if not residents:
        return None, None
    state = db_session.query(AppState).first()
    last_person_index = state.last_person_index if state else -1
    person_index = (last_person_index + offset + 1) % len(residents)
    person = residents[person_index]
    test_date = datetime.now(timezone('Europe/London')) + timedelta(weeks=offset)
    bin_type_info = get_current_bin_type(test_date)
    return person, bin_type_info

# --- Flask Routes ---
@app.route('/')
def home():
    with app.app_context():
        residents = db.session.query(Resident).order_by(Resident.id).all()
        return render_template_string(HOME_TEMPLATE, residents=residents)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    with app.app_context():
        if request.method == 'POST':
            if 'add_resident' in request.form:
                name = request.form.get('name')
                if name:
                    new_resident = Resident(name=name)
                    db.session.add(new_resident)
                    db.session.commit()
                    flash(f"Resident '{name}' added successfully!")
                else:
                    flash("Name cannot be empty.", "error")
            elif 'remove_resident' in request.form:
                resident_id = request.form.get('resident_id')
                resident_to_delete = db.session.query(Resident).get(resident_id)
                if resident_to_delete:
                    db.session.delete(resident_to_delete)
                    state = db.session.query(AppState).first()
                    if state:
                        state.last_person_index = -1
                    db.session.commit()
                    flash(f"Resident '{resident_to_delete.name}' removed successfully!")
                else:
                    flash("Resident not found.", "error")
            elif 'clear_residents' in request.form:
                db.session.query(Resident).delete()
                db.session.query(AppState).delete()
                db.session.commit()
                flash("All residents and app state cleared.")

        residents = db.session.query(Resident).order_by(Resident.id).all()
        return render_template_string(SETUP_TEMPLATE, residents=residents)

@app.route('/schedule')
def schedule():
    with app.app_context():
        residents = db.session.query(Resident).order_by(Resident.id).all()
        schedule_data = []

        if residents:
            num_weeks = request.args.get('weeks', 4, type=int)
            last_person_index = -1
            state = db.session.query(AppState).first()
            if state:
                last_person_index = state.last_person_index
            start_date = datetime.now(timezone('Europe/London'))
            for i in range(num_weeks):
                next_collection_day = start_date + timedelta(weeks=i)
                days_until_friday = (COLLECTION_DAY - next_collection_day.weekday() + 7) % 7
                next_collection_day += timedelta(days=days_until_friday)
                
                bin_type_info = get_current_bin_type(next_collection_day)
                person_index = (last_person_index + 1 + i) % len(residents)
                person = residents[person_index]

                schedule_data.append({"date": next_collection_day,
                                      "bin_type": bin_type_info['type'],
                                      "person": person.name})
    
    return render_template_string(SCHEDULE_TEMPLATE, schedule=schedule_data, num_weeks=request.args.get('weeks', 4, type=int))

@app.route('/test-reminders')
def test_reminders():
    with app.app_context():
        day_param = request.args.get('day', '').lower()
        offset_param = request.args.get('offset', 0, type=int)
        day_map = {'thursday': 3, 'friday': 4}
        if day_param not in day_map.values():
            return "Invalid day specified. Please use 'thursday' or 'friday'."
        person, bin_type = get_person_for_test(db.session, offset_param)
        if person and bin_type:
            if day_param == 'thursday':
                message = (f"Hello {person.name}! It's your turn to take out the bins. "
                           f"Tomorrow is {bin_type['type']} collection day. "
                           f"Please put the {bin_type['color']} bins out tonight. Thanks!")
            elif day_param == 'friday':
                message = (f"Hey {person.name}, hope your day is going well! "
                           f"Just a friendly reminder to please bring in the {bin_type['color']} bins tonight. Thank you!")
            print(f"Simulated test reminder: {message}")
            return render_template_string(TEST_TEMPLATE, message=message)
        else:
            return "Cannot send test reminders. Please make sure you have added residents on the setup page."

# --- Initial app setup and start scheduler ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=5000, debug=True)
