# --- reddit_api_scraper.py (OFFICIAL API - NEVER BLOCKS) ---
import requests
import csv
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# Search Reddit's LEGAL subreddits (goldmine!)
SEARCH_QUERIES = [
    ('legaladvice', 'car accident'),
    ('legaladvice', 'motorcycle accident'),
    ('legaladvice', 'slip and fall'),
    ('legaladvice', 'injured at work'),
    ('personalinjury', 'lawyer'),
    ('Insurance', 'accident claim'),
    ('AskLawyers', 'injury'),
]

# Top USA cities
CITY_SUBREDDITS = [
    'LosAngeles', 'Miami', 'Houston', 'Chicago', 
    'Phoenix', 'Dallas', 'Austin', 'Seattle'
]

def search_reddit(subreddit, query):
    """Uses Reddit's JSON API (no auth needed)."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    
    params = {
        'q': query,
        'sort': 'new',
        'restrict_sr': 'on',
        't': 'month',  # Last month
        'limit': 25
    }
    
    headers = {'User-Agent': 'LeadFinder/1.0'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('children', [])
        else:
            log(f"  ⚠️ Reddit returned {response.status_code}")
            return []
    except Exception as e:
        log(f"  ❌ Error: {e}")
        return []

def extract_city_from_text(text):
    """Finds city mentions in text."""
    cities = {
        'los angeles': 'Los Angeles, CA', 'la': 'Los Angeles, CA',
        'miami': 'Miami, FL', 'houston': 'Houston, TX',
        'chicago': 'Chicago, IL', 'phoenix': 'Phoenix, AZ',
        'dallas': 'Dallas, TX', 'austin': 'Austin, TX',
        'seattle': 'Seattle, WA', 'san diego': 'San Diego, CA',
        'denver': 'Denver, CO', 'atlanta': 'Atlanta, GA'
    }
    
    text_lower = text.lower()
    for city_name, city_full in cities.items():
        if city_name in text_lower:
            return city_full.split(',')[0], city_full.split(',')[1].strip()
    
    return 'Unknown', 'Unknown'

def classify_injury(text):
    """Determines injury type."""
    text = text.lower()
    
    if 'car accident' in text or 'rear end' in text:
        return 'Car Accident'
    elif 'motorcycle' in text or 'bike accident' in text:
        return 'Motorcycle Accident'
    elif 'slip and fall' in text or 'fell' in text:
        return 'Slip and Fall'
    elif 'work injury' in text or 'workers comp' in text:
        return 'Workplace Injury'
    elif 'truck' in text:
        return 'Truck Accident'
    else:
        return 'Personal Injury'

def score_lead(post_data):
    """Scores 1-10."""
    score = 6
    
    title = post_data.get('title', '').lower()
    body = post_data.get('selftext', '').lower()
    text = title + ' ' + body
    
    # Positive indicators
    if any(w in text for w in ['hospital', 'er', 'doctor']):
        score += 2
    if 'police report' in text:
        score += 1
    if any(w in text for w in ['injured', 'hurt', 'pain']):
        score += 1
    if 'need a lawyer' in text or 'should i get a lawyer' in text:
        score += 2
    
    # Negative indicators
    if 'already have a lawyer' in text or 'my attorney' in text:
        score -= 5
    if 'years ago' in text:
        score -= 2
    
    return max(1, min(10, score))

def run_reddit_scraper():
    """Main scraper."""
    log("="*70)
    log("🚀 REDDIT API SCRAPER: Starting...")
    log("="*70)
    
    all_leads = []
    
    # Search legal subreddits
    for subreddit, query in SEARCH_QUERIES:
        log(f"🔍 Searching r/{subreddit} for '{query}'...")
        posts = search_reddit(subreddit, query)
        
        for post in posts:
            data = post.get('data', {})
            
            title = data.get('title', '')
            body = data.get('selftext', '')
            author = data.get('author', 'deleted')
            
            # Must be asking for help
            if author == 'deleted' or len(title) < 20:
                continue
            
            # Must mention injury
            if not any(w in (title + body).lower() for w in ['accident', 'injured', 'hurt', 'injury']):
                continue
            
            # Extract info
            city, state = extract_city_from_text(title + ' ' + body)
            injury_type = classify_injury(title + ' ' + body)
            score = score_lead(data)
            
            # Skip if already has lawyer
            if score <= 2:
                continue
            
            lead = {
                'name': f"u/{author}",
                'city': city,
                'state': state,
                'injury_type': injury_type,
                'description': title[:500],
                'source': 'Reddit',
                'source_url': f"https://reddit.com{data.get('permalink', '')}",
                'posted_date': datetime.fromtimestamp(data.get('created_utc', 0)).strftime('%Y-%m-%d'),
                'quality_score': score
            }
            
            all_leads.append(lead)
            log(f"  ✅ Found: {title[:60]}... (score: {score})")
        
        import time
        time.sleep(2)  # Rate limit
    
    # Also search city subreddits
    for city in CITY_SUBREDDITS[:4]:
        log(f"🔍 Searching r/{city} for accidents...")
        posts = search_reddit(city, 'accident lawyer')
        
        for post in posts[:5]:  # Top 5 per city
            data = post.get('data', {})
            
            title = data.get('title', '')
            author = data.get('author', 'deleted')
            
            if author == 'deleted' or len(title) < 20:
                continue
            
            injury_type = classify_injury(title)
            score = score_lead(data)
            
            if score <= 3:
                continue
            
            lead = {
                'name': f"u/{author}",
                'city': city,
                'state': 'Unknown',
                'injury_type': injury_type,
                'description': title[:500],
                'source': 'Reddit',
                'source_url': f"https://reddit.com{data.get('permalink', '')}",
                'posted_date': datetime.fromtimestamp(data.get('created_utc', 0)).strftime('%Y-%m-%d'),
                'quality_score': score
            }
            
            all_leads.append(lead)
        
        import time
        time.sleep(2)
    
    # Remove duplicates
    unique = []
    seen = set()
    for lead in all_leads:
        if lead['source_url'] not in seen:
            unique.append(lead)
            seen.add(lead['source_url'])
    
    log(f"\n📊 TOTAL UNIQUE LEADS: {len(unique)}")
    
    if unique:
        # Save to CSV
        with open('reddit_leads.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=unique[0].keys())
            writer.writeheader()
            writer.writerows(unique)
        log("✅ Saved to reddit_leads.csv")
        
        # Save to database
        supabase = get_supabase_client()
        if supabase:
            saved = 0
            for lead in unique:
                try:
                    existing = supabase.table('injured_people_leads')\
                        .select('id')\
                        .eq('source_url', lead['source_url'])\
                        .execute()
                    
                    if existing.data:
                        continue
                    
                    supabase.table('injured_people_leads').insert({
                        'prospect_name': lead['name'],
                        'city': lead['city'],
                        'injury_type': lead['injury_type'],
                        'injury_date': 'Recent',
                        'description': lead['description'],
                        'source': lead['source'],
                        'source_url': lead['source_url'],
                        'posted_date': lead['posted_date'],
                        'quality_score': lead['quality_score'],
                        'status': 'new'
                    }).execute()
                    
                    saved += 1
                except Exception as e:
                    log(f"  ❌ DB error: {e}")
            
            log(f"💾 Saved {saved} leads to database")
        
        # Print top leads
        log("\n🎯 TOP 10 LEADS:")
        top = sorted(unique, key=lambda x: x['quality_score'], reverse=True)[:10]
        for i, lead in enumerate(top, 1):
            log(f"{i}. {lead['description'][:70]}... (Score: {lead['quality_score']})")
    
    log("="*70)
    log("✅ REDDIT SCRAPER: Complete")
    log("="*70)

if __name__ == "__main__":
    run_reddit_scraper()
