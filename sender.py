# --- main_sender.py (BREVO VERSION) ---
from datetime import datetime
from database import get_supabase_client
from sender import send_email

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def run_sender_workflow():
    """Sends all pending emails from the outreach_queue using Brevo."""
    log("="*60)
    log("SENDER ORCHESTRATOR: Waking up...")
    log("="*60)
    
    supabase = get_supabase_client()
    if not supabase:
        log("FATAL ERROR: Cannot connect to Supabase. Aborting.")
        return
    
    try:
        log("Fetching pending emails from outreach_queue...")
        
        # Get up to 50 pending emails (Brevo free tier allows 300/day)
        response = supabase.table('outreach_queue').select('*').eq('status', 'pending').limit(50).execute()
        
        pending_emails = response.data
        
        if not pending_emails:
            log("No pending emails found. Nothing to send today.")
            return
        
        log(f"Found {len(pending_emails)} email(s) to send.")
        log("")
        
        sent_count = 0
        failed_count = 0
        
        for email_data in pending_emails:
            email_id = email_data.get('id')
            to_email = email_data.get('recipient_email')
            to_name = email_data.get('business_name')
            subject = email_data.get('email_subject')
            body = email_data.get('email_body')
            
            log(f"Sending email {sent_count + failed_count + 1}/{len(pending_emails)}...")
            
            if send_email(to_email, to_name, subject, body):
                # Mark as sent
                supabase.table('outreach_queue').update({
                    'status': 'sent',
                    'sent_at': datetime.utcnow().isoformat()
                }).eq('id', email_id).execute()
                sent_count += 1
            else:
                # Mark as failed
                supabase.table('outreach_queue').update({
                    'status': 'failed'
                }).eq('id', email_id).execute()
                failed_count += 1
            
            log("")  # Blank line for readability
        
        log("="*60)
        log(f"SENDER ORCHESTRATOR: Complete.")
        log(f"    Sent: {sent_count}")
        log(f"    Failed: {failed_count}")
        log("="*60)
    
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        import traceback
        log(f"Full traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    run_sender_workflow()
