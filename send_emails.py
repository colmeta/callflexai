# --- send_emails.py ---
# Sends emails to dentists from the outreach_queue
# Run: python send_emails.py

import os
import sys
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

load_dotenv()

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# ============================================================================
# EMAIL SENDING (Using Brevo - 300 free emails/day)
# ============================================================================

def send_email_via_brevo(to_email: str, to_name: str, subject: str, body: str) -> bool:
    """
    Sends email using Brevo API (free tier: 300 emails/day).
    
    Args:
        to_email: Recipient email
        to_name: Recipient name
        subject: Email subject
        body: Email body
    
    Returns:
        True if sent, False if failed
    """
    BREVO_API_KEY = os.getenv('BREVO_API_KEY')
    
    if not BREVO_API_KEY:
        log("❌ BREVO_API_KEY not found in .env file!")
        log("Get free key at: https://www.brevo.com/")
        return False
    
    # Your sender email (must be verified in Brevo)
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'your-email@example.com')
    FROM_NAME = os.getenv('FROM_NAME', 'Your Name')
    
    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {
            "name": FROM_NAME,
            "email": FROM_EMAIL
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
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            log(f"  ✅ Sent to {to_name} ({to_email})")
            return True
        else:
            log(f"  ❌ Failed: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        log(f"  ❌ Error: {e}")
        return False

# ============================================================================
# BATCH EMAIL SENDER
# ============================================================================

def send_pending_emails(limit: int = 50, test_mode: bool = False):
    """
    Sends all pending emails from outreach_queue.
    
    Args:
        limit: Max emails to send (default 50, max 300/day on free Brevo)
        test_mode: If True, only prints emails without sending
    """
    log("="*70)
    log(f"📧 EMAIL SENDER: {'TEST MODE' if test_mode else 'LIVE MODE'}")
    log("="*70)
    
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Database connection failed")
        return
    
    try:
        # Get pending emails
        log(f"\n🔍 Fetching pending emails (limit: {limit})...")
        
        response = supabase.table('outreach_queue')\
            .select('*')\
            .eq('status', 'pending')\
            .limit(limit)\
            .execute()
        
        pending_emails = response.data
        
        if not pending_emails:
            log("⚠️ No pending emails found")
            log("💡 Run: python email_generator.py first")
            return
        
        log(f"✅ Found {len(pending_emails)} pending emails")
        
        if test_mode:
            log("\n🧪 TEST MODE: Showing first 3 emails (not sending)")
            for i, email in enumerate(pending_emails[:3], 1):
                log(f"\n{'='*70}")
                log(f"EMAIL #{i}: {email['recipient_name']}")
                log(f"{'='*70}")
                log(f"To: {email['recipient_email']}")
                log(f"Subject: {email['email_subject']}")
                log(f"\nBody:\n{email['email_body'][:300]}...")
                log(f"{'='*70}")
            
            log("\n💡 To send for real: python send_emails.py --live")
            return
        
        # Send emails
        log(f"\n📤 Sending {len(pending_emails)} emails...")
        log("⏳ This will take a few minutes (delays to avoid spam filters)\n")
        
        sent = 0
        failed = 0
        
        for i, email in enumerate(pending_emails, 1):
            email_id = email['id']
            to_email = email['recipient_email']
            to_name = email['recipient_name']
            subject = email['email_subject']
            body = email['email_body']
            
            log(f"[{i}/{len(pending_emails)}] Sending to {to_name}...")
            
            # Send email
            success = send_email_via_brevo(to_email, to_name, subject, body)
            
            if success:
                # Update status to 'sent'
                supabase.table('outreach_queue').update({
                    'status': 'sent',
                    'sent_at': datetime.utcnow().isoformat()
                }).eq('id', email_id).execute()
                
                # Update dentist status
                if email.get('dentist_id'):
                    supabase.table('dentists').update({
                        'status': 'contacted',
                        'outreach_attempts': 1,
                        'last_contact_date': datetime.utcnow().isoformat()
                    }).eq('id', email['dentist_id']).execute()
                
                sent += 1
            else:
                # Update status to 'failed'
                supabase.table('outreach_queue').update({
                    'status': 'failed',
                    'send_attempts': email.get('send_attempts', 0) + 1
                }).eq('id', email_id).execute()
                
                failed += 1
            
            # Delay between emails (avoid spam filters)
            if i < len(pending_emails):
                delay = 3  # 3 seconds between emails
                time.sleep(delay)
        
        log(f"\n{'='*70}")
        log(f"📊 RESULTS:")
        log(f"  ✅ Sent: {sent}")
        log(f"  ❌ Failed: {failed}")
        log(f"  📧 Total: {sent + failed}")
        log(f"{'='*70}")
        
        if sent > 0:
            log("\n🎉 SUCCESS! Emails sent to dentists")
            log(f"📊 Check your Brevo dashboard for delivery stats")
            log(f"💌 Replies will go to: {os.getenv('FROM_EMAIL')}")
        
    except Exception as e:
        log(f"❌ Critical error: {e}")
        import traceback
        log(traceback.format_exc())

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Check command line arguments
    test_mode = True  # Default to test mode for safety
    limit = 50
    
    if len(sys.argv) > 1:
        if '--live' in sys.argv or '--send' in sys.argv:
            test_mode = False
        
        # Check for custom limit
        for arg in sys.argv:
            if arg.isdigit():
                limit = int(arg)
    
    if test_mode:
        log("🧪 Running in TEST MODE (safe - won't send emails)")
        log("💡 To send for real: python send_emails.py --live")
        log("")
    
    send_pending_emails(limit=limit, test_mode=test_mode)
