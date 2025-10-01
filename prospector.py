# --- prospector.py ---
# This module is responsible for finding business leads online.

import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()

SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')

def log(message):
    """A simple logging function for this module."""
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def find_business_leads(query="Plumbers in Austin TX", num_results=20):
    """Finds business leads using SerpApi's Google Local Search engine."""
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
    """Simulates getting review text for a given business place_id."""
    log(f"Prospector: Simulating review fetch for place_id {place_id[:15]}...")
    # This simulated review contains keywords our Analyst will look for.
    return "Communication was poor. I had to call them three times to get a quote, and no one seemed to know what was going on. They never called me back after the first message. Frustrating experience trying to get an appointment."
