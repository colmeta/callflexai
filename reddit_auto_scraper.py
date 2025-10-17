# --- reddit_auto_scraper.py ---
# Automatically finds injured people seeking PI lawyers on Reddit
# Runs every 6 hours via GitHub Actions

import requests
import csv
from datetime import datetime, timedelta
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# Top USA cities to monitor
USA_CITIES = [
    'LosAngeles', 'Miami', 'Houston', 'Chicago', 'Phoenix',
    'Philadelphia', 'SanAntonio', 'SanDiego', 'Dallas', 'Austin',
    'Jacksonville', 'FortWorth', 'Columbus', 'Charlotte', 'SanFrancisco',
    'Indianapolis', 'Seattle', 'Denver', 'Boston', 'Portland'
]

# Keywords that indicate someone needs a PI lawyer
INJURY_KEYWORDS = [
    'car accident', 'hit by car', 'rear ended', 'motorcycle accident',
    'truck accident', 'slip and fall', 'injured at work', 'workplace injury',
    'need a lawyer', 'should i get a lawyer', 'personal injury attorney',
    'hurt in accident', 'medical bills', 'insurance wont pay'
]

def search_reddit_for_injured_people(city_subreddit, days_back=7):
    """
    Searches a city's subreddit for people asking about injury/accident lawyers.
    
    Args:
        city_subreddit (str): e.g., "LosAngeles"
        days_back (int): How many days back to search
    
    Returns:
        list: Found posts with injured people
    """
    log(f"Reddit Scraper: Searching r/{city_subreddit}...")
    
    url = f"https://www.reddit.com/r/{city_subreddit}/search.json"
    
    # Search for each injury keyword
    all_leads = []
    
    for keyword in INJURY_KEYWORDS:
        params = {
            'q': keyword,
            'sort': 'new',
            'limit': 25,
            't': 'week',  # Last week only
            'restrict_sr': 'on'  # Only this subreddit
        }
        
        headers = {
            'User-Agent': 'PILeadFinder/1.0'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                for post in posts:
                    post_data = post['data']
                    
                    # Filter: Must be asking for help, not just discussing
                    title_lower = post_data['title'].lower()
                    body_lower = post_data.get('selftext', '').lower()
                    
                    # Skip if it's a news article or discussion
                    skip_keywords = ['news', 'article', 'video', 'just saw', 'did anyone']
                    if any(skip in title_lower for skip in skip_keywords):
                        continue
                    
                    # Must contain words indicating they need help
                    help_keywords = ['i was', 'my', 'need', 'looking for', 'should i', 'what do i']
                    if not any(help in title_lower or help in body_lower for help in help_keywords):
                        continue
                    
                    # Check if post is recent (within days_back)
                    post_time = datetime.fromtimestamp(post_data['created_utc'])
                    if datetime.now() - post_time > timedelta(days=days_back):
                        continue
                    
                    # Extract injury details
                    injury_type = 'Unknown'
                    if 'car' in title_lower or 'car' in body_lower:
                        injury_type = 'Car Accident'
                    elif 'motorcycle' in title_lower or 'bike' in body_lower:
                        injury_type = 'Motorcycle Accident'
                    elif 'slip' in title_lower or 'fall' in title_lower:
                        injury_type = 'Slip and Fall'
                    elif 'work' in title_lower or 'job' in body_lower:
                        injury_type = 'Workplace Injury'
                    
                    lead = {
                        'name': f"u/{post_data['author']}",
                        'city': city_subreddit,
                        'injury_type': injury_type,
                        'injury_date': 'Recent (within 7 days)',
                        'description': post_data['title'],
                        'details': post_data['selftext'][:300],  # First 300 chars
                        'source': 'Reddit',
                        'source_url': f"https://reddit.com{post_data['permalink']}",
                        'posted_date': post_time.strftime('%Y-%m-%d'),
                        'quality_score': calculate_quality_score(post_data)
                    }
                    
                    all_leads.append(lead)
                
                log(f"  Found {len(posts)} posts for keyword '{keyword}'")
        
        except Exception as e:
            log(f"  ERROR searching for '{keyword}': {e}")
            continue
    
    # Remove duplicates (same URL)
    unique_leads = []
    seen_urls = set()
    for lead in all_leads:
        if lead['source_url'] not in seen_urls:
            unique_leads.append(lead)
            seen_urls.add(lead['source_url'])
    
    log(f"Reddit Scraper: Found {len(unique_leads)} unique leads in r/{city_subreddit}")
    return unique_leads

def calculate_quality_score(post_data):
    """
    Scores a Reddit post from 1-10 based on indicators of a good PI lead.
    """
    score = 5  # Base score
    
    title = post_data['title'].lower()
    body = post_data.get('selftext', '').lower()
    text = title + ' ' + body
    
    # Positive indicators (add points)
    if 'doctor' in text or 'hospital' in text or 'er' in text:
        score += 2  # Sought medical treatment
    
    if 'police report' in text or 'cop' in text:
        score += 1  # Police involved
    
    if any(word in text for word in ['hurt', 'injured', 'pain', 'broken']):
        score += 1  # Clear injury
    
    if any(word in text for word in ['other driver', 'not my fault', 'they hit me']):
        score += 1  # Clear liability
    
    if 'need a lawyer' in text or 'should i get' in text:
        score += 2  # Actively seeking legal help
    
    # Negative indicators (subtract points)
    if 'already have' in text or 'my lawyer' in text:
        score -= 5  # Already has representation
    
    if any(word in text for word in ['years ago', 'long time', 'old']):
        score -= 2  # Old injury (statute issues)
    
    if 'my fault' in text or 'i caused' in text:
        score -= 3  # No clear liability
    
    return max(1, min(10, score))  # Clamp between 1-10

def save_leads_to_csv(leads, filename='reddit_injured_leads.csv'):
    """Saves leads to CSV for manual review."""
    if not leads:
        log("No leads to save.")
        return
    
    log(f"Saving {len(leads)} leads to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=leads[0].keys())
        writer.writeheader()
        writer.writerows(leads)
    
    log(f"✅ Saved to {filename}")

def save_leads_to_database(leads):
    """Saves leads directly to Supabase for automation."""
    supabase = get_supabase_client()
    if not supabase:
        log("ERROR: Cannot connect to database. Saving to CSV only.")
        return
    
    saved_count = 0
    
    for lead in leads:
        try:
            # Check if this lead already exists (by source_url)
            existing = supabase.table('injured_people_leads').select('id').eq('source_url', lead['source_url']).execute()
            
            if existing.data:
                log(f"  Duplicate: {lead['name']} (already in database)")
                continue
            
            # Save new lead
            lead_data = {
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
                'status': 'new',
                'matched_to_firm': None
            }
            
            supabase.table('injured_people_leads').insert(lead_data).execute()
            saved_count += 1
            log(f"  ✅ Saved: {lead['name']} (score: {lead['quality_score']})")
        
        except Exception as e:
            log(f"  ❌ Error saving {lead['name']}: {e}")
    
    log(f"Database: Saved {saved_count} new leads")

def run_reddit_scraper():
    """Main function: Scrapes all USA city subreddits."""
    log("="*60)
    log("REDDIT AUTO SCRAPER: Starting...")
    log("="*60)
    
    all_leads = []
    
    # Scrape top 10 cities (you can increase this)
    for city in USA_CITIES[:10]:
        leads = search_reddit_for_injured_people(city, days_back=7)
        all_leads.extend(leads)
        
        # Be respectful: 2-second delay between cities
        import time
        time.sleep(2)
    
    log(f"\nTotal leads found: {len(all_leads)}")
    
    if all_leads:
        # Save to CSV for your review
        save_leads_to_csv(all_leads)
        
        # Save to database for automation
        save_leads_to_database(all_leads)
        
        # Print summary by city
        from collections import Counter
        city_counts = Counter(lead['city'] for lead in all_leads)
        log("\nLeads by city:")
        for city, count in city_counts.most_common():
            log(f"  {city}: {count} leads")
    
    log("="*60)
    log("REDDIT AUTO SCRAPER: Complete")
    log("="*60)

if __name__ == "__main__":
    run_reddit_scraper()
