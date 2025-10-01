# --- main_communicator.py (FINAL, ROBUST VERSION) ---

from datetime import datetime
import os
from dotenv import load_dotenv

# We will import the tools directly instead of just the client
from supabase import create_client, Client
from communicator import generate_outreach_email_from_template

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# --- Direct Configuration ---
load_dotenv()
log("Communicator Orchestrator: Loading configuration...")
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def initialize_supabase_client():
    """Directly initializes and returns a Supabase client."""
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        try:
            log("Attempting to initialize Supabase client...")
            client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            log("Direct Supabase client initialization successful.")
            return client
        except Exception as e:
            log(f"CRITICAL ERROR: Failed to create Supabase client: {e}")
            return None
    else:
        log("CRITICAL ERROR: Supabase URL or Service Key missing.")
        return None

def run_communicator_workflow():
    log("Communicator Orchestrator: Main process started.")
    
    supabase = initialize_supabase_client()
    if not supabase:
        log("Orchestrator: Aborting run, Supabase client failed to initialize.")
        return

    try:
        log("Communicator: Preparing to query for new leads with status 'new'...")
        
        # This is the query that will find the work.
        response = supabase.table('leads').select('id, business_name, pain_points').eq('status', 'new').limit(5).execute()
        
        # --- NEW DEBUGGING STEP ---
        log(f"Communicator: Supabase query executed. Full response data: {response.data}")

        if response.data and isinstance(response.data, list):
            new_leads = response.data
            log(f"Communicator: SUCCESS - Found {len(new_leads)} new leads to process.")

            for lead in new_leads:
                lead_id = lead.get('id')
                business_name = lead.get('business_name')
                pain_points = lead.get('pain_points')

                if not all([lead_id, business_name, pain_points]):
                    log(f"WARNING: Skipping lead with missing data: {lead}")
                    continue

                log(f"--- Processing lead: {business_name} (ID: {lead_id}) ---")

                subject, body = generate_outreach_email_from_template(business_name, pain_points)

                if subject and body:
                    log("Communicator: Saving generated email to the outreach_queue...")
                    outreach_data = {
                        'lead_id': lead_id, 'business_name': business_name,
                        'email_subject': subject, 'email_body': body,
                        'recipient_email': f"{business_name.lower().replace(' ', '')}@example.com"
                    }
                    supabase.table('outreach_queue').insert(outreach_data).execute()
                    log("Communicator: Email successfully saved to queue.")

                    log("Communicator: Updating lead status to 'contacted'...")
                    supabase.table('leads').update({'status': 'contacted'}).eq('id', lead_id).execute()
                    log("Communicator: Lead status updated.")
                else:
                    log(f"Communicator: Failed to generate email for {business_name}. Skipping.")

                log(f"--- Finished processing lead: {business_name} ---")
        else:
            log("Communicator: No new leads found in the database response. Workflow complete.")

    except Exception as e:
        log(f"Communicator: CRITICAL ERROR during workflow: {e}")
        import traceback
        log(f"Full traceback: {traceback.format_exc()}")

    log("Communicator Orchestrator: Main process finished.")

if __name__ == "__main__":
    run_communicator_workflow()
