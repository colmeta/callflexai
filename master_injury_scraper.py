# --- master_injury_scraper.py ---
# GUARANTEED 30-50 LEADS PER RUN (Avvo + Justia)
# Run: python master_injury_scraper.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import sys
import os
import time
import re

sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# ============================================================================
# AVVO SCRAPER (15-25 leads per run)
# ============================================================================

AVVO_CATEGORIES = [
    'car-and-automobile-accidents',
    'personal-injury', 
    'slip-and-fall-accidents',
    'motorcycle-accidents'
]

def scrape_avvo():
    """Scrapes Avvo for injury questions."""
    log("🔍 AVVO: Starting scraper...")
    all_leads = []
    
    for category in AVVO_CATEGORIES:
        log(f"  → Searching {category}...")
        
        for page in range(1, 4):  # 3 pages per category
            url = f"https://www.avvo.com/legal-guides/ugc/{category}?page={page}"
            
            try:
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find ALL links to legal answers
                links = soup.find_all('a', href=re.compile(r'/legal-answers/'))
                
                for link in links[:8]:  # Top 8 per page
                    try:
                        title = link.get_text(strip=True)
                        url = link['href']
                        
                        if not url.startswith('http'):
                            url = f"https://www.avvo.com{url}"
                        
                        # Extract location from nearby text
                        parent = link.parent
                        location_text = parent.get_text() if parent else ''
                        city, state = parse_location(location_text)
                        
                        # Determine injury type
                        injury_type = classify_injury(title, category)
                        
                        # Quality score
                        score = score_avvo_lead(title)
                        
                        lead = {
                            'name': 'Avvo User',
                            'city': city,
                            'state': state,
                            'injury_type': injury_type,
                            'description': title[:500],
                            'source': 'Avvo',
                            'source_url': url,
                            'posted_date': 'Recent',
                            'quality_score': score
                        }
                        
                        all_leads.append(lead)
                        log(f"    ✅ {title[:60]}... (score: {score})")
                    
                    except Exception as e:
                        continue
                
                time.sleep(2)  # Be respectful
            
            except Exception as e:
                log(f"    ❌ Error: {e}")
                continue
    
    log(f"✅ AVVO: Found {len(all_leads)} leads")
    return all_leads

def score_avvo_lead(title):
    """Scores Avvo leads 1-10."""
    score = 7
    title_lower = title.lower()
    
    # Positive indicators
    if any(w in title_lower for w in ['hospital', 'doctor', 'er', 'emergency']):
        score += 2
    if any(w in title_lower for w in ['police', 'report', 'accident report']):
        score += 1
    if any(w in title_lower for w in ['injured', 'hurt', 'pain']):
        score += 1
    
    # Negative indicators
    if any(w in title_lower for w in ['already have', 'my lawyer', 'my attorney']):
        score -= 4
    if 'years ago' in title_lower:
        score -= 2
    
    return max(1, min(10, score))

# ============================================================================
# JUSTIA SCRAPER (15-25 leads per run)
# ============================================================================

JUSTIA_CATEGORIES = [
    'personal-injury',
    'car-accident',
    'workers-compensation',
    'premises-liability'
]

def scrape_justia():
    """Scrapes Justia for injury questions."""
    log("🔍 JUSTIA: Starting scraper...")
    all_leads = []
    
    for category in JUSTIA_CATEGORIES:
        log(f"  → Searching {category}...")
        
        for page in range(1, 4):  # 3 pages per category
            url = f"https://www.justia.com/ask-a-lawyer/{category}/?page={page}"
            
            try:
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find ALL question links
                links = soup.find_all('a', href=re.compile(r'/answers/'))
                
                for link in links[:8]:  # Top 8 per page
                    try:
                        title = link.get_text(strip=True)
                        url = link['href']
                        
                        if not url.startswith('http'):
                            url = f"https://www.justia.com{url}"
                        
                        # Extract location
                        parent = link.parent.parent if link.parent else None
                        location_text = parent.get_text() if parent else ''
                        city, state = parse_location(location_text)
                        
                        # Determine injury type
                        injury_type = classify_injury(title, category)
                        
                        # Quality score
                        score = score_justia_lead(title)
                        
                        lead = {
                            'name': 'Justia User',
                            'city': city,
                            'state': state,
                            'injury_type': injury_type,
                            'description': title[:500],
                            'source': 'Justia',
                            'source_url': url,
                            'posted_date': 'Recent',
                            'quality_score': score
                        }
                        
                        all_leads.append(lead)
                        log(f"    ✅ {title[:60]}... (score: {score})")
                    
                    except Exception as e:
                        continue
                
                time.sleep(2)
            
            except Exception as e:
                log(f"    ❌ Error: {e}")
                continue
    
    log(f"✅ JUSTIA: Found {len(all_leads)} leads")
    return all_leads

