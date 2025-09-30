import os
import google.generativeai as genai
from serpapi import GoogleSearch
from supabase import create_client, Client
import json
from dotenv import load_dotenv

# --- Enhanced Logging Version ---

# This function helps us print clear, timestamped logs
from datetime import datetime
def log(message):
    """Prints a message with a timestamp."""
    print(f"[{datetime.utcnow().isoformat()}] {message}")


# Load environment variables from a .env file (for local development)
load_dotenv()
log("Starting agent execution...")

# --- CONFIGURATION ---
log("Loading configuration from environment variables...")
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Basic configuration validation
if not all([SERPAPI_API_KEY, GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    log("FATAL ERROR: One or more required environment variables are missing.")
else:
    log("All required environment variables are loaded.")

# --- Supabase Client Initialization ---
supabase: Client = None # Initialize to None
try:
    log("Initializing Supabase client...")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    log("Supabase client initialized successfully.")
except Exception as e:
    log(f"CRITICAL ERROR: Failed to initialize Supabase client. Reason: {e}")


# --- AGENT 1: PROSPECTOR ---
def find_business_leads(query="HVAC service in Charlotte NC", num_results=3):
    """Finds business leads using Google Local Search."""
    log(f"Prospector Agent: Preparing to search for '{query}'...")
    if not SERPAPI_API_KEY:
        log("Prospector Agent: ERROR - SerpApi key is missing.")
        return []
        
    search_params = {
        "engine": "google_local",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": num_results
    }
    
    try:
        search = GoogleSearch(search_params)
        results = search.get_dict()
        local_results = results.get("local_results", [])
        
        if not local_results:
            log(f"Prospector Agent: WARNING - Search for '{query}' returned ZERO local results. This could be a valid result or an issue with the query/API key.")
        else:
            log(f"Prospector Agent: SUCCESS - Found {len(local_results)} leads.")
        
        return local_results

    except Exception as e:
        log(f"Prospector Agent: ERROR during API call to SerpApi. Reason: {e}")
        return [] # Return an empty list on error

def get_business_reviews(place_id):
    """Simulates getting reviews for a business."""
    log(f"Prospector Agent: Simulating review fetch for place_id {place_id[:15]}...")
    return "The service was okay, but when I called back with a question, no one answered the phone. Had to call three times to get a follow-up scheduled. Very frustrating communication."

# --- AGENT 2: ANALYST ---
def analyze_opportunity(business_name, reviews_text):
    """Analyzes reviews using Gemini."""
    log(f"Analyst Agent: Preparing to analyze opportunity for '{business_name}'...")
    if not GEMINI_API_KEY:
        log("Analyst Agent: ERROR - Gemini API key is missing.")
        return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Analyze the following reviews for the company "{business_name}".
        Identify pain points related to lead management, callbacks, scheduling, and communication.
        Provide ONLY a JSON object with:
        - "opportunity_score": An integer from 1 to 10.
        - "pain_points": A Python list of short strings.
        - "summary": A one-sentence explanation.
        REVIEWS: "{reviews_text}"
        """
        
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        analysis = json.loads(json_text)
        log(f"Analyst Agent: SUCCESS - Analysis complete. Score: {analysis.get('opportunity_score')}")
        return analysis

    except Exception as e:
        log(f"Analyst Agent: ERROR during AI analysis with Gemini. Reason: {e}")
        return None

# --- DATABASE LOGIC ---
def save_lead(business_name, rating, review_count, analysis):
    """Saves the analyzed lead to Supabase."""
    log(f"Database Module: Preparing to save lead '{business_name}'...")
    if not supabase:
        log("Database Module: ERROR - Supabase client is not initialized. Cannot save.")
        return
    if not analysis:
        log("Database Module: WARNING - Analysis from Analyst Agent was empty. Skipping save.")
        return

    try:
        data_to_insert = {
            "business_name": business_name,
            "rating": rating,
            "review_count": review_count,
            "opportunity_score": analysis['opportunity_score'],
            "pain_points": ", ".join(analysis['pain_points']),
            "summary": analysis['summary']
        }
        
        log(f"Database Module: Attempting to insert: {data_to_insert}")
        response = supabase.table('leads').insert(data_to_insert).execute()
        
        log(f"Database Module: SUCCESS - Supabase insert operation completed.")
        
    except Exception as e:
        log(f"Database Module: CRITICAL ERROR saving lead to Supabase. Reason: {e}")


# --- THE MAIN ORCHESTRATOR ---
if __name__ == "__main__":
    log("Orchestrator: Main process started.")
    
    business_leads = find_business_leads()

    if business_leads:
        log(f"Orchestrator: Processing {len(business_leads)} found leads...")
        for i, lead in enumerate(business_leads):
            log(f"--- Processing Lead #{i+1} ---")
            business_name = lead.get('title')
            
            if not business_name:
                log("Orchestrator: WARNING - Lead has no title. Skipping.")
                continue

            log(f"Orchestrator: Current lead -> {business_name}")
            place_id = lead.get('place_id', 'N/A')
            rating = lead.get('rating')
            reviews_count = lead.get('reviews')

            review_text_summary = get_business_reviews(place_id) 

            ai_analysis = analyze_opportunity(business_name, review_text_summary)
            
            save_lead(business_name, rating, reviews_count, ai_analysis)
            log(f"--- Finished Processing Lead #{i+1} ---")
    else:
        log("Orchestrator: No business leads were found to process. This could be a normal result or an API issue.")

    log("Orchestrator: Main process finished. Agent shutting down.")
