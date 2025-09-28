import os
import google.generativeai as genai
from serpapi import GoogleSearch
from supabase import create_client, Client
import json
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
# Secrets for our services. We will set these in Render.
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Create a single Supabase client instance
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("Supabase client initialized successfully.")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase = None

# Set DRY_RUN to True to avoid API calls and database writes for testing
DRY_RUN = False 

# --- AGENT 1: PROSPECTOR (No changes needed here) ---
def find_business_leads(query="plumbers in austin", num_results=5):
    """Finds business leads using Google Local Search."""
    print(f"Prospector: Searching for '{query}'...")
    if DRY_RUN:
        return [{'title': 'Mock Plumbing Inc.', 'place_id': 'mock_id_123', 'reviews': 40, 'rating': 3.5}]
    
    # ... (This function's code is identical to the previous version) ...
    search_params = { "engine": "google_local", "q": query, "api_key": SERPAPI_API_KEY, "num": num_results }
    search = GoogleSearch(search_params)
    results = search.get_dict()
    local_results = results.get("local_results", [])
    print(f"Prospector: Found {len(local_results)} leads.")
    return local_results

def get_business_reviews(place_id):
    """Gets/simulates reviews for a business."""
    # ... (This function's code is also identical) ...
    print(f"Prospector: Fetching reviews for place_id {place_id[:15]}...")
    if DRY_RUN:
        return "Customers complain about slow service and no one ever calling them back. One person said 'I called three times and never got a quote!'."
    return "Customers complain about high prices and poor communication. 'They never called me back to confirm the appointment.' 'Waited all day, no show no call'."

# --- AGENT 2: ANALYST (No changes needed here) ---
def analyze_opportunity(business_name, reviews_text):
    """Analyzes reviews using Gemini to find callback/CRM weaknesses."""
    # ... (This function's code is also identical) ...
    print(f"Analyst: Analyzing opportunity for '{business_name}'...")
    if DRY_RUN:
        return {"opportunity_score": 8, "pain_points": ["No one calls back", "Terrible follow-up"], "summary": "High potential."}
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    You are a business analyst identifying operational weaknesses in companies based on reviews.
    Analyze the following for "{business_name}":
    
    REVIEWS: "{reviews_text}"
    
    Provide a JSON object with: "opportunity_score" (1-10), "pain_points" (list of strings), and "summary" (one sentence).
    Provide ONLY the JSON object.
    """
    
    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace('```json', '').replace('```', '')
        analysis = json.loads(json_text)
        print(f"Analyst: Analysis complete. Opportunity score: {analysis.get('opportunity_score')}")
        return analysis
    except Exception as e:
        print(f"Analyst: Error during AI analysis - {e}")
        return None


# --- DATABASE LOGIC (UPGRADED for Supabase) ---
def save_lead(business_name, rating, review_count, analysis):
    """Saves the analyzed lead to the Supabase database. Cleaner and simpler!"""
    print(f"Database: Saving lead '{business_name}' to Supabase...")
    if DRY_RUN or not analysis or not supabase:
        print("Database: DRY RUN or client not initialized. Skipping save.")
        return

    try:
        data_to_insert = {
            "business_name": business_name,
            "rating": rating,
            "review_count": review_count,
            "opportunity_score": analysis['opportunity_score'],
            "pain_points": ", ".join(analysis['pain_points']), # Store list as a comma-separated string
            "summary": analysis['summary']
        }
        
        # This is the magic! So much cleaner than before.
        data, count = supabase.table('leads').insert(data_to_insert).execute()
        
        print(f"Database: Lead '{business_name}' saved successfully.")

    except Exception as e:
        print(f"Database: Error saving lead to Supabase - {e}")


# --- THE MAIN ORCHESTRATOR (Simpler and Cleaner) ---
if __name__ == "__main__":
    if not supabase:
        print("AI Callback Empire Agent: Cannot start, Supabase client failed to initialize.")
    else:
        print("AI Callback Empire Agent: Initializing...")
        
        business_leads = find_business_leads(query="HVAC repair in Denver", num_results=1)

        for lead in business_leads:
            business_name = lead.get('title')
            place_id = lead.get('place_id')
            rating = lead.get('rating')
            reviews_count = lead.get('reviews')

            review_text_summary = get_business_reviews(place_id) 

            if review_text_summary:
                ai_analysis = analyze_opportunity(business_name, review_text_summary)
                if ai_analysis:
                    save_lead(business_name, rating, reviews_count, ai_analysis)
        
        print("AI Callback Empire Agent: Run complete.")
