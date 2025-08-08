# WhatsApp Bin Collection Reminder App (Fixed Schedule Version)

This is a Python Flask application designed to automate bin collection reminders for a shared household. This specific version of the app has a fixed, hardcoded schedule: collections are always on Fridays, alternating weekly between General Waste and Recycling.

The app uses a fair resident rotation system and a web interface for easy management. It is designed for seamless and reliable deployment on cloud platforms like Render using a separate cron job for message scheduling.

## Features

- **Fixed Bin Schedule**: The collection schedule is hardcoded for a weekly alternating pattern, with both General Waste and Recycling collected on Fridays.
- **Automated WhatsApp Reminders**: Sends a daily message to the designated WhatsApp group to remind the responsible resident to take the bins out or bring them in.
- **Fair Resident Rotation**: Automatically cycles through a list of residents to ensure everyone takes a turn. The rotation is preserved in the database.
- **Robust Persistence**: Uses a PostgreSQL database to store residents and the app's rotation state.
- **Comprehensive Web Interface**: A simple Flask interface to add, remove, and view residents, and view the upcoming schedule.
- **Dynamic Schedule Overview**: Displays a preview of the upcoming bin collections and who is responsible for each, for a configurable number of weeks.
- **Safe Local Testing**: A dedicated test endpoint to manually trigger the reminder logic for any day or future week without sending actual WhatsApp messages.
- **Production-Ready Deployment**: The application logic is split into a web server (`app.py`) and a cron job script (`run_reminders_fixed.py`) for reliable scheduling on cloud platforms like Render.

## Prerequisites

Before running this application, you will need:

- Python 3.x
- A PostgreSQL database
- A GreenAPI account with an Instance ID and API Token
- A WhatsApp group chat ID where the reminders will be sent

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/bin-collection-app.git
cd bin-collection-app
```

### 2. Set up a Python Virtual Environment
It is highly recommended to use a virtual environment to manage your project dependencies.

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory of your project and add the following variables:

```
GREENAPI_INSTANCE_ID="YOUR_INSTANCE_ID"
GREENAPI_API_TOKEN="YOUR_API_TOKEN"
WHATSAPP_GROUP_CHAT_ID="YOUR_CHAT_ID"
DATABASE_URL="YOUR_RENDER_POSTGRES_DB_URL"
SECRET_KEY=b'a_strong_random_key_here'
```

> **Note:** For local testing, you can use a SQLite database by changing the `DATABASE_URL` to `sqlite:///bin_collection_app.db`.

### 5. Run the Web Server
```bash
python app.py
```
The application will start on [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Usage

### Web Interface
- **Home Page** (`/`): A landing page to welcome you and provide navigation.
- **Setup Page** (`/setup`): Add or remove residents. The bin schedule is fixed and displayed here.
- **Schedule Page** (`/schedule`): View a preview of the upcoming bin collection schedule. You can specify the number of weeks to view by adding a `?weeks=<number>` parameter to the URL (e.g., `/schedule?weeks=52` for a year).

### Local Testing
To test the reminder logic without sending live WhatsApp messages, use the `/test-reminders` endpoint.

**"Take out" reminder (Thursday):**
```
http://127.0.0.1:5000/test-reminders?day=thursday
```

**"Bring in" reminder (Friday):**
```
http://127.0.0.1:5000/test-reminders?day=friday
```

Use the `offset` parameter to test future weeks (e.g., `&offset=1`). The app correctly alternates bin type each week.

## Deployment on Render

This application is designed for a split deployment on Render using two services.

### 1. Web Service
Deploy `app.py` as a standard Render web service to manage residents and view the schedule.

### 2. Cron Jobs
Create two separate Render Cron Jobs to handle automated reminders. Both will run `run_reminders_fixed.py`.

| Job Name           | Schedule (London Time)               | Command                          | Purpose                                 |
|--------------------|---------------------------------------|-----------------------------------|-----------------------------------------|
| take-out-reminder  | Daily at 6:00 PM (e.g., `0 17 * * thu`) | `python run_reminders_fixed.py`  | Sends the reminder to put the bins out |
| bring-in-reminder  | Daily at 7:00 PM (e.g., `0 18 * * fri`) | `python run_reminders_fixed.py`  | Sends the reminder to bring the bins in|

By using two separate cron jobs, reminders are sent at the correct times every day, reliably and independently of your web server.
