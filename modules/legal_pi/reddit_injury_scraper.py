# --- modules/legal_pi/reddit_injury_scraper.py (FIXED & COMPLETE) ---
import requests
import csv
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# LEGAL ADVICE SUBREDDITS (Better than city subreddits!)
LEGAL_SUBREDDITS = [
    'legaladvice',
    'personalinjury', 
    'AskLawyers',
    'Insurance'
]

# Also search some high-traffic city subreddits
TOP_CITY_SUBREDDITS = [
    'LosAngeles', 'Miami', 'Houston', 'Chicago', 'Phoenix'
]

# Injury keywords
INJURY_KEYWORDS = [
    'car accident', 'hit by car', 'rear ended', 'motorcycle accident',
    'truck accident', 'slip and fall', 'injured at work',
    'need a lawyer', 'should i get a lawyer', 'medical bills',
    'insurance wont pay', 'other driver', 'not my fault'
]

def search_subreddit(subreddit_name, days_back=7):
    """Searches one subreddit for injury posts."""
    log(f"Searching r/{subreddit_name}...")
    
    url = f"https://www.reddit.com/r/{subreddit_name}/search.json"
    all_leads = []
    
    for keyword in INJURY_KEYWORDS[:8]:  # Use top 8 keywords
        params = {
            'q': keyword,
            'sort': 'new',
            'limit': 25,
            't': 'week',
            'restrict_sr': 'on'
        }
        
        headers = {'User-Agent': 'PILeadFinder/1.0'}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                for post in posts:
                    post_data = post['data']
                    
                    title = post_data['title'].lower()
                    body = post_data.get('selftext', '').lower()
                    
                    # Must be asking for help
                    if not any(word in title or word in body for word in ['i was', 'my', 'need', 'should i']):
                        continue
                    
                    # Check recency
                    post_time = datetime.fromtimestamp(post_data['created_utc'])
                    if datetime.now() - post_time > timedelta(days=days_back):
                        continue
                    
                    # Determine injury type
                    injury_type = 'Unknown'
                    if 'car' in title or 'car' in body:
                        injury_type = 'Car Accident'
                    elif 'motorcycle' in title or 'bike' in body:
                        injury_type = 'Motorcycle Accident'
                    elif 'slip' in title or 'fall' in title:
                        injury_type = 'Slip and Fall'
                    elif 'work' in title or 'job' in body:
                        injury_type = 'Workplace Injury'
                    
                    # Extract city from post if available
                    city = extract_city_from_text(title + ' ' + body) or subreddit_name
                    
                    lead = {
                        'name': f"u/{post_data['author']}",
                        'city': city,
                        'injury_type': injury_type,
                        'injury_date': 'Recent',
                        'description': post_data['title'],
                        'details': post_data['selftext'][:300],
                        'source': 'Reddit',
                        'source_url': f"https://reddit.com{post_data['permalink']}",
                        'posted_date': post_time.strftime('%Y-%m-%d'),
                        'quality_score': calculate_quality_score(post_data)
                    }
                    
                    all_leads.append(lead)
        
        except Exception as e:
            log(f"  Error with '{keyword}': {e}")
            continue
    
    # Remove duplicates
    unique = []
    seen = set()
    for lead in all_leads:
        if lead['source_url'] not in seen:
            unique.append(lead)
            seen.add(lead['source_url'])
    
    log(f"  Found {len(unique)} unique leads in r/{subreddit_name}")
    return unique

def extract_city_from_text(text):
    """Tries to extract city name from post text."""
    cities = [
        'Los Angeles', 'LA', 'Miami', 'Houston', 'Chicago', 'Phoenix',
        'Dallas', 'Austin', 'Seattle', 'Denver', 'Atlanta', 'San Diego'
    ]
    
    for city in cities:
        if city.lower() in text.lower():
            if city == 'LA':
                return 'Los Angeles'
            return city
    return None

def calculate_quality_score(post_data):
    """Scores from 1-10."""
    score = 5
    title = post_data['title'].lower()
    body = post_data.get('selftext', '').lower()
    text = title + ' ' + body
    
    # Positive
    if 'doctor' in text or 'hospital' in text or 'er' in text:
        score += 2
    if 'police' in text:
        score += 1
    if any(w in text for w in ['hurt', 'injured', 'pain']):
        score += 1
    if any(w in text for w in ['other driver', 'not my fault']):
        score += 1
    if 'need a lawyer' in text:
        score += 2
    
    # Negative
    if 'already have' in text or 'my lawyer' in text:
        score -= 5
    if 'years ago' in text:
        score -= 2
    
    return max(1, min(10, score))

def save_to_csv(leads, filename='reddit_injured_leads.csv'):
    """Saves to CSV."""
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
    
    saved = 0
    for lead in leads:
        try:
            existing = supabase.table('injured_people_leads').select('id').eq('source_url', lead['source_url']).execute()
            if existing.data:
                continue
            
            supabase.table('injured_people_leads').insert({
                'prospect_name': lead['name'],
                'city': lead['city'],
                'injury_type': lead['injury_type'],
                'injury_date': lead['injury_date'],
                'description': lead['description'],
                'details': lead['details'],
                'source': lead['source'],
                'source_url': lead['source_url'],
                'posted_date': lead['posted_date'],
                'quality_score': lead['quality_score'],
                'status': 'new'
            }).execute()
            
            saved += 1
            log(f"  ✅ Saved: {lead['name']} (score: {lead['quality_score']})")
        except Exception as e:
            log(f"  ❌ Error: {e}")
    
    log(f"Database: Saved {saved} new leads")

def run_reddit_scraper():
    """Main function."""
    log("="*70)
    log("REDDIT SCRAPER: Starting...")
    log("="*70)
    
    all_leads = []
    
    # Search legal advice subreddits (BEST SOURCE!)
    for subreddit in LEGAL_SUBREDDITS:
        leads = search_subreddit(subreddit, days_back=7)
        all_leads.extend(leads)
        import time
        time.sleep(3)
    
    # Also search top city subreddits
    for subreddit in TOP_CITY_SUBREDDITS[:3]:
        leads = search_subreddit(subreddit, days_back=7)
        all_leads.extend(leads)
        import time
        time.sleep(3)
    
    log(f"\nTotal: {len(all_leads)} leads")
    
    if all_leads:
        save_to_csv(all_leads)
        save_to_database(all_leads)
        
        # Summary
        from collections import Counter
        city_counts = Counter(l['city'] for l in all_leads)
        log("\nLeads by city:")
        for city, count in city_counts.most_common():
            log(f"  {city}: {count}")
    
    log("="*70)
    log("REDDIT SCRAPER: Complete")
    log("="*70)

if __name__ == "__main__":
    run_reddit_scraper()
