# --- main_lead_delivery.py (FIXED IMPORTS) ---

from datetime import datetime
import sys

# FIXED: Add modules path BEFORE importing
sys.path.append('./modules/service_business')

from database import get_supabase_client
from modules.service_business.sender import send_email

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def generate_lead_briefing_email(client_name, leads):
    """
    Creates a beautiful email with all the hot leads for a client.
    
    Args:
        client_name (str): Client's business name
        leads (list): List of prospect_leads from database
    
    Returns:
        tuple: (subject, body)
    """
    subject = f"🔥 {len(leads)} Hot Lead(s) for {client_name} - {datetime.now().strftime('%B %d')}"
    
    # Build the email body
    body = f"""Good morning!

Your CallFlex AI system found {len(leads)} qualified lead(s) ready for you to contact today:

"""
    
    for idx, lead in enumerate(leads, 1):
        body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEAD #{idx}: {lead.get('prospect_name', 'Unknown')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Contact: {lead.get('prospect_email', 'N/A')} | {lead.get('prospect_phone', 'N/A')}
Needs: {lead.get('service_needed', 'N/A')}
Quality Score: {lead.get('quality_score', 0)}/10
Source: {lead.get('source', 'N/A')}

Context:
{lead.get('notes', 'No additional notes')}

View original post: {lead.get('source_url', 'N/A')}

RECOMMENDED ACTION:
→ Call/email them within the next 2 hours for best conversion
→ Mention you saw their inquiry and have availability this week

"""
    
    body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Your Stats This Week:
   • Total leads delivered: {len(leads)}
   • Average quality score: {sum(l.get('quality_score', 0) for l in leads) // len(leads)}/10
   
💡 Pro Tip: Respond to leads with a quality score of 8+ first. They're the most likely to convert.

Questions? Reply to this email or call me: +256-XXX-XXXXXX

Best,
Collin
Founder, CallFlex AI
"""
    
    return subject, body

def deliver_leads_to_client(client):
    """
    Finds all new prospect leads for a client and emails them.
    
    Args:
        client (dict): Client data from database
    """
    client_id = client['id']
    client_name = client['business_name']
    client_email = client['contact_email']
    
    log(f"Lead Delivery: Processing {client_name}...")
    
    supabase = get_supabase_client()
    if not supabase:
        log("ERROR: Cannot connect to database.")
        return
    
    try:
        # Get all new leads for this client
        response = supabase.table('prospect_leads').select('*').eq('client_id', client_id).eq('status', 'new').order('quality_score', desc=True).execute()
        
        new_leads = response.data
        
        if not new_leads:
            log(f"Lead Delivery: No new leads for {client_name} today.")
            return
        
        log(f"Lead Delivery: Found {len(new_leads)} new lead(s) for {client_name}")
        
        # Generate email
        subject, body = generate_lead_briefing_email(client_name, new_leads)
        
        # Send email to client
        if send_email(
            to_email=client_email,
            to_name=client_name,
            subject=subject,
            body=body
        ):
            log(f"✅ Lead briefing sent to {client_name}")
            
            # Mark all leads as 'delivered'
            lead_ids = [lead['id'] for lead in new_leads]
            supabase.table('prospect_leads').update({
                'status': 'delivered',
                'contacted_at': datetime.utcnow().isoformat()
            }).in_('id', lead_ids).execute()
            
            log(f"✅ Marked {len(lead_ids)} leads as delivered")
        else:
            log(f"❌ Failed to send email to {client_name}")
    
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())

def run_lead_delivery_workflow():
    """
    Main orchestrator: Delivers leads to ALL active clients.
    This runs once per day (e.g., 8 AM their local time).
    """
    log("="*60)
    log("LEAD DELIVERY ORCHESTRATOR: Starting daily briefing...")
    log("="*60)
    
    supabase = get_supabase_client()
    if not supabase:
        log("FATAL: Cannot connect to database.")
        return
    
    try:
        # Get all active clients
        response = supabase.table('clients').select('*').in_('subscription_status', ['active', 'trialing']).execute()
        
        active_clients = response.data
        
        if not active_clients:
            log("No active clients found.")
            return
        
        log(f"Found {len(active_clients)} active client(s)")
        log("")
        
        for idx, client in enumerate(active_clients, 1):
            log(f"Processing client {idx}/{len(active_clients)}: {client['business_name']}")
            deliver_leads_to_client(client)
            log("")
        
        log("="*60)
        log("LEAD DELIVERY: All briefings sent successfully")
        log("="*60)
    
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    run_lead_delivery_workflow()
