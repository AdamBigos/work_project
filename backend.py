from flask import Flask, request, jsonify
import requests
import logging
import os
from flask_httpauth import HTTPBasicAuth
from ldap3 import Server, Connection, ALL
from dotenv import load_dotenv

# Load env vars
load_dotenv()

app = Flask(__name__)
auth = HTTPBasicAuth()

# Setup logging
logging.basicConfig(level=logging.INFO, filename='sms_sender.log', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# config
SMS_HUB_API_URL = os.getenv('SMS_HUB_API_URL')
SMS_HUB_API_KEY = os.getenv('SMS_HUB_API_KEY')
LDAP_SERVER = os.getenv('LDAP_SERVER')

# testowy user
users = {
    "admin": "secret"
}

# LDAP Authentication
@auth.verify_password
def verify_password(username, password):
    try:
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=f"{username}@yourdomain.local", password=password)
        if conn.bind():
            logging.info(f"User {username} authenticated via LDAP")
            return username
    except Exception as e:
        logging.error(f"LDAP auth failed for {username}: {str(e)}")
    return None

# SMS sending endpoint
@app.route('/send-sms', methods=['POST'])
@auth.login_required
def send_sms():
    data = request.json
    number = data.get('number')
    message = data.get('message')

    if not number or not message:
        return jsonify({"error": "Number and message required"}), 400

    payload = {
        "to": number,
        "message": message,
        "apikey": SMS_HUB_API_KEY
    }

    try:
        response = requests.post(SMS_HUB_API_URL, json=payload)
        response.raise_for_status()
        logging.info(f"{auth.current_user()} sent SMS to {number}: {message}")
        return jsonify({"status": "sent", "response": response.json()})
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send SMS: {str(e)}")
        return jsonify({"error": "SMS sending failed"}), 500

if __name__ == '__main__':
    app.run(debug=True)
