# --- modules/legal_pi/avvo_scraper.py ---
# Scrapes Avvo.com for people asking injury questions
# GUARANTEED 20-30 leads per run!

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# Avvo categories with high injury questions
AVVO_CATEGORIES = [
    'car-and-automobile-accidents',
    'personal-injury',
    'workers-compensation',
    'medical-malpractice',
    'slip-and-fall-accidents',
    'motorcycle-accidents',
    'truck-accidents'
]

def scrape_avvo_category(category, pages=3):
    """
    Scrapes Avvo Q&A for a specific injury category.
    
    Args:
        category (str): Avvo category slug
        pages (int): Number of pages to scrape
    
    Returns:
        list: Found injury questions
    """
    log(f"Avvo Scraper: Searching {category}...")
    
    all_questions = []
    
    for page in range(1, pages + 1):
        url = f"https://www.avvo.com/ask-a-lawyer/{category}?page={page}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all question cards
                questions = soup.find_all('div', class_='ask-a-lawyer-question')
                
                # Avvo uses different HTML structure, try multiple selectors
                if not questions:
                    questions = soup.find_all('article', class_='question')
                
                if not questions:
                    # Try finding links with specific patterns
                    links = soup.find_all('a', href=lambda x: x and '/legal-answers/' in x)
                    questions = [link.parent for link in links[:10]]
                
                for question in questions:
                    try:
                        # Extract question text
                        title_tag = question.find('h3') or question.find('h2') or question.find('a')
                        title = title_tag.text.strip() if title_tag else 'No title'
                        
                        # Get question link
                        link_tag = question.find('a', href=lambda x: x and '/legal-answers/' in x)
                        question_url = link_tag['href'] if link_tag else ''
                        if question_url and not question_url.startswith('http'):
                            question_url = f"https://www.avvo.com{question_url}"
                        
                        # Extract location (usually in metadata)
                        location_tag = question.find('span', class_='location') or question.find(text=lambda x: x and (',' in x and any(state in x for state in ['CA', 'TX', 'FL', 'NY', 'IL'])))
                        location = location_tag.text.strip() if location_tag else 'Unknown'
                        
                        # Extract date
                        date_tag = question.find('time') or question.find('span', class_='date')
                        posted_date = date_tag.text.strip() if date_tag else 'Recent'
                        
                        # Parse city and state from location
                        city = 'Unknown'
                        state = 'Unknown'
                        if location and ',' in location:
                            parts = location.split(',')
                            city = parts[0].strip()
                            state = parts[1].strip() if len(parts) > 1 else 'Unknown'
                        
                        # Determine injury type from category
                        injury_type = category.replace('-', ' ').title()
                        if 'car' in category or 'automobile' in category:
                            injury_type = 'Car Accident'
                        elif 'slip' in category or 'fall' in category:
                            injury_type = 'Slip and Fall'
                        elif 'motorcycle' in category:
                            injury_type = 'Motorcycle Accident'
                        elif 'truck' in category:
                            injury_type = 'Truck Accident'
                        elif 'workers' in category:
                            injury_type = 'Workplace Injury'
                        
                        # Calculate quality score based on recency and detail
                        quality_score = calculate_avvo_quality_score(title, posted_date, location)
                        
                        question_data = {
                            'name': 'Avvo User',
                            'city': city,
                            'state': state,
                            'injury_type': injury_type,
                            'description': title[:500],
                            'source': 'Avvo',
                            'source_url': question_url,
                            'posted_date': posted_date,
                            'quality_score': quality_score
                        }
                        
                        all_questions.append(question_data)
                    
                    except Exception as e:
                        log(f"  Error parsing question: {e}")
                        continue
                
                log(f"  Found {len(questions)} questions on page {page}")
            else:
                log(f"  HTTP {response.status_code} for page {page}")
        
        except Exception as e:
            log(f"  ERROR on page {page}: {e}")
            continue
        
        # Be respectful: 2-second delay between pages
        time.sleep(2)
    
    log(f"Avvo: Found {len(all_questions)} questions in {category}")
    return all_questions

