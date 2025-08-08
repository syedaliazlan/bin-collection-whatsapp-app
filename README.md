# WhatsApp Bin Collection Reminder App

This is a Python Flask application designed to automate bin collection reminders for a shared household using the GreenAPI for WhatsApp. The app manages a rotation of residents, sends automated reminders to the responsible person on the day before and the day of collection, and provides a web interface to manage residents and view the upcoming schedule.

## Features

- **Automated WhatsApp Reminders**: Sends a message to a designated WhatsApp group to remind the responsible person to put the bins out.
- **Fair Resident Rotation**: Automatically cycles through a list of residents to ensure everyone takes a turn.
- **Persistent State**: Uses a PostgreSQL database to store the list of residents and the current rotation state, so the app can be restarted without losing track.
- **Web Interface**: A simple Flask web interface to add, remove, and view residents.
- **Dynamic Schedule Overview**: View the upcoming bin collection schedule for any number of weeks.
- **Easy Local Testing**: A dedicated test endpoint to manually trigger reminders and verify the rotation logic without affecting the live schedule.

## Prerequisites

Before running this application, you will need:

- Python 3.x
- A PostgreSQL database (for production deployment, a local SQLite database can be used for development)
- A GreenAPI account with an Instance ID and API Token
- A WhatsApp group chat ID where the reminders will be sent

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/bin-collection-app.git
cd bin-collection-app
```

### 2. Set up a Python Virtual Environment

It's highly recommended to use a virtual environment to manage your project dependencies.

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

> **Note:** For local testing, you can use a SQLite database by setting `DATABASE_URL` to `sqlite:///bin_collection_app.db`.

### 5. Run the Application

```bash
python app.py
```

The application will start on [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Usage

### Web Interface

- **Home Page** (`/`): Displays a list of the current residents.
- **Setup Page** (`/setup`): Add and remove residents, or clear all data.
- **Schedule Page** (`/schedule`): View the upcoming bin collection schedule. Add `?weeks=<number>` to preview more weeks.

### Testing Reminders

Test without sending real WhatsApp messages:

```
/test-reminders?day=thursday
/test-reminders?day=thursday&offset=1
/test-reminders?day=friday
```

The `offset` parameter lets you test any future week.

## Deployment

This application can be deployed to services like Render. Ensure environment variables are set and a production-ready PostgreSQL database is used. See Render's documentation for details.
