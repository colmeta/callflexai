# --- reddit_api_scraper.py (PUSHSHIFT API - NEVER BLOCKS) ---
import requests
import csv
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def search_pushshift(subreddit, query, limit=50):
    """Uses Pushshift API (Reddit archive - no blocks)."""
    url = "https://api.pushshift.io/reddit/search/submission/"
    
    params = {
        'subreddit': subreddit,
        'q': query,
        'size': limit,
        'sort': 'desc',
        'sort_type': 'created_utc'
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            log(f"  ⚠️ Pushshift returned {response.status_code}")
            return []
    except Exception as e:
        log(f"  ❌ Error: {e}")
        return []

def extract_city(text):
    """Finds city in text."""
    cities = {
        'los angeles': ('Los Angeles', 'CA'), 'la': ('Los Angeles', 'CA'),
        'miami': ('Miami', 'FL'), 'houston': ('Houston', 'TX'),
        'chicago': ('Chicago', 'IL'), 'phoenix': ('Phoenix', 'AZ'),
        'dallas': ('Dallas', 'TX'), 'austin': ('Austin', 'TX')
    }
    
    text_lower = text.lower()
    for key, (city, state) in cities.items():
        if key in text_lower:
            return city, state
    return 'Unknown', 'Unknown'

def classify_injury(text):
    """Determines injury type."""
    text = text.lower()
    
    if 'car accident' in text or 'rear end' in text:
        return 'Car Accident'
    elif 'motorcycle' in text:
        return 'Motorcycle Accident'
    elif 'slip and fall' in text:
        return 'Slip and Fall'
    elif 'work' in text or 'workers comp' in text:
        return 'Workplace Injury'
    else:
        return 'Personal Injury'

def score_lead(title, selftext):
    """Scores 1-10."""
    score = 6
    text = (title + ' ' + selftext).lower()
    
    if any(w in text for w in ['hospital', 'er', 'doctor']):
        score += 2
    if 'police' in text:
        score += 1
    if any(w in text for w in ['injured', 'hurt', 'pain']):
        score += 1
    if 'need a lawyer' in text:
        score += 2
    
    if 'already have' in text or 'my attorney' in text:
        score -= 5
    if 'years ago' in text:
        score -= 2
    
    return max(1, min(10, score))

def run_reddit_scraper():
    """Main scraper."""
    log("="*70)
    log("🚀 REDDIT SCRAPER (PUSHSHIFT API): Starting...")
    log("="*70)
    
    searches = [
        ('legaladvice', 'car accident'),
        ('legaladvice', 'injured'),
        ('personalinjury', 'need lawyer'),
        ('Insurance', 'accident'),
    ]
    
    all_leads = []
    
    for subreddit, query in searches:
        log(f"🔍 Searching r/{subreddit} for '{query}'...")
        
        posts = search_pushshift(subreddit, query, limit=25)
        
        for post in posts:
            title = post.get('title', '')
            selftext = post.get('selftext', '')
            author = post.get('author', 'deleted')
            
            if author == 'deleted' or len(title) < 20:
                continue
            
            if not any(w in (title + selftext).lower() for w in ['accident', 'injured', 'hurt']):
                continue
            
            city, state = extract_city(title + ' ' + selftext)
            injury_type = classify_injury(title + ' ' + selftext)
            score = score_lead(title, selftext)
            
            if score <= 3:
                continue
            
            lead = {
                'name': f"u/{author}",
                'city': city,
                'state': state,
                'injury_type': injury_type,
                'description': title[:500],
                'source': 'Reddit',
                'source_url': f"https://reddit.com/r/{subreddit}/comments/{post.get('id', '')}",
                'posted_date': datetime.fromtimestamp(post.get('created_utc', 0)).strftime('%Y-%m-%d'),
                'quality_score': score
            }
            
            all_leads.append(lead)
            log(f"  ✅ {title[:60]}... (score: {score})")
        
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
        # Save CSV
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
                    existing = supabase.table('injured_people_leads').select('id').eq('source_url', lead['source_url']).execute()
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
            
            log(f"💾 Saved {saved} to database")
        
        # Print top leads
        log("\n🎯 TOP 10 LEADS:")
        top = sorted(unique, key=lambda x: x['quality_score'], reverse=True)[:10]
        for i, lead in enumerate(top, 1):
            log(f"{i}. {lead['description'][:70]}... ({lead['quality_score']}/10)")
    else:
        log("⚠️ No leads found")
    
    log("="*70)

if __name__ == "__main__":
    run_reddit_scraper()
