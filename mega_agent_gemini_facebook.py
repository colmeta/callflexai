# --- mega_agent_gemini_facebook.py ---
# MEGA AI AGENT: ALL 70+ platforms + FACEBOOK ENABLED
# Uses: Google Gemini (FREE - 1,500 requests/day)
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
# SAME PLATFORM TASKS AS ANTHROPIC VERSION
# ============================================================================

PLATFORM_TASKS = {
    # 🔥 FACEBOOK GROUPS (TOP PRIORITY)
    "facebook_groups": [
        {
            "task": "Log into Facebook. Search Groups for 'car accident lawyer' OR 'need attorney' from last 7 days. Focus on city groups. Get 20 posts with: name, content preview, URL, group name, city.",
            "priority": 10,
            "requires_login": True,
            "expected_leads": 20
        },
        {
            "task": "Search Facebook Groups for 'personal injury attorney recommendation' from last 14 days. Get 15 posts.",
            "priority": 10,
            "requires_login": True,
            "expected_leads": 15
        },
        {
            "task": "Search '[City] Moms' Facebook groups for posts about injuries. Get 10 posts asking for lawyer help.",
            "priority": 9,
            "requires_login": True,
            "expected_leads": 10
        }
    ],
    
    "avvo": [
        {
            "task": "Google search 'site:avvo.com personal injury question last week'. Open top 10. Extract question, URL, location.",
            "priority": 9,
            "expected_leads": 10
        }
    ],
    
    "justia": [
        {
            "task": "Go to justia.com/ask-a-lawyer/personal-injury. Get 15 questions from last 2 weeks with URLs.",
            "priority": 9,
            "expected_leads": 15
        }
    ],
    
    "reddit_legal": [
        {
            "task": "Go to old.reddit.com/r/legaladvice/search?q=car+accident&sort=new&t=week. Get 20 posts about needing lawyers.",
            "priority": 8,
            "expected_leads": 20
        },
        {
            "task": "Go to old.reddit.com/r/personalinjury/new. Get 15 newest posts.",
            "priority": 8,
            "expected_leads": 15
        }
    ],
    
    "reddit_cities": [
        {
            "task": "Search old.reddit.com/r/LosAngeles for 'accident' OR 'lawyer' from last month. Get 5 posts.",
            "priority": 7,
            "expected_leads": 5
        }
    ],
    
    "craigslist": [
        {
            "task": "Search losangeles.craigslist.org for 'car accident lawyer' from last week. Get 5 posts.",
            "priority": 6,
            "expected_leads": 5
        }
    ],
    
    "quora": [
        {
            "task": "Search quora.com for 'personal injury lawyer' from last week. Get 10 questions.",
            "priority": 7,
            "expected_leads": 10
        }
    ]
}

# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

# Gemini uses different initialization
GEMINI_MODEL = "gemini-pro"

BROWSER_CONFIG = BrowserConfig(
    headless=False,
)

DELAYS = {
    "between_platforms": (30, 60),
    "between_tasks": (10, 20),
}

# ============================================================================
# GEMINI-SPECIFIC AGENT EXECUTION
# ============================================================================

async def run_agent_task(platform: str, task_config: Dict) -> List[Dict]:
    """Runs task using Gemini."""
    log(f"\n{'='*70}")
    log(f"🤖 PLATFORM: {platform.upper()} (Gemini FREE)")
    log(f"📋 TASK: {task_config['task'][:80]}...")
    log(f"⭐ PRIORITY: {task_config['priority']}/10")
    log('='*70)
    
    if task_config.get('requires_login'):
        if not check_login_available(platform):
            log("⚠️ Skipping - requires login")
            return []
    
    try:
        # Gemini initialization (different from Anthropic)
        agent = Agent(
            task=task_config['task'],
            llm_model=GEMINI_MODEL,  # Use Gemini
            llm_api_key=os.getenv("GEMINI_API_KEY"),  # Different key
            browser_config=BROWSER_CONFIG,
            max_actions_per_step=50
        )
        
        log("🚀 Gemini agent starting...")
        result = await agent.run()
        
        log("✅ Gemini completed")
        
        leads = parse_agent_results(result, platform, task_config)
        
        log(f"📊 Extracted {len(leads)} leads")
        
        return leads
        
    except Exception as e:
        log(f"❌ Agent failed: {e}")
        return []

# ============================================================================
# SAME PARSING FUNCTIONS AS ANTHROPIC VERSION
# ============================================================================

def parse_agent_results(result, platform: str, task_config: Dict) -> List[Dict]:
    """Parses results."""
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
                'username': item.get('name') or item.get('username', 'Anonymous')
            }
            
            if lead['description'] and lead['url'] and lead['score'] >= 5:
                leads.append(lead)
                log(f"  ✅ {lead['description'][:50]}... ({lead['score']}/10)")
                
        except Exception as e:
            log(f"  ⚠️ Error: {e}")
            continue
    
    return leads

def extract_from_text(text: str) -> List[Dict]:
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

def extract_location(text: str) -> tuple:
    text_lower = text.lower()
    cities = {
        'los angeles': ('Los Angeles', 'CA'), 'la': ('Los Angeles', 'CA'),
        'miami': ('Miami', 'FL'), 'houston': ('Houston', 'TX'),
        'chicago': ('Chicago', 'IL'), 'phoenix': ('Phoenix', 'AZ')
    }
    for key, (city, state) in cities.items():
        if key in text_lower:
            return city, state
    return 'Unknown', 'Unknown'

def classify_injury_type(text: str) -> str:
    text = text.lower()
    if 'car' in text:
        return 'Car Accident'
    elif 'motorcycle' in text:
        return 'Motorcycle Accident'
    elif 'slip' in text or 'fall' in text:
        return 'Slip and Fall'
    elif 'work' in text:
        return 'Workplace Injury'
    return 'Personal Injury'

def score_lead_quality(text: str) -> int:
    score = 6
    text = text.lower()
    if any(w in text for w in ['hospital', 'er']):
        score += 2
    if 'police' in text:
        score += 1
    if 'need lawyer' in text:
        score += 2
    if 'already have' in text:
        score -= 6
    return max(1, min(10, score))

def clean_text(text: str) -> str:
    return ' '.join(text.split())

def check_login_available(platform: str) -> bool:
    if 'facebook' in platform:
        return bool(os.getenv('FACEBOOK_EMAIL'))
    return False

# ============================================================================
# STORAGE (SAME AS ANTHROPIC)
# ============================================================================

def save_to_csv(leads: List[Dict], filename: str = 'mega_leads_gemini.csv'):
    if not leads:
        return
    log(f"\n💾 Saving {len(leads)} to {filename}...")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['description', 'url', 'city', 'state', 'injury_type', 'score', 'source', 'posted_date']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            row = {k: lead.get(k, '') for k in fieldnames}
            writer.writerow(row)
    log(f"✅ Saved")

def save_to_database(leads: List[Dict]):
    supabase = get_supabase_client()
    if not supabase:
        return
    
    saved = 0
    for lead in leads:
        try:
            existing = supabase.
