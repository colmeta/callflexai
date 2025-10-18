# --- modules/legal_pi/google_maps_pi_lawyer_scraper.py ---
# Finds PI lawyers using Google Maps + extracts emails, phones, reviews
# This finds YOUR CLIENTS (the lawyers who will pay you)

import os
import sys
import csv
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_supabase_client

# Try to import SerpAPI (falls back to manual search if not available)
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    print("⚠️ SerpAPI not installed. Install with: pip install google-search-results")

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# Top USA cities with high accident rates = more PI cases
TARGET_CITIES = [
    {'city': 'Los Angeles', 'state': 'CA'},
    {'city': 'Miami', 'state': 'FL'},
    {'city': 'Houston', 'state': 'TX'},
    {'city': 'Phoenix', 'state': 'AZ'},
    {'city': 'Dallas', 'state': 'TX'},
    {'city': 'Chicago', 'state': 'IL'},
    {'city': 'Atlanta', 'state': 'GA'},
    {'city': 'Las Vegas', 'state': 'NV'},
    {'city': 'San Diego', 'state': 'CA'},
    {'city': 'Austin', 'state': 'TX'}
]

def find_pi_lawyers_in_city(city, state, limit=20):
    """
    Finds Personal Injury lawyers in a city using Google Maps.
    
    Returns:
        list: Law firms with contact info
    """
    log(f"🔍 Searching for PI lawyers in {city}, {state}...")
    
    SERPAPI_KEY = os.getenv('SERPAPI_API_KEY')
    
    if not SERPAPI_KEY or not SERPAPI_AVAILABLE:
        log("❌ SerpAPI not configured. Using manual search fallback.")
        return manual_search_fallback(city, state)
    
    # Search Google Maps for PI lawyers
    search_params = {
        "engine": "google_maps",
        "q": f"personal injury lawyer {city} {state}",
        "type": "search",
        "api_key": SERPAPI_KEY
    }
    
    try:
        search = GoogleSearch(search_params)
        results = search.get_dict()
        
        local_results = results.get("local_results", [])
        
        if not local_results:
            log(f"⚠️ No results found for {city}")
            return []
        
        lawyers = []
        
        for result in local_results[:limit]:
            # Extract law firm details
            lawyer = {
                'business_name': result.get('title', 'Unknown'),
                'city': city,
                'state': state,
                'address': result.get('address', ''),
                'phone': result.get('phone', ''),
                'website': result.get('website', ''),
                'rating': result.get('rating', 0),
                'review_count': result.get('reviews', 0),
                'hours': result.get('hours', ''),
                'google_maps_url': result.get('link', ''),
                
                # Analyze if they need leads (based on reviews/rating)
                'needs_leads_score': calculate_needs_leads_score(result),
                'status': 'prospect'
            }
            
            # Try to guess email (will verify later)
            lawyer['contact_email'] = guess_email_from_website(lawyer['website'], lawyer['business_name'])
            
            lawyers.append(lawyer)
            log(f"  ✅ Found: {lawyer['business_name']} (Score: {lawyer['needs_leads_score']}/10)")
        
        log(f"✅ Found {len(lawyers)} PI lawyers in {city}")
        return lawyers
    
    except Exception as e:
        log(f"❌ Error: {e}")
        return []

def calculate_needs_leads_score(result):
    """
    Scores how badly a law firm needs leads (1-10).
    Higher score = more desperate for clients.
    """
    score = 5  # Base score
    
    rating = result.get('rating', 0)
    review_count = result.get('reviews', 0)
    
    # Low reviews = not getting much business
    if review_count < 50:
        score += 2
    elif review_count < 20:
        score += 3
    
    # Lower rating = communication issues (our value prop!)
    if rating < 4.0:
        score += 2
    elif rating < 3.5:
        score += 3
    
    # No website = not investing in marketing
    if not result.get('website'):
        score += 1
    
    return min(10, score)

def guess_email_from_website(website, business_name):
    """
    Guesses the contact email based on common patterns.
    
    Examples:
    - info@smithlaw.com
    - contact@jonesandpartners.com
    - intake@millerinjurylaw.com
    """
    if not website:
        return None
    
    # Extract domain from website
    domain = website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
    
    # Common email patterns for law firms
    patterns = [
        f"info@{domain}",
        f"contact@{domain}",
        f"intake@{domain}",
        f"admin@{domain}"
    ]
    
    # Return the most likely one (info@ is most common)
    return patterns[0]

