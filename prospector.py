# --- prospector.py (FLEXIBLE VERSION) ---

import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()

# We are using SerpApi because it is superior at PARSING and returning clean JSON.
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')

def log(message):
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def find_business_leads(niche, location, num_results=20):
    """
    Finds real business leads using SerpApi's parsed Google Local endpoint.
    This version does NOT use simulation. It returns real data.
    """
    query = f"{niche} in {location}"
    log(f"Prospector: Searching for real data for '{query}' using SerpApi...")
    
    if not SERPAPI_API_KEY:
        log("Prospector: ERROR - SerpApi API key is missing. Cannot perform real search.")
        return []
        
    search_params = {
        "engine": "google_local",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": num_results
    }
    
    try:
        log("Prospector: Sending request to SerpApi...")
        search = GoogleSearch(search_params)
        results = search.get_dict()
        
        local_results = results.get("local_results", [])
        
        if "error" in results:
            log(f"Prospector: API ERROR from SerpApi: {results['error']}")
            return []

        if not local_results:
            log(f"Prospector: WARNING - SerpApi returned ZERO 'local_results' for this query.")
        else:
            log(f"Prospector: SUCCESS - Found {len(local_results)} real business leads.")
            
        # The API gives us exactly what we need, no manual parsing required.
        # The structure is already a list of dictionaries, e.g., {"title": "...", "rating": 4.5, ...}
        return local_results

    except Exception as e:
        log(f"Prospector: CRITICAL ERROR during SerpApi call: {e}")
        return []

def get_business_reviews(place_id):
    """
    Simulates fetching review text for a business.
    This part remains a simulation as fetching real reviews is a more advanced (and costly) step.
    This provides our Analyst with the keywords it needs to function.
    """
    log(f"Prospector: Simulating review fetch for place_id '{place_id}'...")
    
    # This simulation is still essential for our keyword-based Analyst to work.
    review_templates = [
        "They never called me back after I left a voicemail. I had to find another company.",
        "Scheduling was a nightmare. Very poor communication and no follow-up.",
        "Hard to get a hold of anyone on the phone. Goes straight to an answering machine."
    ]
    
    import random
    return " ".join(random.sample(review_templates, k=2))
