# --- dentist_scraper.py ---
# Scrapes 100+ dentists per day across America using Google Maps API
# Run: python dentist_scraper.py

import os
import csv
import time
import requests
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

load_dotenv()

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# ============================================================================
# TARGET USA CITIES (High-population areas = more dentists)
# ============================================================================

USA_CITIES = [
    {'city': 'New York', 'state': 'NY'},
    {'city': 'Los Angeles', 'state': 'CA'},
    {'city': 'Chicago', 'state': 'IL'},
    {'city': 'Houston', 'state': 'TX'},
    {'city': 'Phoenix', 'state': 'AZ'},
    {'city': 'Philadelphia', 'state': 'PA'},
    {'city': 'San Antonio', 'state': 'TX'},
    {'city': 'San Diego', 'state': 'CA'},
    {'city': 'Dallas', 'state': 'TX'},
    {'city': 'San Jose', 'state': 'CA'},
    {'city': 'Austin', 'state': 'TX'},
    {'city': 'Jacksonville', 'state': 'FL'},
    {'city': 'Fort Worth', 'state': 'TX'},
    {'city': 'Columbus', 'state': 'OH'},
    {'city': 'Charlotte', 'state': 'NC'},
    {'city': 'San Francisco', 'state': 'CA'},
    {'city': 'Indianapolis', 'state': 'IN'},
    {'city': 'Seattle', 'state': 'WA'},
    {'city': 'Denver', 'state': 'CO'},
    {'city': 'Boston', 'state': 'MA'},
    {'city': 'Nashville', 'state': 'TN'},
    {'city': 'Baltimore', 'state': 'MD'},
    {'city': 'Portland', 'state': 'OR'},
    {'city': 'Las Vegas', 'state': 'NV'},
    {'city': 'Miami', 'state': 'FL'},
]

# ============================================================================
# GOOGLE MAPS SCRAPER (Using SerpAPI)
# ============================================================================

