# --- modules/legal_pi/craigslist_scraper.py ---
# Scrapes Craigslist for injury-related posts (free, no API needed)

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# Craigslist city domains
CRAIGSLIST_CITIES = {
    'Los Angeles': 'losangeles',
    'Miami': 'miami',
    'Houston': 'houston',
    'Chicago': 'chicago',
    'Phoenix': 'phoenix',
    'San Diego': 'sandiego',
    'Dallas': 'dallas',
    'Austin': 'austin',
    'Seattle': 'seattle',
    'Denver': 'denver'
}

# Search terms for injuries
INJURY_SEARCH_TERMS = [
    'car accident lawyer',
    'injury attorney',
    'personal injury',
    'accident lawyer needed',
    'hit by car need lawyer'
]

def scrape_craigslist_city(city_name, city_domain):
    """
    Scrapes Craigslist community/legal sections for injury posts.
    
    Args:
        city_name (str): "Los Angeles"
        city_domain (str): "losangeles"
    
    Returns:
        list: Found injury-related posts
    """
    log(f"Craigslist Scraper: Searching {city_name}...")
    
    all_posts = []
    
    for search_term in INJURY_SEARCH_TERMS:
        # Craigslist search URL (searches all categories)
        url = f"https://{city_domain}.craigslist.org/search/sss?query={search_term.replace(' ', '+')}&sort=date"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all result rows
                results = soup.find_all('li', class_='cl-static-search-result')
                
                for result in results:
                    try:
                        # Extract post details
                        title_tag = result.find('div', class_='title')
                        title = title_tag.text.strip() if title_tag else 'No Title'
                        
                        link_tag = result.find('a')
                        link = link_tag['href'] if link_tag else ''
                        
                        # Full URL
                        if link and not link.startswith('http'):
                            link = f"https://{city_domain}.craigslist.org{link}"
                        
                        # Date posted
                        date_tag = result.find('div', class_='meta')
                        date_text = date_tag.text.strip() if date_tag else 'Unknown'
                        
                        # Filter: Must be seeking help (not offering services)
                        title_lower = title.lower()
                        
                        # Skip if it's a lawyer advertising
                        if any(word in title_lower for word in ['attorney', 'law firm', 'legal services', 'free consultation']):
                            continue
                        
                        # Must be asking for help
                        if not any(word in title_lower for word in ['need', 'looking for', 'help', 'advice', 'recommend']):
                            continue
                        
                        post = {
                            'name': 'Craigslist User',
                            'city': city_name,
                            'injury_type': 'Unknown',
                            'description': title,
                            'source': 'Craigslist',
                            'source_url': link,
                            'posted_date': date_text,
                            'quality_score': 5  # Average quality
                        }
                        
                        all_posts.append(post)
                    
                    except Exception as e:
                        log(f"  Error parsing result: {e}")
                        continue
                
                log(f"  Found {len(results)} posts for '{search_term}'")
            
            else:
                log(f"  HTTP {response.status_code} for {city_name}")
        
        except Exception as e:
            log(f"  ERROR: {e}")
            continue
        
        # Be respectful: 3-second delay between searches
        import time
        time.sleep(3)
    
    log(f"Craigslist: Found {len(all_posts)} posts in {city_name}")
    return all_posts

def save_to_csv(leads, filename='craigslist_injured_leads.csv'):
    """Saves leads to CSV."""
    if not leads:
        log("No leads to save.")
        return
    
    log(f"Saving {len(leads)} leads to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=leads[0].keys())
        writer.writeheader()
        writer.writerows(leads)
    
    log(f"✅ Saved to {filename}")

def save_to_database(leads):
    """Saves to Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        log("ERROR: Cannot connect to database.")
        return
    
    saved_count = 0
    
    for lead in leads:
        try:
            # Check for duplicates
            existing = supabase.table('injured_people_leads').select('id').eq('source_url', lead['source_url']).execute()
            
            if existing.data:
                continue
            
            lead_data = {
                'prospect_name': lead['name'],
                'city': lead['city'],
                'injury_type': lead['injury_type'],
                'description': lead['description'],
                'source': lead['source'],
                'source_url': lead['source_url'],
                'posted_date': lead['posted_date'],
                'quality_score': lead['quality_score'],
                'status': 'new'
            }
            
            supabase.table('injured_people_leads').insert(lead_data).execute()
            saved_count += 1
            log(f"  ✅ Saved: {lead['description'][:50]}...")
        
        except Exception as e:
            log(f"  ❌ Error: {e}")
    
    log(f"Database: Saved {saved_count} new leads")

def run_craigslist_scraper():
    """Main function."""
    log("="*60)
    log("CRAIGSLIST AUTO SCRAPER: Starting...")
    log("="*60)
    
    all_leads = []
    
    # Scrape top 5 cities
    for city_name, city_domain in list(CRAIGSLIST_CITIES.items())[:5]:
        leads = scrape_craigslist_city(city_name, city_domain)
        all_leads.extend(leads)
    
    log(f"\nTotal leads found: {len(all_leads)}")
    
    if all_leads:
        save_to_csv(all_leads)
        save_to_database(all_leads)
    
    log("="*60)
    log("CRAIGSLIST SCRAPER: Complete")
    log("="*60)

if __name__ == "__main__":
    run_craigslist_scraper()
