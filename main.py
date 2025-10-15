# --- main.py (FLEXIBLE MULTI-TENANT ORCHESTRATOR) ---

from datetime import datetime
from database import get_supabase_client
from prospector import find_business_leads, get_business_reviews
from analyst import analyze_opportunity_with_keywords

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def save_lead(supabase_client, client_id, lead_data, analysis):
    """Saves a single lead to the database, linked to a specific client."""
    log(f"Database: Saving '{lead_data.get('title')}' for client {client_id}...")
    try:
        data_to_insert = {
            "client_id": client_id,
            "business_name": lead_data.get('title'),
            "rating": lead_data.get('rating'),
            "review_count": lead_data.get('reviews'),
            "opportunity_score": analysis.get('opportunity_score'),
            "pain_points": ", ".join(analysis.get('pain_points', [])),
            "summary": analysis.get('summary'),
            "status": "new"
        }
        supabase_client.table('leads').insert(data_to_insert).execute()
        log(f"Database: SUCCESS - Lead saved.")
    except Exception as e:
        log(f"Database: ERROR saving lead: {e}")

def check_if_lead_exists(supabase_client, client_id, business_name):
    """
    Checks if we've already prospected this business for this client.
    This prevents duplicate outreach (idempotency).
    """
    try:
        response = supabase_client.table('leads').select('id').eq('client_id', client_id).eq('business_name', business_name).execute()
        return len(response.data) > 0
    except Exception as e:
        log(f"Database: ERROR checking for duplicates: {e}")
        return False

def run_prospecting_for_client(supabase_client, client):
    """Runs the prospecting workflow for ONE client."""
    client_id = client.get('id')
    client_name = client.get('business_name')
    niche = client.get('prospecting_niche')
    location = client.get('prospecting_location')
    max_leads_per_day = client.get('max_leads_per_day', 20)  # NEW: Configurable limit
    
    # Validate that client has required settings
    if not all([client_id, niche, location]):
        log(f"Orchestrator: SKIPPING {client_name} - Missing niche or location in database.")
        return
    
    log(f"--- STARTING JOB FOR: {client_name} ---")
    log(f"    Target Niche: {niche}")
    log(f"    Target Location: {location}")
    
    # NEW: Dynamic search based on client's settings
    business_leads = find_business_leads(niche=niche, location=location, num_results=20)
    
    if not business_leads:
        log(f"Orchestrator: No leads found for {client_name}.")
        return
    
    log(f"Orchestrator: Found {len(business_leads)} potential leads.")
    
    new_leads_count = 0
    duplicate_leads_count = 0
    
    for lead_data in business_leads:
        business_name = lead_data.get('title')
        if not business_name:
            continue
        
        # Check for duplicates (don't contact the same business twice)
        if check_if_lead_exists(supabase_client, client_id, business_name):
            log(f"Orchestrator: DUPLICATE - '{business_name}' already in database. Skipping.")
            duplicate_leads_count += 1
            continue
        
        # Get reviews and analyze
        review_text = get_business_reviews(lead_data.get('place_id'))
        analysis = analyze_opportunity_with_keywords(business_name, review_text)
        
        # Only save leads with a score above threshold (don't waste time on low-quality)
        if analysis.get('opportunity_score', 0) >= 3:
            save_lead(supabase_client, client_id, lead_data, analysis)
            new_leads_count += 1
        else:
            log(f"Orchestrator: FILTERED - '{business_name}' scored too low ({analysis.get('opportunity_score')}). Skipping.")
    
    log(f"--- JOB COMPLETE FOR: {client_name} ---")
    log(f"    New Leads: {new_leads_count}")
    log(f"    Duplicates Filtered: {duplicate_leads_count}")

def run_master_orchestrator():
    """The master workflow that processes ALL active clients."""
    log("="*60)
    log("MASTER ORCHESTRATOR: Waking up...")
    log("="*60)
    
    supabase_client = get_supabase_client()
    if not supabase_client:
        log("FATAL ERROR: Cannot connect to Supabase. Aborting.")
        return
    
    try:
        log("Fetching all active clients from database...")
        
        # Get all clients who are active or trialing
        response = supabase_client.table('clients').select('*').in_('subscription_status', ['active', 'trialing']).execute()
        
        active_clients = response.data
        
        if not active_clients:
            log("No active clients found. Nothing to do today.")
            return
        
        log(f"Found {len(active_clients)} active client(s) to process.")
        log("")
        
        # Process each client one by one
        for idx, client in enumerate(active_clients, 1):
            log(f"Processing client {idx}/{len(active_clients)}...")
            run_prospecting_for_client(supabase_client, client)
            log("")  # Blank line for readability
        
        log("="*60)
        log("MASTER ORCHESTRATOR: All jobs complete. Shutting down.")
        log("="*60)
    
    except Exception as e:
        log(f"CRITICAL ERROR in master orchestrator: {e}")
        import traceback
        log(f"Full traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    run_master_orchestrator()
