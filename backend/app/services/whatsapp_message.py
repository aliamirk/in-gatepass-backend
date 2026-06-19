import requests
import json
import os
from datetime import datetime, timedelta

# WhatsApp API credentials
phone_number_id = "866095989922419"
access_token = "EAATJDPXxzGEBQKAhz7AJdBji1n03HNDP8q5EHFlYrRVi8YiXkZCWPlS47kIh4YkBC9Iwn10QST7c4YnZAeZAy8fvHDh6AX3Knbe2o4h1A2fX9ZBqfK3WdLvDCCqy80eJKa8JHX6JOVwkmFzNO3vX6USBGxiZBO1o6Kyd5rZALPADjuax7MSJWsE6EtA6H5EYwVQwZDZD"

# WhatsApp Template
TEMPLATE_NAME = "gatepass_alert"  # Replace with your registered template name
TEMPLATE_LANG = "en"         # Replace with the correct language code

# File to track user activity
DATA_FILE = "user_activity.json"

# Recipients (fixed list)
recipients = [
    "923193347800",
    "923462695471",
    "923145040874",
    "923213772697",
    "923219251210",
    "923022299687",
    "923219282273",
    "923192209991",
    "923322590048"
]

# --- Utility functions ---

def load_user_activity():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except (json.JSONDecodeError, ValueError):
        return {}

def save_user_activity(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def handle_incoming_message(from_number):
    """
    Call this when a user sends a message (via webhook) to update last activity.
    """
    activity = load_user_activity()
    activity[from_number] = datetime.now().isoformat()
    save_user_activity(activity)

# --- Main function to send WhatsApp messages ---

def send_whatsapp_messages(message, gatepass_number):
    """
    Sends WhatsApp messages to all recipients.
    Uses template if user hasn't messaged in last 24h, otherwise sends normal text.
    
    Parameters:
        message (str): The message text for normal messages
        gatepass_number (str): The gatepass number to replace {{1}} in the template
    """
    if not gatepass_number:
        print("Error: gatepass_number is empty. Cannot send template.")
        return

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    user_activity = load_user_activity()
    now = datetime.now()

    for number in recipients:
        last_message_str = user_activity.get(number)
        send_template = True

        if last_message_str:
            last_message_time = datetime.fromisoformat(last_message_str)
            if now - last_message_time < timedelta(hours=24):
                send_template = False

        if send_template:
            payload = {
                "messaging_product": "whatsapp",
                "to": number,
                "type": "template",
                "template": {
                    "name": TEMPLATE_NAME,
                    "language": {"code": TEMPLATE_LANG},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": gatepass_number
                                }
                            ]
                        }
                    ]
                }
            }
            response = requests.post(url, json=payload, headers=headers)
            print(f"TEMPLATE sent to {number}: {response.json()}")
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": number,
                "type": "text",
                "text": {"body": message}
            }
            response = requests.post(url, json=payload, headers=headers)
            print(f"Normal message sent to {number}: {response.json()}")

        # Update last activity timestamp
        user_activity[number] = now.isoformat()
        save_user_activity(user_activity)
