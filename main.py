import os
import google.generativeai as genai
from serpapi import GoogleSearch
from supabase import create_client, Client
import json
from dotenv import load_dotenv
from datetime import datetime

# --- KEYWORD-BASED ANALYSIS VERSION ---

def log(message):
    """Prints a message with a timestamp."""
    print(f"[{datetime.utcnow().isoformat()}] {message}")

load_dotenv()
log("Starting agent execution...")

# --- CONFIGURATION ---
log("Loading configuration...")
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# NOTE: GEMINI_API_KEY is no longer checked as it's not used in this version.
if not all([SERPAPI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    log("FATAL ERROR: Environment variables are missing.")
else:
    log("All required environment variables loaded.")

# --- Supabase Client ---
supabase: Client = None
try:
    log("Initializing Supabase client...")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    log("Supabase client initialized successfully.")
except Exception as e:
    log(f"CRITICAL ERROR initializing Supabase: {e}")

# --- AGENT 1: PROSPECTOR ---
def find_business_leads(query="Plumbers in Austin TX", num_results=20):
    log(f"Prospector: Searching for '{query}'...")
    if not SERPAPI_API_KEY:
        log("Prospector: ERROR - SerpApi key is missing.")
        return []
        
    search_params = {
        "engine": "google_local", "q": query, "api_key": SERPAPI_API_KEY, "num": num_results
    }
    
    try:
        search = GoogleSearch(search_params)
        results = search.get_dict()
        local_results = results.get("local_results", [])
        
        if not local_results:
            log(f"Prospector: WARNING - Search returned ZERO local results.")
        else:
            log(f"Prospector: SUCCESS - Found {len(local_results)} leads.")
        return local_results

    except Exception as e:
        log(f"Prospector: ERROR during SerpApi call: {e}")
        return []

def get_business_reviews(place_id):
    log(f"Prospector: Simulating review fetch for place_id {place_id[:15]}...")
    # This simulated review contains keywords our new Analyst will look for.
    return "Communication was poor. I had to call them three times to get a quote, and no one seemed to know what was going on. They never called me back after the first message. Frustrating experience trying to get an appointment."

# --- AGENT 2: ANALYST (KEYWORD-BASED - NO AI REQUIRED) ---
def analyze_opportunity(business_name, reviews_text):
    log(f"Analyst: Analyzing '{business_name}' with keyword matching (NO AI)...")
    
    # Define keywords and their point values. Higher points for stronger "pain" signals.
    keywords = {
        'call back': 3, 'callback': 3, 'never called': 4, 'no call': 2,
        'communication': 2, 'no response': 4, 'unreachable': 3, 'unresponsive': 3,
        'scheduling': 2, 'appointment': 1, 'no show': 4, 'follow-up': 2,
        'phone': 1, 'answer': 1, 'reach': 1, 'contact': 1, 'quote': 2
    }
    
    score = 0
    pain_points_found = []
    reviews_lower = reviews_text.lower()
    
    for keyword, points in keywords.items():
        if keyword in reviews_lower:
            score += points
            # Use the keyword itself as the pain point
            if keyword not in pain_points_found:
                 pain_points_found.append(keyword)
    
    # Cap the score at 10 to keep it consistent.
    final_score = min(score, 10)
    
    # If no keywords are found, we can assign a neutral score or skip, but a neutral score is better for testing.
    if final_score == 0:
        final_score = 3 # Assign a low score if no keywords are found
        summary = "No specific communication pain points found via keywords."
    else:
        summary = f"Found {len(pain_points_found)} communication-related issues via keywords."
    
    analysis_result = {
        "opportunity_score": final_score,
        "pain_points": pain_points_found[:3], # Return up to 3 found pain points
        "summary": summary
    }
    
    log(f"Analyst: SUCCESS - Keyword analysis complete. Score: {analysis_result['opportunity_score']}")
    return analysis_result


# --- DATABASE LOGIC ---
def save_lead(business_name, rating, review_count, analysis):
    log(f"Database: Preparing to save lead '{business_name}'...")
    if not supabase:
        log("Database: ERROR - Supabase client is offline.")
        return
    if not analysis:
        log("Database: WARNING - Analysis was empty. Skipping save.")
        return

    try:
        data_to_insert = {
            "business_name": business_name,
            "rating": rating if rating is not None else 0.0,
            "review_count": review_count if review_count is not None else 0,
            "opportunity_score": analysis.get('opportunity_score', 0),
            "pain_points": ", ".join(analysis.get('pain_points', [])),
            "summary": analysis.get('summary', '')
        }
        
        log(f"Database: Attempting to insert: {data_to_insert}")
        result = supabase.table('leads').insert(data_to_insert).execute()
        log(f"Database: SUCCESS - Lead '{business_name}' saved.")
        
    except Exception as e:
        log(f"Database: CRITICAL ERROR saving to Supabase. Reason: {e}")

# --- MAIN ORCHESTRATOR ---
if __name__ == "__main__":
    log("Orchestrator: Main process started.")
    
    if supabase is None:
        log("Orchestrator: Aborting run, Supabase not connected.")
    else:
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

                review_text_summary = get_business_reviews(place_id) 
                ai_analysis = analyze_opportunity(business_name, review_text_summary)
                save_lead(business_name, rating, reviews_count, ai_analysis)
                log(f"--- Finished Lead #{i+1} ---")
        else:
            log("Orchestrator: No business leads were found to process.")

    log("Orchestrator: Main process finished.")