def scrape_dentists_in_city(city: str, state: str, limit: int = 20) -> List[Dict]:
    """
    Scrapes dentists using Google Maps via SerpAPI.
    
    Args:
        city: City name
        state: State abbreviation
        limit: Number of results per city
    
    Returns:
        List of dentist data
    """
    log(f"\n🔍 Scraping dentists in {city}, {state}...")
    
    SERPAPI_KEY = os.getenv('SERPAPI_API_KEY')
    
    if not SERPAPI_KEY:
        log("❌ SERPAPI_API_KEY not found in .env file!")
        log("Get free key at: https://serpapi.com/")
        return []
    
    try:
        from serpapi import GoogleSearch
        
        search_params = {
            "engine": "google_maps",
            "q": f"dentist {city} {state}",
            "type": "search",
            "api_key": SERPAPI_KEY
        }
        
        search = GoogleSearch(search_params)
        results = search.get_dict()
        
        local_results = results.get("local_results", [])
        
        if not local_results:
            log(f"⚠️ No dentists found in {city}")
            return []
        
        dentists = []
        
        for result in local_results[:limit]:
            dentist = {
                'business_name': result.get('title', 'Unknown'),
                'city': city,
                'state': state,
                'address': result.get('address', ''),
                'phone': result.get('phone', ''),
                'website': result.get('website', ''),
                'rating': result.get('rating', 0),
                'review_count': result.get('reviews', 0),
                'google_maps_url': result.get('link', ''),
                
                # Calculate chatbot need score
                'needs_chatbot_score': calculate_chatbot_need_score(result),
                
                # Extract pain points from reviews
                'pain_points': extract_pain_points(result),
                
                # Guess email
                'contact_email': guess_email(result.get('website', ''), result.get('title', '')),
                
                'status': 'new',
                'found_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            dentists.append(dentist)
            log(f"  ✅ {dentist['business_name']} | Score: {dentist['needs_chatbot_score']}/10")
        
        log(f"✅ Found {len(dentists)} dentists in {city}")
        return dentists
        
    except ImportError:
        log("❌ SerpAPI not installed. Install: pip install google-search-results")
        return []
    except Exception as e:
        log(f"❌ Error: {e}")
        return []

def calculate_chatbot_need_score(result: Dict) -> int:
    """
    Scores how much a dentist needs a chatbot (1-10).
    Higher = more desperate for automation.
    """
    score = 5  # Base score
    
    rating = result.get('rating', 0)
    review_count = result.get('reviews', 0)
    
    # Low reviews = not many patients
    if review_count < 50:
        score += 2
    elif review_count < 100:
        score += 1
    
    # Lower rating = service issues (chatbot can help!)
    if rating < 4.0:
        score += 3
    elif rating < 4.3:
        score += 2
    elif rating < 4.5:
        score += 1
    
    # No website = not tech-savvy (easier sell)
    if not result.get('website'):
        score += 1
    
    return min(10, score)

def extract_pain_points(result: Dict) -> List[str]:
    """
    Identifies pain points from reviews.
    These are problems your chatbot can solve!
    """
    pain_points = []
    
    # Check service types
    service_options = result.get('service_options', {})
    
    if not service_options.get('online_appointments'):
        pain_points.append('No online booking')
    
    if not service_options.get('online_care'):
        pain_points.append('No online consultation')
    
    # Check hours
    hours = result.get('hours', '')
    if 'closed' in hours.lower() or not hours:
        pain_points.append('Limited availability')
    
    # Based on review count and rating
    rating = result.get('rating', 0)
    review_count = result.get('reviews', 0)
    
    if review_count < 50:
        pain_points.append('Low patient volume')
    
    if rating < 4.3:
        pain_points.append('Customer service issues')
    
    return pain_points[:3]  # Top 3 pain points

def guess_email(website: str, business_name: str) -> str:
    """
    Guesses the contact email based on website.
    """
    if not website:
        return ''
    
    # Extract domain
    domain = website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
    
    # Common patterns for dental practices
    patterns = [
        f"info@{domain}",
        f"contact@{domain}",
        f"office@{domain}",
        f"reception@{domain}"
    ]
    
    return patterns[0]  # Return most likely

# ============================================================================
# SAVE FUNCTIONS
# ============================================================================

def save_to_csv(dentists: List[Dict], filename: str = 'dentists_scraped.csv'):
    """Saves to CSV for review."""
    if not dentists:
        return
    
    log(f"\n💾 Saving {len(dentists)} dentists to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['business_name', 'city', 'state', 'phone', 'website', 
                     'contact_email', 'rating', 'review_count', 'needs_chatbot_score', 
                     'pain_points', 'google_maps_url', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for dentist in dentists:
            row = {k: dentist.get(k, '') for k in fieldnames}
            # Convert list to string for CSV
            if isinstance(row['pain_points'], list):
                row['pain_points'] = ', '.join(row['pain_points'])
            writer.writerow(row)
    
    log(f"✅ Saved to {filename}")

def save_to_database(dentists: List[Dict]):
    """Saves dentists to Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Database connection failed")
        return
    
    saved = 0
    duplicates = 0
    
    for dentist in dentists:
        try:
            # Check for duplicates
            existing = supabase.table('dentists')\
                .select('id')\
                .eq('business_name', dentist['business_name'])\
                .eq('city', dentist['city'])\
                .execute()
            
            if existing.data:
                duplicates += 1
                continue
            
            # Save to database
            db_data = {
                'business_name': dentist['business_name'],
                'contact_email': dentist['contact_email'],
                'contact_phone': dentist.get('phone'),
                'city': dentist['city'],
                'state': dentist['state'],
                'address': dentist.get('address'),
                'website': dentist.get('website'),
                'rating': dentist.get('rating'),
                'review_count': dentist.get('review_count'),
                'google_maps_url': dentist.get('google_maps_url'),
                'needs_chatbot_score': dentist.get('needs_chatbot_score'),
                'pain_points': dentist.get('pain_points', []),
                'status': 'new',
                'found_date': dentist.get('found_date')
            }
            
            supabase.table('dentists').insert(db_data).execute()
            
            saved += 1
            log(f"  ✅ Saved: {dentist['business_name']}")
            
        except Exception as e:
            log(f"  ❌ Error saving {dentist['business_name']}: {e}")
    
    log(f"\n💾 DATABASE: Saved {saved}, Duplicates {duplicates}")

# ============================================================================
# MASTER ORCHESTRATOR
# ============================================================================

def run_dentist_scraper(target_count: int = 100):
    """
    Main function: Scrapes dentists until target reached.
    
    Args:
        target_count: How many dentists to scrape (default 100)
    """
    log("="*70)
    log(f"🦷 DENTIST SCRAPER: Target {target_count} dentists")
    log("="*70)
    
    all_dentists = []
    cities_processed = 0
    
    # Calculate how many cities we need (assuming ~20 per city)
    dentists_per_city = 20
    cities_needed = (target_count // dentists_per_city) + 1
    
    log(f"📊 Will scrape {cities_needed} cities ({dentists_per_city} dentists each)")
    
    for location in USA_CITIES[:cities_needed]:
        dentists = scrape_dentists_in_city(
            location['city'], 
            location['state'], 
            limit=dentists_per_city
        )
        
        all_dentists.extend(dentists)
        cities_processed += 1
        
        log(f"📊 Progress: {len(all_dentists)}/{target_count} dentists scraped")
        
        # Stop if we hit target
        if len(all_dentists) >= target_count:
            log(f"🎯 Target reached! Scraped {len(all_dentists)} dentists")
            break
        
        # Delay between cities (be respectful to API)
        if cities_processed < cities_needed:
            log("⏳ Waiting 5 seconds...")
            time.sleep(5)
    
    log(f"\n{'='*70}")
    log(f"📊 TOTAL DENTISTS FOUND: {len(all_dentists)}")
    log(f"{'='*70}")
    
    if all_dentists:
        # Save results
        save_to_csv(all_dentists)
        save_to_database(all_dentists)
        
        # Print top prospects
        log(f"\n🎯 TOP 10 PROSPECTS (Most Likely to Buy Chatbot):")
        top_prospects = sorted(all_dentists, key=lambda x: x['needs_chatbot_score'], reverse=True)[:10]
        
        for i, dentist in enumerate(top_prospects, 1):
            log(f"\n{i}. {dentist['business_name']}")
            log(f"   📍 {dentist['city']}, {dentist['state']}")
            log(f"   ⭐ Rating: {dentist['rating']}/5 ({dentist['review_count']} reviews)")
            log(f"   📞 {dentist['phone']}")
            log(f"   📧 {dentist['contact_email']}")
            log(f"   🤖 Chatbot Need: {dentist['needs_chatbot_score']}/10")
            log(f"   💡 Pain Points: {', '.join(dentist['pain_points'])}")
        
        # Print stats by city
        from collections import Counter
        city_counts = Counter(d['city'] for d in all_dentists)
        
        log(f"\n📊 DENTISTS BY CITY:")
        for city, count in city_counts.most_common(10):
            log(f"  {city}: {count}")
    
    log("\n" + "="*70)
    log("✅ DENTIST SCRAPER: Complete")
    log("="*70)
    log("\n📋 NEXT STEPS:")
    log("1. Review CSV: dentists_scraped.csv")
    log("2. Check Supabase: dentists table")
    log("3. Run: python email_generator.py (to create outreach emails)")

if __name__ == "__main__":
    # Scrape 100 dentists by default
    # To scrape more: python dentist_scraper.py 200
    
    target = 100
    if len(sys.argv) > 1:
        try:
            target = int(sys.argv[1])
        except ValueError:
            log("Usage: python dentist_scraper.py [number]")
            log("Example: python dentist_scraper.py 200")
            sys.exit(1)
    
    run_dentist_scraper(target_count=target)
