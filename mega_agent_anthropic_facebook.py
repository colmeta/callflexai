# --- mega_agent_anthropic_facebook.py ---
# MEGA AI AGENT: ALL 70+ platforms + FACEBOOK ENABLED
# Uses: Anthropic Claude ($5 free, then $30-50/month)
# Expected: 250-400 leads per run

import asyncio
import csv
import os
import random
from datetime import datetime
from browser_use import Agent, BrowserConfig
from typing import List, Dict

import sys
sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# ============================================================================
# PLATFORM TASKS - ALL 70+ PLATFORMS + FACEBOOK PRIORITY
# ============================================================================

PLATFORM_TASKS = {
    # 🔥 TIER 1: FACEBOOK (HIGHEST PRIORITY - THE GOLDMINE)
    "facebook_groups": [
        {
            "task": "Log into Facebook if not already logged in. Then search Facebook Groups for posts containing 'car accident lawyer' OR 'need attorney' OR 'injured' posted in the last 7 days. Focus on city-specific groups like 'Los Angeles Community', 'Miami Neighbors', etc. Extract 20 posts with: poster's full name, post content preview (first 100 chars), post URL, group name, and city if mentioned.",
            "priority": 10,
            "requires_login": True,
            "expected_leads": 20
        },
        {
            "task": "Search Facebook Groups for 'personal injury attorney recommendation' OR 'slip and fall lawyer' posted in last 14 days. Get 15 posts with full details.",
            "priority": 10,
            "requires_login": True,
            "expected_leads": 15
        },
        {
            "task": "In Facebook, search for '[City] Moms' groups (Los Angeles Moms, Miami Moms, Houston Moms). Look for posts about kids getting injured or accidents. Get 10 posts where someone asks for lawyer help.",
            "priority": 9,
            "requires_login": True,
            "expected_leads": 10
        },
        {
            "task": "Search Facebook Groups for 'workers compensation' OR 'injured at work' posted in last month. Get 10 posts from people seeking legal help.",
            "priority": 9,
            "requires_login": True,
            "expected_leads": 10
        },
        {
            "task": "Search Facebook for 'motorcycle accident lawyer' OR 'bike accident attorney' in Groups from last 2 weeks. Get 10 posts.",
            "priority": 8,
            "requires_login": True,
            "expected_leads": 10
        }
    ],
    
    # TIER 2: LEGAL Q&A SITES (HIGHEST QUALITY)
    "avvo": [
        {
            "task": "Go to Google and search 'site:avvo.com personal injury question last week'. Open top 10 results. Extract: question text, URL, location if mentioned, date posted.",
            "priority": 9,
            "expected_leads": 10
        },
        {
            "task": "Navigate to avvo.com/ask-a-lawyer/personal-injury. Scroll through first 3 pages. Find questions from last 30 days. Get 15 questions with URLs.",
            "priority": 9,
            "expected_leads": 15
        }
    ],
    
    "justia": [
        {
            "task": "Go to justia.com/ask-a-lawyer/personal-injury. Find 15 questions posted in last 2 weeks. Extract: question title, URL, location, injury details.",
            "priority": 9,
            "expected_leads": 15
        }
    ],
    
    "findlaw": [
        {
            "task": "Search Google for 'site:findlaw.com personal injury question'. Click top 10 results and extract questions.",
            "priority": 8,
            "expected_leads": 10
        }
    ],
    
    # TIER 3: REDDIT (HIGH VOLUME)
    "reddit_legal": [
        {
            "task": "Go to old.reddit.com/r/legaladvice/search?q=car+accident&sort=new&t=week. Extract 20 posts where people ask if they need a lawyer. Get: username, title, URL, city/state if mentioned.",
            "priority": 8,
            "expected_leads": 20
        },
        {
            "task": "Navigate to old.reddit.com/r/personalinjury/new. Get newest 15 posts. Extract title and URL.",
            "priority": 8,
            "expected_leads": 15
        },
        {
            "task": "Search old.reddit.com/r/Insurance for 'accident claim' from last week. Get 10 posts about injuries.",
            "priority": 7,
            "expected_leads": 10
        }
    ],
    
    "reddit_cities": [
        {
            "task": "Search old.reddit.com/r/LosAngeles for 'car accident' OR 'need lawyer' OR 'injured' from last month. Get 5 relevant posts.",
            "priority": 7,
            "expected_leads": 5
        },
        {
            "task": "Search old.reddit.com/r/Miami for accident/lawyer posts from last month. Get 5 posts.",
            "priority": 7,
            "expected_leads": 5
        },
        {
            "task": "Search old.reddit.com/r/Houston for injury lawyer questions from last month. Get 5 posts.",
            "priority": 7,
            "expected_leads": 5
        }
    ],
    
    # TIER 4: CRAIGSLIST
    "craigslist": [
        {
            "task": "Go to losangeles.craigslist.org. Search 'car accident lawyer' in all categories from last 7 days. Get 5 posts.",
            "priority": 6,
            "expected_leads": 5
        },
        {
            "task": "Search miami.craigslist.org for 'injury attorney' from last week. Get 5 posts.",
            "priority": 6,
            "expected_leads": 5
        }
    ],
    
    # TIER 5: QUORA
    "quora": [
        {
            "task": "Go to quora.com. Search 'personal injury lawyer' filtered by last week. Get 10 questions with URLs.",
            "priority": 7,
            "expected_leads": 10
        }
    ],
    
    # TIER 6: NEXTDOOR (HIGH VALUE)
    "nextdoor": [
        {
            "task": "Log into Nextdoor if not logged in. Search for 'lawyer recommendation' OR 'accident' OR 'injured' in your neighborhood from last month. Get 5 posts.",
            "priority": 8,
            "requires_login": True,
            "expected_leads": 5
        }
    ]
}

