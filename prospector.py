# --- prospector.py (FLEXIBLE VERSION) ---
# This module finds business leads based on CLIENT-SPECIFIC settings.

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# NEW: We're using ScraperAPI's free tier instead of SerpAPI
SCRAPER_API_KEY = os.getenv('SCRAPER_API_KEY')

def log(message):
    """Simple logging function."""
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def find_business_leads(niche, location, num_results=20):
    """
    Finds business leads using Google Local Search via ScraperAPI.
    
    Args:
        niche (str): Type of business (e.g., "Plumbers", "Dentists")
        location (str): City/area (e.g., "Austin TX", "Miami FL")
        num_results (int): How many results to return
    
    Returns:
        list: Business data dictionaries
    """
    query = f"{niche} in {location}"
    log(f"Prospector: Searching for '{query}'...")
    
    if not SCRAPER_API_KEY:
        log("Prospector: ERROR - ScraperAPI key is missing.")
        return []
    
    # Build the Google Local Search URL
    google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=lcl"
    
    # Use ScraperAPI to scrape Google (bypasses rate limits)
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={google_url}"
    
    try:
        log("Prospector: Sending request to ScraperAPI...")
        response = requests.get(scraper_url, timeout=60)
        
        if response.status_code == 200:
            # Parse the HTML response (simple version - we'll extract business data)
            html = response.text
            businesses = parse_google_local_results(html, num_results)
            
            if not businesses:
                log(f"Prospector: WARNING - Search returned ZERO results.")
            else:
                log(f"Prospector: SUCCESS - Found {len(businesses)} leads.")
            return businesses
        else:
            log(f"Prospector: ERROR - ScraperAPI returned status {response.status_code}")
            return []
    
    except Exception as e:
        log(f"Prospector: ERROR during search: {e}")
        return []

def parse_google_local_results(html, limit):
    """
    Parses Google Local search results from HTML.
    This is a simplified parser - you can enhance with BeautifulSoup.
    """
    # For now, we'll return simulated data to keep things moving
    # In production, you'd use BeautifulSoup to parse the HTML properly
    
    # TEMPORARY SIMULATION (replace this once you test ScraperAPI works)
    log("Prospector: Using simulated results for testing...")
    simulated_results = [
        {
            "title": f"Test Business {i}",
            "place_id": f"test_id_{i}",
            "rating": 4.2,
            "reviews": 45,
            "address": "123 Main St"
        }
        for i in range(1, limit + 1)
    ]
    return simulated_results[:limit]

def get_business_reviews(place_id):
    """
    Fetches review text for a business.
    For now, returns simulated reviews with pain point keywords.
    
    TODO: In production, integrate Google Places API (free tier: 0-100k requests)
    """
    log(f"Prospector: Fetching reviews for place_id {place_id[:15]}...")
    
    # Simulated reviews with pain points our Analyst will detect
    review_templates = [
        "They never called me back. Had to reach out three times for a quote.",
        "Scheduling was a nightmare. Couldn't get through on the phone.",
        "Great service but communication was terrible. No follow-up at all.",
        "I left two voicemails and never heard back. Very unprofessional.",
        "Hard to reach. Phone always goes to voicemail during business hours."
    ]
    
    # Return a random mix of reviews
    import random
    return " ".join(random.sample(review_templates, k=3))
