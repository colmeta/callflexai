# --- main.py (Multi-Tenant Orchestrator v2.0) ---

from datetime import datetime
from database import get_supabase_client
from prospector import find_business_leads, get_business_reviews
from analyst import analyze_opportunity_with_keywords

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def save_lead(supabase_client, client_id, lead_data, analysis):
    """Saves a single lead to the database, now linked to a client."""
    log(f"Database: Preparing to save '{lead_data.get('title')}' for client {client_id}...")
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
        log(f"Database: SUCCESS - Lead '{lead_data.get('title')}' saved.")
    except Exception as e:
        log(f"Database: CRITICAL ERROR saving lead. Reason: {e}")

def run_prospecting_for_client(supabase_client, client):
    """Runs the entire prospecting workflow for a single client."""
    client_id = client.get('id')
    niche = client.get('prospecting_niche')
    location = client.get('prospecting_location')
    
    if not all([client_id, niche, location]):
        log(f"Orchestrator: WARNING - Skipping client {client.get('business_name')} due to missing config (niche or location).")
        return

    log(f"--- Starting Prospecting Job for Client: {client.get('business_name')} ---")
    query = f"{niche} in {location}"
    
    business_leads = find_business_leads(query=query)

    if business_leads:
        log(f"Orchestrator: Found {len(business_leads)} potential leads for {client.get('business_name')}.")
        for lead_data in business_leads:
            business_name = lead_data.get('title')
            if not business_name:
                log("Orchestrator: WARNING - Skipping a lead with no title.")
                continue

            # In the future, this is where Idempotency check will go
            # pseudo-code: if database.lead_exists(client_id, lead_data['place_id']): continue

            review_text = get_business_reviews(lead_data.get('place_id'))
            analysis = analyze_opportunity_with_keywords(business_name, review_text)
            
            save_lead(supabase_client, client_id, lead_data, analysis)
        log(f"--- Finished Job for Client: {client.get('business_name')} ---")
    else:
        log(f"Orchestrator: No new leads found for {client.get('business_name')}.")

# --- THE NEW MAIN WORKFLOW ---
def run_master_orchestrator():
    log("Master Orchestrator: Waking up...")
    
    supabase_client = get_supabase_client()
    if not supabase_client:
        log("Master Orchestrator: ABORTING - Supabase connection failed.")
        return

    # Step A: Fetch all active clients who get this service
    try:
        log("Master Orchestrator: Fetching all active clients on the 'pro' plan...")
        # Note: In the future, we'll filter by `monthly_plan`. For now, we get all active clients.
        response = supabase_client.table('clients').select('*').in_('subscription_status', ['active', 'trialing']).execute()
        
        active_clients = response.data
        if not active_clients:
            log("Master Orchestrator: No active clients found. Going back to sleep.")
            return

        log(f"Master Orchestrator: Found {len(active_clients)} clients to process.")
        
        # Step B: Loop through each client and run their job
        for client in active_clients:
            run_prospecting_for_client(supabase_client, client)

    except Exception as e:
        log(f"Master Orchestrator: CRITICAL ERROR during client fetch or loop: {e}")

    log("Master Orchestrator: All client jobs complete. Shutting down.")


if __name__ == "__main__":
    run_master_orchestrator()