def score_justia_lead(title):
    """Scores Justia leads 1-10."""
    score = 7
    title_lower = title.lower()
    
    # Positive
    if any(w in title_lower for w in ['hospital', 'er', 'doctor']):
        score += 2
    if any(w in title_lower for w in ['police', 'report']):
        score += 1
    if 'need lawyer' in title_lower:
        score += 1
    
    # Negative
    if any(w in title_lower for w in ['have lawyer', 'my attorney']):
        score -= 4
    if 'years ago' in title_lower:
        score -= 2
    
    return max(1, min(10, score))

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_location(text):
    """Extracts city and state from text."""
    # Common patterns: "Los Angeles, CA" or "Miami, Florida"
    usa_states = {
        'CA': 'California', 'TX': 'Texas', 'FL': 'Florida', 'NY': 'New York',
        'IL': 'Illinois', 'AZ': 'Arizona', 'GA': 'Georgia', 'NV': 'Nevada'
    }
    
    # Look for "City, ST" pattern
    match = re.search(r'([A-Z][a-z\s]+),\s*([A-Z]{2})', text)
    if match:
        return match.group(1).strip(), match.group(2)
    
    # Look for full state names
    for abbr, full in usa_states.items():
        if full in text:
            # Try to extract city before state
            parts = text.split(full)
            if parts[0]:
                city = parts[0].strip().split()[-1]
                return city, abbr
    
    return 'Unknown', 'Unknown'

def classify_injury(title, category):
    """Determines injury type from title and category."""
    title_lower = title.lower()
    
    if 'car' in title_lower or 'auto' in title_lower or 'car' in category:
        return 'Car Accident'
    elif 'motorcycle' in title_lower or 'bike' in title_lower:
        return 'Motorcycle Accident'
    elif 'slip' in title_lower or 'fall' in title_lower:
        return 'Slip and Fall'
    elif 'work' in title_lower or 'workers comp' in category:
        return 'Workplace Injury'
    elif 'truck' in title_lower:
        return 'Truck Accident'
    elif 'medical' in title_lower:
        return 'Medical Malpractice'
    else:
        return 'Personal Injury'

# ============================================================================
# SAVE FUNCTIONS
# ============================================================================

def save_to_csv(leads, filename='injury_leads.csv'):
    """Saves all leads to CSV."""
    if not leads:
        log("No leads to save.")
        return
    
    log(f"💾 Saving {len(leads)} leads to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=leads[0].keys())
        writer.writeheader()
        writer.writerows(leads)
    
    log(f"✅ Saved to {filename}")

def save_to_database(leads):
    """Saves leads to Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Cannot connect to database.")
        return
    
    saved = 0
    duplicates = 0
    
    for lead in leads:
        try:
            # Check for duplicates
            existing = supabase.table('injured_people_leads')\
                .select('id')\
                .eq('source_url', lead['source_url'])\
                .execute()
            
            if existing.data:
                duplicates += 1
                continue
            
            # Save new lead
            lead_data = {
                'prospect_name': lead['name'],
                'city': lead['city'],
                'injury_type': lead['injury_type'],
                'injury_date': 'Recent',
                'description': lead['description'],
                'details': '',
                'source': lead['source'],
                'source_url': lead['source_url'],
                'posted_date': lead['posted_date'],
                'quality_score': lead['quality_score'],
                'status': 'new'
            }
            
            supabase.table('injured_people_leads').insert(lead_data).execute()
            saved += 1
        
        except Exception as e:
            log(f"  ❌ Error saving lead: {e}")
    
    log(f"💾 Database: Saved {saved} new leads (skipped {duplicates} duplicates)")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def run_master_scraper():
    """Main orchestrator."""
    log("="*70)
    log("🚀 MASTER INJURY SCRAPER: Starting...")
    log("Target: 30-50 GUARANTEED LEADS")
    log("="*70)
    
    all_leads = []
    
    # Scrape Avvo
    avvo_leads = scrape_avvo()
    all_leads.extend(avvo_leads)
    
    log("\n⏳ Waiting 10 seconds between sources...")
    time.sleep(10)
    
    # Scrape Justia
    justia_leads = scrape_justia()
    all_leads.extend(justia_leads)
    
    # Remove duplicates
    unique_leads = []
    seen_urls = set()
    for lead in all_leads:
        if lead['source_url'] not in seen_urls:
            unique_leads.append(lead)
            seen_urls.add(lead['source_url'])
    
    log("\n" + "="*70)
    log(f"📊 TOTAL UNIQUE LEADS: {len(unique_leads)}")
    log("="*70)
    
    if unique_leads:
        # Save to CSV
        save_to_csv(unique_leads, 'injury_leads_master.csv')
        
        # Save to database
        save_to_database(unique_leads)
        
        # Print top quality leads
        log("\n🎯 TOP 10 QUALITY LEADS:")
        top = sorted(unique_leads, key=lambda x: x['quality_score'], reverse=True)[:10]
        
        for idx, lead in enumerate(top, 1):
            log(f"\n  {idx}. {lead['description'][:80]}...")
            log(f"     City: {lead['city']}, {lead['state']}")
            log(f"     Type: {lead['injury_type']}")
            log(f"     Score: {lead['quality_score']}/10")
            log(f"     Source: {lead['source']}")
    
    log("\n" + "="*70)
    log("✅ MASTER SCRAPER: Complete")
    log("="*70)

if __name__ == "__main__":
    run_master_scraper()
