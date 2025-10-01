# --- main.py (The Orchestrator) ---
# This script manages the overall workflow, using the specialized modules.

from datetime import datetime
# Import our custom modules
from database import get_supabase_client
from prospector import find_business_leads, get_business_reviews
from analyst import analyze_opportunity_with_keywords

def log(message):
    """Prints a message with a timestamp."""
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# --- DATABASE LOGIC ---
def save_lead(supabase_client, business_name, rating, review_count, analysis):
    log(f"Database Module: Preparing to save lead '{business_name}'...")
    if not supabase_client:
        log("Database Module: ERROR - Supabase client is offline.")
        return
    if not analysis:
        log("Database Module: WARNING - Analysis was empty. Skipping save.")
        return

    try:
        data_to_insert = {
            "business_name": business_name,
            "rating": rating if rating is not None else 0.0,
            "review_count": review_count if review_count is not None else 0,
            "opportunity_score": analysis.get('opportunity_score', 0),
                    "pain_points": ", ".join(analysis.get('pain_points', [])),
        "summary": analysis.get('summary', ''),
        "status": "new"  # ✅ The line that fixes everything.
    }
```4.  Optionally, for better logging, find this line:
`log(f"Database Module: SUCCESS - Lead '{business_name}' saved.")`
And change it to what you suggested:
`log(f"Database Module: SUCCESS - Lead '{business_name}' saved with status='new'.")`
        
        log(f"Database Module: Attempting to insert: {data_to_insert}")
        result = supabase_client.table('leads').insert(data_to_insert).execute()
        log(f"Database Module: SUCCESS - Lead '{business_name}' saved.")
        
    except Exception as e:
        log(f"Database Module: CRITICAL ERROR saving to Supabase. Reason: {e}")

# --- MAIN WORKFLOW ---
def run_agent_workflow():
    log("Orchestrator: Main process started.")
    
    supabase_client = get_supabase_client()
    if supabase_client is None:
        log("Orchestrator: Aborting run, Supabase not connected.")
        return

    business_leads = find_business_leads()

    if business_leads:
        log(f"Orchestrator: Processing {len(business_leads)} found leads...")
        for i, lead in enumerate(business_leads):
            log(f"--- Processing Lead #{i+1} ---")
            business_name = lead.get('title')
            
            if not business_name:
                log("Orchestrator: WARNING - Skipping lead with no title.")
                continue

            log(f"Orchestrator: Current lead -> {business_name}")
            place_id = lead.get('place_id', 'N/A')
            rating = lead.get('rating')
            reviews_count = lead.get('reviews')

            # Step 1: Prospector gets the reviews
            review_text_summary = get_business_reviews(place_id) 
            
            # Step 2: Analyst scores the opportunity
            analysis = analyze_opportunity_with_keywords(business_name, review_text_summary)
            
            # Step 3: Database module saves the final result
            save_lead(supabase_client, business_name, rating, reviews_count, analysis)
            log(f"--- Finished Lead #{i+1} ---")
    else:
        log("Orchestrator: No business leads were found to process.")

    log("Orchestrator: Main process finished.")

if __name__ == "__main__":
    run_agent_workflow()
