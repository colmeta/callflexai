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
        "engine": "google_maps",  # Changed from google_local to google_maps
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "ll": "@30.267153,-97.7430608,11z",  # Austin, TX coordinates
        "type": "search"
    }
    
    try:
        log(f"Prospector: Sending request to SerpAPI with params: {search_params}")
        search = GoogleSearch(search_params)
        results = search.get_dict()
        
        # Log the full response for debugging
        log(f"Prospector: Full API Response Keys: {list(results.keys())}")
        
        # Try multiple possible result keys
        local_results = (
            results.get("local_results", []) or 
            results.get("organic_results", []) or
            results.get("places_results", []) or
            []
        )
        
        if not local_results:
            log(f"Prospector: WARNING - Search returned ZERO results.")
            log(f"Prospector: API Response: {json.dumps(results, indent=2)[:500]}")  # First 500 chars
            
            # Check for error messages
            if "error" in results:
                log(f"Prospector: API ERROR: {results['error']}")
            if "search_information" in results:
                log(f"Prospector: Search Info: {results['search_information']}")
        else:
            log(f"Prospector: SUCCESS - Found {len(local_results)} leads.")
        
        return local_results

    except Exception as e:
        log(f"Prospector: ERROR during SerpApi call: {e}")
        import traceback
        log(f"Prospector: Full traceback: {traceback.format_exc()}")
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
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Analyze reviews for "{business_name}".
        Pain points should be related to callbacks, scheduling, and communication.
        
        You MUST respond with ONLY a valid JSON object. No markdown, no explanation, no code blocks.
        The JSON must have exactly these fields:
        - "opportunity_score": a number from 1 to 10
        - "pain_points": an array of strings
        - "summary": a single sentence string
        
        REVIEWS: "{reviews_text}"
        
        Response format (respond with ONLY this, nothing else):
        {{"opportunity_score": 8, "pain_points": ["example1", "example2"], "summary": "Brief summary here"}}
        """
        
        response = model.generate_content(prompt)
        raw_text_output = response.text
        log(f"Analyst: RAW AI Output received:\n---\n{raw_text_output}\n---")
        
        # More aggressive cleaning
        cleaned_text = raw_text_output.strip()
        # Remove markdown code blocks
        cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
        # Remove any leading/trailing text before/after JSON object
        if '{' in cleaned_text and '}' in cleaned_text:
            start = cleaned_text.find('{')
            end = cleaned_text.rfind('}') + 1
            cleaned_text = cleaned_text[start:end]
        
        log(f"Analyst: Cleaned text:\n---\n{cleaned_text}\n---")
        
        analysis = json.loads(cleaned_text)
        
        # Validate required fields
        required_fields = ['opportunity_score', 'pain_points', 'summary']
        missing_fields = [field for field in required_fields if field not in analysis]
        
        if missing_fields:
            log(f"Analyst: ERROR - Missing required fields: {missing_fields}")
            return None
        
        log(f"Analyst: SUCCESS - JSON Parsed. Score: {analysis.get('opportunity_score')}")
        return analysis

    except json.JSONDecodeError as e:
        log(f"Analyst: CRITICAL JSON PARSING ERROR. The AI output was not valid JSON.")
        log(f"Analyst: JSON Error Details: {e}")
        log(f"Analyst: Attempted to parse: {cleaned_text}")
        return None
    except Exception as e:
        log(f"Analyst: CRITICAL GEMINI API ERROR. Check API Key, Billing, and Permissions.")
        log(f"Analyst: Error Details: {e}")
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
        # Handle potential None values
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
        log(f"Database: Insert result: {result}")
        
    except Exception as e:
        log(f"Database: CRITICAL ERROR saving to Supabase.")
        log(f"Database: Error type: {type(e).__name__}")
        log(f"Database: Error details: {str(e)}")
        log(f"Database: Data attempted: {data_to_insert}")


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