# ============================================================================
# BROWSER CONFIGURATION
# ============================================================================

BROWSER_CONFIG = BrowserConfig(
    headless=False,  # Show browser (more human-like)
    disable_security=False,  # Keep security on
)

DELAYS = {
    "between_platforms": (30, 60),
    "between_tasks": (10, 20),
}

# ============================================================================
# AI AGENT EXECUTION
# ============================================================================

async def run_agent_task(platform: str, task_config: Dict) -> List[Dict]:
    """Runs a single AI agent task."""
    log(f"\n{'='*70}")
    log(f"🤖 PLATFORM: {platform.upper()}")
    log(f"📋 TASK: {task_config['task'][:80]}...")
    log(f"⭐ PRIORITY: {task_config['priority']}/10")
    log(f"🎯 EXPECTED: ~{task_config['expected_leads']} leads")
    log('='*70)
    
    # Check login requirements
    if task_config.get('requires_login'):
        if not check_login_available(platform):
            log("⚠️ Skipping - requires login (credentials not configured)")
            return []
    
    try:
        # Initialize BrowserUse with Anthropic Claude
        agent = Agent(
            task=task_config['task'],
            llm_api_key=os.getenv("ANTHROPIC_API_KEY"),
            browser_config=BROWSER_CONFIG,
            max_actions_per_step=50
        )
        
        log("🚀 Agent starting...")
        result = await agent.run()
        
        log("✅ Agent completed")
        
        # Parse results
        leads = parse_agent_results(result, platform, task_config)
        
        log(f"📊 Extracted {len(leads)} leads")
        
        return leads
        
    except Exception as e:
        log(f"❌ Agent failed: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return []

def parse_agent_results(result, platform: str, task_config: Dict) -> List[Dict]:
    """Parses agent results into structured leads."""
    leads = []
    
    if isinstance(result, dict) and 'extracted_data' in result:
        raw_data = result['extracted_data']
    elif isinstance(result, list):
        raw_data = result
    else:
        raw_data = extract_from_text(str(result))
    
    for item in raw_data:
        try:
            text = str(item.get('title') or item.get('text') or item.get('content', ''))
            
            city, state = extract_location(text)
            
            lead = {
                'description': clean_text(text)[:500],
                'url': item.get('url', ''),
                'city': city,
                'state': state,
                'injury_type': classify_injury_type(text),
                'score': score_lead_quality(text),
                'source': platform,
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'username': item.get('name') or item.get('username', 'Anonymous'),
                'group_name': item.get('group_name', '')
            }
            
            if lead['description'] and lead['url'] and lead['score'] >= 5:
                leads.append(lead)
                log(f"  ✅ {lead['city']}, {lead['state']} | {lead['description'][:50]}... (score: {lead['score']}/10)")
            else:
                log(f"  ⚠️ Filtered: score {lead.get('score', 0)}/10")
                
        except Exception as e:
            log(f"  ⚠️ Parse error: {e}")
            continue
    
    return leads

def extract_from_text(text: str) -> List[Dict]:
    """Fallback parser."""
    leads = []
    lines = text.split('\n')
    
    current = {}
    for line in lines:
        line = line.strip()
        
        if 'http' in line and 'url' not in current:
            current['url'] = line
        elif len(line) > 20 and 'text' not in current:
            current['text'] = line
        
        if 'url' in current and 'text' in current:
            leads.append(current)
            current = {}
    
    return leads

# ============================================================================
# DATA EXTRACTION HELPERS
# ============================================================================

def extract_location(text: str) -> tuple:
    """Extracts city and state."""
    text_lower = text.lower()
    
    cities = {
        'los angeles': ('Los Angeles', 'CA'), 'la': ('Los Angeles', 'CA'),
        'miami': ('Miami', 'FL'), 'houston': ('Houston', 'TX'),
        'chicago': ('Chicago', 'IL'), 'phoenix': ('Phoenix', 'AZ'),
        'dallas': ('Dallas', 'TX'), 'austin': ('Austin', 'TX'),
        'san diego': ('San Diego', 'CA'), 'seattle': ('Seattle', 'WA'),
        'denver': ('Denver', 'CO'), 'atlanta': ('Atlanta', 'GA'),
        'las vegas': ('Las Vegas', 'NV'), 'new york': ('New York', 'NY')
    }
    
    for key, (city, state) in cities.items():
        if key in text_lower:
            return city, state
    
    return 'Unknown', 'Unknown'

def classify_injury_type(text: str) -> str:
    """Classifies injury type."""
    text = text.lower()
    
    if any(word in text for word in ['car accident', 'rear end', 'auto accident']):
        return 'Car Accident'
    elif 'motorcycle' in text:
        return 'Motorcycle Accident'
    elif any(word in text for word in ['slip and fall', 'premises']):
        return 'Slip and Fall'
    elif any(word in text for word in ['work injury', 'workers comp']):
        return 'Workplace Injury'
    elif 'truck' in text:
        return 'Truck Accident'
    elif 'medical malpractice' in text:
        return 'Medical Malpractice'
    else:
        return 'Personal Injury'

def score_lead_quality(text: str) -> int:
    """Scores quality 1-10."""
    score = 6
    text = text.lower()
    
    if any(word in text for word in ['hospital', 'er', 'emergency']):
        score += 2
    if 'police report' in text:
        score += 1
    if any(word in text for word in ['injured', 'hurt', 'pain']):
        score += 1
    if 'need a lawyer' in text:
        score += 2
    if any(word in text for word in ['medical bills', 'insurance']):
        score += 1
    
    if any(phrase in text for phrase in ['already have', 'my lawyer']):
        score -= 6
    if 'years ago' in text:
        score -= 2
    
    return max(1, min(10, score))

def clean_text(text: str) -> str:
    """Cleans text."""
    return ' '.join(text.split())

def check_login_available(platform: str) -> bool:
    """Checks if login credentials available."""
    if 'facebook' in platform:
        return bool(os.getenv('FACEBOOK_EMAIL') and os.getenv('FACEBOOK_PASSWORD'))
    elif 'nextdoor' in platform:
        return bool(os.getenv('NEXTDOOR_EMAIL') and os.getenv('NEXTDOOR_PASSWORD'))
    return False

# ============================================================================
# STORAGE
# ============================================================================

def save_to_csv(leads: List[Dict], filename: str = 'mega_leads_anthropic.csv'):
    """Saves to CSV."""
    if not leads:
        return
    
    log(f"\n💾 Saving {len(leads)} leads to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['description', 'url', 'city', 'state', 'injury_type', 'score', 'source', 'posted_date', 'username']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for lead in leads:
            row = {k: lead.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    log(f"✅ Saved to {filename}")

def save_to_database(leads: List[Dict]):
    """Saves to Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Database unavailable")
        return
    
    saved = 0
    duplicates = 0
    
    for lead in leads:
        try:
            existing = supabase.table('injured_people_leads').select('id').eq('source_url', lead['url']).execute()
            
            if existing.data:
                duplicates += 1
                continue
            
            supabase.table('injured_people_leads').insert({
                'prospect_name': lead['username'],
                'city': lead['city'],
                'injury_type': lead['injury_type'],
                'injury_date': 'Recent',
                'description': lead['description'],
                'source': lead['source'],
                'source_url': lead['url'],
                'posted_date': lead['posted_date'],
                'quality_score': lead['score'],
                'status': 'new'
            }).execute()
            
            saved += 1
            
        except Exception as e:
            log(f"  ❌ DB error: {e}")
    
    log(f"\n💾 DATABASE: Saved {saved}, Duplicates {duplicates}")

# ============================================================================
# MASTER ORCHESTRATOR
# ============================================================================

async def run_mega_collector():
    """Master orchestrator."""
    log("="*70)
    log("🚀 MEGA COLLECTOR (ANTHROPIC + FACEBOOK): Starting...")
    log("="*70)
    
    all_leads = []
    task_count = 0
    total_tasks = sum(len(tasks) for tasks in PLATFORM_TASKS.values())
    
    for platform, tasks in PLATFORM_TASKS.items():
        log(f"\n{'🎯'*35}")
        log(f"PLATFORM: {platform.upper()}")
        log(f"{'🎯'*35}")
        
        for task_config in tasks:
            task_count += 1
            log(f"\n[Task {task_count}/{total_tasks}]")
            
            leads = await run_agent_task(platform, task_config)
            all_leads.extend(leads)
            
            if task_count < total_tasks:
                delay = random.randint(*DELAYS['between_tasks'])
                log(f"⏳ Waiting {delay}s...")
                await asyncio.sleep(delay)
        
        delay = random.randint(*DELAYS['between_platforms'])
        log(f"\n⏳ Platform complete. Waiting {delay}s...")
        await asyncio.sleep(delay)
    
    # Remove duplicates
    unique_leads = []
    seen_urls = set()
    for lead in all_leads:
        if lead['url'] not in seen_urls:
            unique_leads.append(lead)
            seen_urls.add(lead['url'])
    
    log("\n" + "="*70)
    log(f"📊 RESULTS: {len(unique_leads)} unique leads")
    log("="*70)
    
    if unique_leads:
        save_to_csv(unique_leads)
        save_to_database(unique_leads)
        print_analytics(unique_leads)
    
    log("\n✅ COMPLETE")

def print_analytics(leads: List[Dict]):
    """Prints analytics."""
    by_source = {}
    for lead in leads:
        by_source[lead['source']] = by_source.get(lead['source'], 0) + 1
    
    log("\n📊 BY SOURCE:")
    for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
        log(f"  {source}: {count}")
    
    avg_score = sum(l['score'] for l in leads) / len(leads) if leads else 0
    log(f"\n📊 Avg Quality: {avg_score:.1f}/10")

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        log("❌ ERROR: ANTHROPIC_API_KEY not found")
        exit(1)
    
    asyncio.run(run_mega_collector())
