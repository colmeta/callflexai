# --- reddit_finder.py ---
# This automatically finds people asking for services on Reddit.

import os
import requests
from datetime import datetime
from database import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def search_reddit_for_leads(subreddit, keyword, location):
    """
    Searches a subreddit for posts containing specific keywords.
    
    Args:
        subreddit (str): e.g., "Austin"
        keyword (str): e.g., "dentist"
        location (str): e.g., "Austin"
    
    Returns:
        list: Found posts with potential leads
    """
    log(f"Reddit Finder: Searching r/{subreddit} for '{keyword}'...")
    
    # Reddit's free JSON API (no auth needed for read-only)
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    
    params = {
        'q': keyword,
        'sort': 'new',
        'limit': 50,
        't': 'week'  # Posts from the last week
    }
    
    headers = {
        'User-Agent': 'CallFlexAI Lead Finder 1.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            leads = []
            for post in posts:
                post_data = post['data']
                
                # Filter: Only posts asking for recommendations
                title_lower = post_data['title'].lower()
                body_lower = post_data.get('selftext', '').lower()
                
                asking_keywords = ['looking for', 'need a', 'recommend', 'suggestion', 'help find']
                
                if any(kw in title_lower or kw in body_lower for kw in asking_keywords):
                    leads.append({
                        'author': post_data['author'],
                        'title': post_data['title'],
                        'body': post_data['selftext'][:200],  # First 200 chars
                        'url': f"https://reddit.com{post_data['permalink']}",
                        'created': post_data['created_utc']
                    })
            
            log(f"Reddit Finder: Found {len(leads)} potential leads.")
            return leads
        else:
            log(f"Reddit Finder: ERROR - Status {response.status_code}")
            return []
    
    except Exception as e:
        log(f"Reddit Finder: ERROR: {e}")
        return []

def save_reddit_leads_to_database(leads, client_id, service_type):
    """Saves Reddit leads to Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        log("ERROR: Cannot connect to database.")
        return
    
    for lead in leads:
        try:
            lead_data = {
                'client_id': client_id,
                'prospect_name': lead['author'],
                'source': 'reddit',
                'service_needed': service_type,
                'source_url': lead['url'],
                'notes': f"Post title: {lead['title']}",
                'status': 'new',
                'quality_score': 6  # Reddit leads are decent quality
            }
            
            supabase.table('prospect_leads').insert(lead_data).execute()
            log(f"✅ Saved Reddit lead: u/{lead['author']}")
        
        except Exception as e:
            log(f"❌ Error saving lead: {e}")

def run_reddit_finder_for_client(client):
    """Main workflow: Find leads for one client on Reddit."""
    client_id = client['id']
    niche = client['prospecting_niche']  # e.g., "Dentists"
    location = client['prospecting_location']  # e.g., "Austin TX"
    
    # Extract city from location
    city = location.split(',')[0].strip()  # "Austin"
    
    # Search Reddit
    keyword = niche.rstrip('s').lower()  # "Dentists" → "dentist"
    leads = search_reddit_for_leads(subreddit=city, keyword=keyword, location=city)
    
    if leads:
        save_reddit_leads_to_database(leads, client_id, niche)
        log(f"Reddit Finder: Completed job for {client['business_name']}")
    else:
        log("Reddit Finder: No leads found.")

# Example usage in your main orchestrator:
# from reddit_finder import run_reddit_finder_for_client
# for client in active_clients:
#     run_reddit_finder_for_client(client)
