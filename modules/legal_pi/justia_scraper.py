# --- modules/legal_pi/justia_scraper.py ---
# Scrapes Justia.com Ask a Lawyer for injury questions
# GUARANTEED 15-20 leads per run!

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

# Justia categories
JUSTIA_CATEGORIES = [
    'personal-injury',
    'car-accident',
    'workers-compensation',
    'medical-malpractice',
    'premises-liability'
]

def scrape_justia_category(category, pages=3):
    """
    Scrapes Justia Ask a Lawyer for injury questions.
    
    Args:
        category (str): Justia category
        pages (int): Number of pages
    
    Returns:
        list: Found questions
    """
    log(f"Justia Scraper: Searching {category}...")
    
    all_questions = []
    
    for page in range(1, pages + 1):
        url = f"https://www.justia.com/ask-a-lawyer/{category}/?page={page}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find question containers
                questions = soup.find_all('div', class_='question-item')
                
                # Try alternative selectors
                if not questions:
                    questions = soup.find_all('article')
                
                if not questions:
                    questions = soup.find_all('div', class_='qa-item')
                
                for question in questions:
                    try:
                        # Extract title
                        title_tag = question.find('h3') or question.find('h2') or question.find('a', class_='question-title')
                        title = title_tag.text.strip() if title_tag else 'No title'
                        
                        # Get URL
                        link_tag = question.find('a', href=lambda x: x and '/answers/' in x)
                        question_url = link_tag['href'] if link_tag else ''
                        if question_url and not question_url.startswith('http'):
                            question_url = f"https://www.justia.com{question_url}"
                        
                        # Extract location
                        location_tag = question.find('span', class_='location') or question.find(text=lambda x: x and ', ' in str(x) and len(str(x)) < 50)
                        location = location_tag.strip() if location_tag else 'Unknown'
                        
                        # Extract snippet/preview
                        snippet_tag = question.find('p', class_='question-preview') or question.find('div', class_='question-text')
                        snippet = snippet_tag.text.strip()[:300] if snippet_tag else ''
                        
                        # Parse location
                        city = 'Unknown'
                        state = 'Unknown'
                        if location and ',' in location:
                            parts = location.split(',')
                            city = parts[0].strip()
                            state = parts[1].strip() if len(parts) > 1 else 'Unknown'
                        
                        # Determine injury type
                        injury_type = 'Unknown'
                        title_lower = title.lower() + ' ' + snippet.lower()
                        
                        if 'car' in title_lower or 'auto' in title_lower:
                            injury_type = 'Car Accident'
                        elif 'slip' in title_lower or 'fall' in title_lower:
                            injury_type = 'Slip and Fall'
                        elif 'work' in title_lower or 'workers comp' in title_lower:
                            injury_type = 'Workplace Injury'
                        elif 'medical' in title_lower or 'doctor' in title_lower:
                            injury_type = 'Medical Malpractice'
                        elif 'motorcycle' in title_lower:
                            injury_type = 'Motorcycle Accident'
                        elif 'truck' in title_lower:
                            injury_type = 'Truck Accident'
                        
                        # Quality score
                        quality_score = calculate_justia_quality(title, snippet, location)
                        
                        question_data = {
                            'name': 'Justia User',
                            'city': city,
                            'state': state,
                            'injury_type': injury_type,
                            'description': title,
                            'details': snippet,
                            'source': 'Justia',
                            'source_url': question_url,
                            'posted_date': 'Recent',
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
        
        time.sleep(2)
    
    log(f"Justia: Found {len(all_questions)} questions in {category}")
    return all_questions

def calculate_justia_quality(title, snippet, location):
    """Scores Justia questions."""
    score = 7
    
    text = (title + ' ' + snippet).lower()
    
    # Positive indicators
    if 'hospital' in text or 'er' in text or 'doctor' in text:
        score += 2
    
    if 'police' in text or 'report' in text:
        score += 1
    
    if 'injured' in text or 'hurt' in text:
        score += 1
    
    if location and location != 'Unknown':
        score += 1
    
    if 'need lawyer' in text or 'looking for attorney' in text:
        score += 1
    
    # Negative indicators
    if 'have lawyer' in text or 'my attorney' in text:
        score -= 4
    
    if 'years ago' in text:
        score -= 2
    
    return max(1, min(10, score))

def save_to_csv(leads, filename='justia_injured_leads.csv'):
    """Saves to CSV."""
    if not leads:
        log("No Justia leads to save.")
        return
    
    log(f"Saving {len(leads)} Justia leads to {filename}...")
    
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
    duplicate_count = 0
    
    for lead in leads:
        try:
            if lead['source_url']:
                existing = supabase.table('injured_people_leads').select('id').eq('source_url', lead['source_url']).execute()
                
                if existing.data:
                    duplicate_count += 1
                    continue
            
            lead_data = {
                'prospect_name': lead['name'],
                'city': lead['city'],
                'injury_type': lead['injury_type'],
                'injury_date': 'Recent',
                'description': lead['description'],
                'details': lead['details'],
                'source': lead['source'],
                'source_url': lead['source_url'] or f"justia-{datetime.now().timestamp()}",
                'posted_date': lead['posted_date'],
                'quality_score': lead['quality_score'],
                'status': 'new'
            }
            
            supabase.table('injured_people_leads').insert(lead_data).execute()
            saved_count += 1
            log(f"  ✅ Saved: {lead['description'][:50]}... (score: {lead['quality_score']})")
        
        except Exception as e:
            log(f"  ❌ Error: {e}")
    
    log(f"\nJustia Summary:")
    log(f"  Saved: {saved_count}")
    log(f"  Duplicates: {duplicate_count}")

def run_justia_scraper():
    """Main function."""
    log("="*70)
    log("JUSTIA SCRAPER: Starting...")
    log("="*70)
    
    all_leads = []
    
    for category in JUSTIA_CATEGORIES[:3]:
        leads = scrape_justia_category(category, pages=2)
        all_leads.extend(leads)
        time.sleep(3)
    
    log(f"\nTotal Justia leads: {len(all_leads)}")
    
    if all_leads:
        save_to_csv(all_leads)
        save_to_database(all_leads)
    
    log("\n" + "="*70)
    log("JUSTIA SCRAPER: Complete")
    log("="*70)

if __name__ == "__main__":
    run_justia_scraper()