def manual_search_fallback(city, state):
    """
    Fallback: Returns instructions for manual Google Maps search.
    """
    log(f"\n📋 MANUAL SEARCH INSTRUCTIONS for {city}, {state}:")
    log("1. Open Google Maps")
    log(f"2. Search: 'personal injury lawyer {city} {state}'")
    log("3. Copy the top 10-20 results to a CSV:")
    log("   - Business Name")
    log("   - Phone Number")
    log("   - Website")
    log("   - Rating")
    log("   - Number of Reviews")
    log("4. Save as: pi_lawyers_{city.lower()}.csv")
    log("5. Run: python upload_manual_lawyers.py pi_lawyers_{city.lower()}.csv\n")
    
    return []

def save_to_csv(lawyers, filename='pi_lawyers_prospects.csv'):
    """Saves lawyer prospects to CSV for review."""
    if not lawyers:
        log("No lawyers to save.")
        return
    
    log(f"💾 Saving {len(lawyers)} lawyers to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=lawyers[0].keys())
        writer.writeheader()
        writer.writerows(lawyers)
    
    log(f"✅ Saved to {filename}")

def save_to_database(lawyers):
    """Saves lawyers to Supabase as potential clients."""
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Cannot connect to database.")
        return
    
    saved_count = 0
    duplicate_count = 0
    
    for lawyer in lawyers:
        try:
            # Check for duplicates (by business name + city)
            existing = supabase.table('pi_lawyer_clients').select('id')\
                .eq('business_name', lawyer['business_name'])\
                .eq('city', lawyer['city']).execute()
            
            if existing.data:
                log(f"  ⚠️ Duplicate: {lawyer['business_name']}")
                duplicate_count += 1
                continue
            
            # Prepare data for insertion
            lawyer_data = {
                'business_name': lawyer['business_name'],
                'contact_email': lawyer['contact_email'],
                'contact_phone': lawyer.get('phone'),
                'city': lawyer['city'],
                'state': lawyer['state'],
                'website': lawyer.get('website'),
                'status': 'prospect',
                'price_per_lead': 800.00  # Default pricing
            }
            
            supabase.table('pi_lawyer_clients').insert(lawyer_data).execute()
            saved_count += 1
            log(f"  ✅ Saved: {lawyer['business_name']} (needs_leads_score: {lawyer['needs_leads_score']})")
        
        except Exception as e:
            log(f"  ❌ Error saving {lawyer['business_name']}: {e}")
    
    log(f"\n📊 Summary:")
    log(f"  Saved: {saved_count}")
    log(f"  Duplicates skipped: {duplicate_count}")

def run_lawyer_scraper():
    """Main function: Scrapes PI lawyers in all target cities."""
    log("="*70)
    log("🎯 PI LAWYER SCRAPER: Finding Your Clients")
    log("="*70 + "\n")
    
    all_lawyers = []
    
    # Scrape top 5 cities (increase later)
    for location in TARGET_CITIES[:5]:
        lawyers = find_pi_lawyers_in_city(location['city'], location['state'], limit=20)
        all_lawyers.extend(lawyers)
        
        # Be respectful: 3-second delay between cities
        import time
        time.sleep(3)
    
    log(f"\n📊 Total lawyers found: {len(all_lawyers)}")
    
    if all_lawyers:
        # Save to CSV for your review
        save_to_csv(all_lawyers)
        
        # Save to database as prospects
        save_to_database(all_lawyers)
        
        # Print top prospects (highest needs_leads_score)
        log("\n🎯 TOP 10 PROSPECTS (Most Likely to Need Leads):")
        top_prospects = sorted(all_lawyers, key=lambda x: x['needs_leads_score'], reverse=True)[:10]
        
        for idx, lawyer in enumerate(top_prospects, 1):
            log(f"\n  {idx}. {lawyer['business_name']}")
            log(f"     City: {lawyer['city']}, {lawyer['state']}")
            log(f"     Phone: {lawyer['phone']}")
            log(f"     Email (guessed): {lawyer['contact_email']}")
            log(f"     Rating: {lawyer['rating']}/5 ({lawyer['review_count']} reviews)")
            log(f"     Needs Leads Score: {lawyer['needs_leads_score']}/10")
    
    log("\n" + "="*70)
    log("✅ LAWYER SCRAPER: Complete")
    log("="*70)

if __name__ == "__main__":
    run_lawyer_scraper()
