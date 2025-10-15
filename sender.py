# --- sender.py (BREVO/SENDINBLUE FREE VERSION) ---
import os
import requests
from dotenv import load_dotenv

load_dotenv()
BREVO_API_KEY = os.getenv('BREVO_API_KEY')

def log(message):
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def send_email(to_email, to_name, subject, body, from_email="collin@yourdomain.com", from_name="Collin from CallFlex AI"):
    """
    Sends an email using Brevo's free API (300 emails/day).
    
    Args:
        to_email (str): Recipient's email
        to_name (str): Recipient's name (e.g., business name)
        subject (str): Email subject line
        body (str): Email body (plain text)
        from_email (str): Your sender email (must be verified in Brevo)
        from_name (str): Your sender name
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    log(f"Sender: Preparing email to {to_email}...")
    
    if not BREVO_API_KEY:
        log("Sender: ERROR - Brevo API key missing.")
        return False
    
    # Brevo API endpoint
    url = "https://api.brevo.com/v3/smtp/email"
    
    # Request headers
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    # Email payload
    payload = {
        "sender": {
            "name": from_name,
            "email": from_email
        },
        "to": [
            {
                "email": to_email,
                "name": to_name
            }
        ],
        "subject": subject,
        "textContent": body
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            log(f"Sender: SUCCESS - Email sent to {to_email}")
            return True
        else:
            log(f"Sender: ERROR - Brevo returned status {response.status_code}: {response.text}")
            return False
    
    except Exception as e:
        log(f"Sender: CRITICAL ERROR: {e}")
        return False

def send_sms(to_phone, message):
    """
    Sends an SMS using Brevo's SMS API (Transactional SMS).
    
    NOTE: Brevo SMS requires purchasing credits (~$0.04/SMS).
    For a FREE alternative, use Discord webhooks or Telegram bot API
    to notify YOUR phone, then you manually call the lead.
    
    Args:
        to_phone (str): Phone number in international format (e.g., "+1234567890")
        message (str): SMS content
    
    Returns:
        bool: True if sent, False otherwise
    """
    log(f"Sender: SMS to {to_phone} - Feature not implemented (requires paid credits).")
    # Uncomment this if you purchase Brevo SMS credits:
    # url = "https://api.brevo.com/v3/transactionalSMS/sms"
    # ...implementation here...
    return False
