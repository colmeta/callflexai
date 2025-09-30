import os
import google.generativeai as genai
from serpapi import GoogleSearch
from supabase import create_client, Client
import json
from dotenv import load_dotenv
from datetime import datetime

# --- FINAL DIAGNOSTIC LOGGING ---

def log(message):
    """Prints a message with a timestamp."""
    print(f"[{datetime.utcnow().isoformat()}] {message}")

load_dotenv()
log("Starting agent execution...")

# --- CONFIGURATION ---
log("Loading configuration...")
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not all([SERPAPI_API_KEY, GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    log("FATAL ERROR: Environment variables are missing.")
else:
    log("All environment variables loaded.")

# --- Supabase Client ---
supabase: Client = None
try:
    log("Initializing Supabase client...")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    log("Supabase client initialized successfully.")
except Exception as e:
    log(f"CRITICAL ERROR initializing Supabase: {e}")

# --- AGENT 1: PROSPECTOR ---
def find_business_leads(query="Plumbers in Austin TX", num_results=5):
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
            log(f"Prospector: Full API Response: {results.get('search_information', {}).get('local_results_state', 'No state info')}")
        else:
            log(f"Prospector: SUCCESS - Found {len(local_results)} leads.")
        return local_results

    except Exception as e:
        log(f"Prospector: ERROR during SerpApi call: {e}")
        return []

def get_business_reviews(place_id):
    log(f"Prospector: Simulating review fetch for place_id {place_id[:15]}...")
    return "Communication was poor. I had to call them three times to get a quote, and no one seemed to know what was going on. Frustrating experience trying to give them my business."

# --- AGENT 2: ANALYST ---
def analyze_opportunity(business_name, reviews_text):
    log(f"Analyst: Preparing to analyze '{business_name}'...")
    if not GEMINI_API_KEY:
        log("Analyst: ERROR - Gemini API key is missing.")
        return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Using the latest recommended model for this task
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = f"""
        Analyze reviews for "{business_name}".
        Pain points should be related to callbacks, scheduling, and communication.
        Provide ONLY a JSON object with "opportunity_score" (1-10), "pain_points" (list of strings), and "summary" (one sentence).
        REVIEWS: "{reviews_text}"
        """
        
        response = model.generate_content(prompt)
        
        # --- THIS IS THE NEW CRITICAL LOGGING STEP ---
        raw_text_output = response.text
        log(f"Analyst: RAW AI Output received:\n---\n{raw_text_output}\n---")
        
        # Clean the raw text before trying to parse it
        cleaned_text = raw_text_output.strip().replace('```json', '').replace('```', '').strip()
        
        analysis = json.loads(cleaned_text)
        log(f"Analyst: SUCCESS - JSON Parsed. Score: {analysis.get('opportunity_score')}")
        return analysis

    except json.JSONDecodeError as e:
        log(f"Analyst: CRITICAL JSON PARSING ERROR. The AI output was not valid JSON. Reason: {e}")
        return None
    except Exception as e:
        log(f"Analyst: CRITICAL GEMINI API ERROR. Check API Key, Billing, and Permissions. Reason: {e}")
        return None

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
            "business_name": business_name, "rating": rating, "review_count": review_count,
            "opportunity_score": analysis['opportunity_score'],
            "pain_points": ", ".join(analysis['pain_points']), "summary": analysis['summary']
        }
        
        log(f"Database: Attempting to insert: {data_to_insert}")
        supabase.table('leads').insert(data_to_insert).execute()
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
