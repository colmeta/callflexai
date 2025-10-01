# --- main_communicator.py ---
# This orchestrator finds new leads and queues outreach for them.

from datetime import datetime
from database import get_supabase_client
from communicator import generate_outreach_email_from_template

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def run_communicator_workflow():
    log("Communicator Orchestrator: Main process started.")
    
    supabase = get_supabase_client()
    if not supabase:
        log("Orchestrator: Aborting run, Supabase not connected.")
        return

    try:
        # 1. Fetch new leads from the database that need to be contacted.
        log("Communicator: Searching for new leads with status 'new'...")
        response = supabase.table('leads').select('id, business_name, pain_points').eq('status', 'new').limit(5).execute()
        
        new_leads = response.data
        if not new_leads:
            log("Communicator: No new leads to process. Workflow complete.")
            return

        log(f"Communicator: Found {len(new_leads)} new leads to process.")

        for lead in new_leads:
            business_name = lead['business_name']
            pain_points = lead['pain_points']
            log(f"--- Processing lead: {business_name} (ID: {lead_id}) ---")

            # 2. Generate a personalized email for this lead.
            subject, body = generate_outreach_email_from_template(business_name, pain_points)

            if subject and body:
                # 3. Save the generated email to our 'outreach_queue' table.
                log(f"Communicator: Saving generated email to the outreach_queue...")
                outreach_data = {
                    'lead_id': lead_id,
                    'business_name': business_name,
                    'email_subject': subject,
                    'email_body': body,
                    'recipient_email': 'test@example.com' # Placeholder for now
                }
                supabase.table('outreach_queue').insert(outreach_data).execute()
                log("Communicator: Email successfully saved to queue.")

                # 4. CRITICAL: Update the lead's status to prevent re-contacting.
                log("Communicator: Updating lead status to 'contacted'...")
                supabase.table('leads').update({'status': 'contacted'}).eq('id', lead_id).execute()
                log("Communicator: Lead status updated.")
            else:
                log(f"Communicator: Failed to generate email for {business_name}. Skipping.")

            log(f"--- Finished processing lead: {business_name} ---")

    except Exception as e:
        log(f"Communicator: A critical error occurred during the workflow: {e}")

    log("Communicator Orchestrator: Main process finished.")

if __name__ == "__main__":
    run_communicator_workflow()