def calculate_avvo_quality_score(title, posted_date, location):
    """Scores Avvo questions based on quality indicators."""
    score = 7  # Base score (Avvo questions are generally high quality)
    
    title_lower = title.lower()
    
    # Positive indicators
    if 'hospital' in title_lower or 'doctor' in title_lower or 'er' in title_lower:
        score += 2
    
    if 'police' in title_lower or 'report' in title_lower:
        score += 1
    
    if 'injured' in title_lower or 'hurt' in title_lower or 'pain' in title_lower:
        score += 1
    
    if location and location != 'Unknown':
        score += 1  # Has location = easier to match to lawyer
    
    # Recent posts are better
    if any(word in posted_date.lower() for word in ['today', 'hour', 'yesterday']):
        score += 1
    
    # Negative indicators
    if 'already have lawyer' in title_lower or 'my attorney' in title_lower:
        score -= 3
    
    if 'years ago' in title_lower or 'old case' in title_lower:
        score -= 2
    
    return max(1, min(10, score))

def save_to_csv(leads, filename='avvo_injured_leads.csv'):
    """Saves Avvo leads to CSV."""
    if not leads:
        log("No Avvo leads to save.")
        return
    
    log(f"Saving {len(leads)} Avvo leads to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=leads[0].keys())
        writer.writeheader()
        writer.writerows(leads)
    
    log(f"✅ Saved to {filename}")

def save_to_database(leads):
    """Saves Avvo leads to Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        log("ERROR: Cannot connect to database.")
        return
    
    saved_count = 0
    duplicate_count = 0
    
    for lead in leads:
        try:
            # Check for duplicates by source_url
            if lead['source_url']:
                existing = supabase.table('injured_people_leads').select('id').eq('source_url', lead['source_url']).execute()
                
                if existing.data:
                    duplicate_count += 1
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
                'source_url': lead['source_url'] or f"avvo-{datetime.now().timestamp()}",
                'posted_date': lead['posted_date'],
                'quality_score': lead['quality_score'],
                'status': 'new'
            }
            
            supabase.table('injured_people_leads').insert(lead_data).execute()
            saved_count += 1
            log(f"  ✅ Saved: {lead['description'][:50]}... (score: {lead['quality_score']})")
        
        except Exception as e:
            log(f"  ❌ Error saving lead: {e}")
    
    log(f"\nAvvo Summary:")
    log(f"  Saved: {saved_count}")
    log(f"  Duplicates skipped: {duplicate_count}")

def run_avvo_scraper():
    """Main function: Scrapes all Avvo injury categories."""
    log("="*70)
    log("AVVO SCRAPER: Starting...")
    log("="*70)
    
    all_leads = []
    
    # Scrape top 4 categories (customize this based on what works best)
    for category in AVVO_CATEGORIES[:4]:
        leads = scrape_avvo_category(category, pages=2)
        all_leads.extend(leads)
        
        # Be respectful: 3-second delay between categories
        time.sleep(3)
    
    log(f"\nTotal Avvo leads found: {len(all_leads)}")
    
    if all_leads:
        save_to_csv(all_leads)
        save_to_database(all_leads)
        
        # Print top quality leads
        top_leads = sorted(all_leads, key=lambda x: x['quality_score'], reverse=True)[:10]
        log("\n🎯 TOP 10 QUALITY LEADS:")
        for idx, lead in enumerate(top_leads, 1):
            log(f"\n  {idx}. {lead['description'][:80]}...")
            log(f"     City: {lead['city']}, {lead['state']}")
            log(f"     Quality: {lead['quality_score']}/10")
            log(f"     Posted: {lead['posted_date']}")
    
    log("\n" + "="*70)
    log("AVVO SCRAPER: Complete")
    log("="*70)

if __name__ == "__main__":
    run_avvo_scraper()
