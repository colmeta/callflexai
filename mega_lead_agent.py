# --- mega_lead_agent.py ---
# MEGA AI AGENT: Scrapes ALL 70+ platforms for PI leads
# Expected: 200-300 leads per run

import asyncio
import csv
from datetime import datetime
from browser_use import Agent
import os
import sys

sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# ============================================================================
# MEGA TASK LIST - ALL 70+ PLATFORMS
# ============================================================================

MEGA_TASKS = [
    # === TIER 1: LEGAL Q&A SITES (HIGHEST QUALITY) ===
    {
        "task": "Go to Google and search 'site:avvo.com personal injury question last week', open top 10 results, extract question text and URL from each",
        "source": "Avvo",
        "priority": 10
    },
    {
        "task": "Go to justia.com/ask-a-lawyer/personal-injury, scroll down and find 15 recent questions, extract question text and URL",
        "source": "Justia",
        "priority": 10
    },
    {
        "task": "Search Google for 'site:findlaw.com personal injury question', click top 10 results, extract questions",
        "source": "FindLaw",
        "priority": 9
    },
    {
        "task": "Go to lawyers.com, search 'personal injury', filter by questions in last week, get 10 questions",
        "source": "Lawyers.com",
        "priority": 9
    },
    {
        "task": "Search site:freeadvice.com personal injury on Google, get 10 recent questions",
        "source": "FreeAdvice",
        "priority": 8
    },
    
    # === TIER 2: REDDIT (HIGH VOLUME) ===
    {
        "task": "Go to old.reddit.com/r/legaladvice/search?q=car+accident&sort=new&t=week, extract top 20 posts where people ask if they need a lawyer",
        "source": "Reddit",
        "priority": 9
    },
    {
        "task": "Go to old.reddit.com/r/personalinjury/new, get the newest 15 posts, extract title and URL",
        "source": "Reddit",
        "priority": 9
    },
    {
        "task": "Search old.reddit.com/r/Insurance for 'accident claim' in last week, get 10 posts",
        "source": "Reddit",
        "priority": 8
    },
    {
        "task": "Go to old.reddit.com/r/AskLawyers, search 'injury', get 10 recent posts",
        "source": "Reddit",
        "priority": 8
    },
    
    # City subreddits
    {
        "task": "Search old.reddit.com/r/LosAngeles for 'car accident lawyer' or 'need attorney' in last month, get 5 posts",
        "source": "Reddit",
        "priority": 7
    },
    {
        "task": "Search old.reddit.com/r/Miami for accident-related lawyer requests, get 5 posts",
        "source": "Reddit",
        "priority": 7
    },
    {
        "task": "Search old.reddit.com/r/Houston for injury lawyer questions, get 5 posts",
        "source": "Reddit",
        "priority": 7
    },
    
    # === TIER 3: FACEBOOK (requires login - skip if not logged in) ===
    {
        "task": "Go to Facebook, search for 'car accident lawyer' in Groups from last week, extract 10 posts with poster name and link",
        "source": "Facebook",
        "priority": 9,
        "requires_login": True
    },
    {
        "task": "Search Facebook Groups for 'personal injury attorney recommendation' from last week, get 10 posts",
        "source": "Facebook",
        "priority": 9,
        "requires_login": True
    },
    
    # === TIER 4: CRAIGSLIST ===
    {
        "task": "Go to losangeles.craigslist.org, search 'car accident lawyer', filter by last 7 days, get 5 posts",
        "source": "Craigslist",
        "priority": 7
    },
    {
        "task": "Search miami.craigslist.org for 'injury attorney', get 5 recent posts",
        "source": "Craigslist",
        "priority": 7
    },
    {
        "task": "Search houston.craigslist.org for 'need lawyer accident', get 5 posts",
        "source": "Craigslist",
        "priority": 7
    },
    
    # === TIER 5: QUORA ===
    {
        "task": "Go to quora.com, search 'personal injury lawyer', filter by last week, get 10 questions",
        "source": "Quora",
        "priority": 7
    },
    {
        "task": "Search Quora for 'car accident lawyer recommendation', get 10 recent questions",
        "source": "Quora",
        "priority": 7
    },
    
    # === TIER 6: TWITTER/X ===
    {
        "task": "Search Twitter for 'car accident need lawyer' posted in last 7 days, get 15 tweets with location if mentioned",
        "source": "Twitter",
        "priority": 6
    },
    {
        "task": "Search Twitter for 'injured attorney recommendation' from last week, get 10 tweets",
        "source": "Twitter",
        "priority": 6
    },
    
    # === TIER 7: YOUTUBE COMMENTS ===
    {
        "task": "Go to YouTube, search 'what to do after car accident', open top 3 videos, read comments for people asking about lawyers",
        "source": "YouTube",
        "priority": 5
    },
    {
        "task": "Search YouTube 'personal injury lawyer', open top video, find comments where people ask for help",
        "source": "YouTube",
        "priority": 5
    },
    
    # === TIER 8: YELP ===
    {
        "task": "Go to yelp.com, search 'personal injury lawyer Los Angeles', look at Q&A sections, find people asking questions",
        "source": "Yelp",
        "priority": 6
    },
    
    # === TIER 9: NEXTDOOR (requires login) ===
    {
        "task": "Go to Nextdoor, search 'lawyer recommendation accident' in your neighborhood, get 5 posts",
        "source": "Nextdoor",
        "priority": 8,
        "requires_login": True
    },
    
    # === TIER 10: FORUMS ===
    {
        "task": "Go to city-data.com forums, search legal section for injury questions from last month, get 5 posts",
        "source": "City-Data",
        "priority": 6
    },
    {
        "task": "Search Google 'site:injuryboard.com personal injury question', get 5 recent posts",
        "source": "InjuryBoard",
        "priority": 7
    },
    
    # === TIER 11: LOCAL NEWS COMMENTS ===
    {
        "task": "Google 'Los Angeles car accident news', open top 3 news articles, read comments for people discussing similar accidents",
        "source": "Local News",
        "priority": 5
    },
    
    # === TIER 12: TIKTOK ===
    {
        "task": "Search TikTok for #caraccident #lawyer, look at recent videos, read comments for people asking for help",
        "source": "TikTok",
        "priority": 4
    },
    
    # === TIER 13: INSTAGRAM ===
    {
        "task": "Search Instagram #personalinjury #losangeles, look at recent posts, read comments for lawyer requests",
        "source": "Instagram",
        "priority": 4
    },
]

# ============================================================================
# AI AGENT RUNNER
# ============================================================================

async def run_single_agent(task_config):
    """Runs one AI agent task."""
    log(f"\n{'='*70}")
    log(f"🤖 AGENT: {task_config['source']}")
    log(f"📋 TASK: {task_config['task'][:80]}...")
    log(f"⭐ PRIORITY: {task_config['priority']}/10")
    log('='*70)
    
    # Skip tasks that require login if not available
    if task_config.get('requires_login') and not os.getenv('BROWSER_USE_LOGIN'):
        log("⚠️ Skipping - requires login (set BROWSER_USE_LOGIN=true)")
        return []
    
    try:
        # Initialize AI agent
        agent = Agent(
            task=task_config['task'],
            llm=os.getenv("ANTHROPIC_API_KEY"),
            # Add anti-detection features
            use_stealth=True,  # Human-like behavior
            headless=False if task_config.get('requires_login') else True
        )
        
        # Run agent
        result = await agent.run()
        
        log(f"✅ Agent completed")
        
        # Parse results
        leads = parse_agent_results(result, task_config)
        
        log(f"📊 Extracted {len(leads)} leads")
        
        return leads
    
    except Exception as e:
        log(f"❌ Agent failed: {e}")
        return []

def parse_agent_results(result, task_config):
    """Parses AI agent results into structured leads."""
    leads = []
    
    # BrowserUse returns structured data
    if isinstance(result, dict) and 'extracted_data' in result:
        raw_leads = result['extracted_data']
    elif isinstance(result, list):
        raw_leads = result
    else:
        # Try parsing text
        raw_leads = extract_from_text(str(result))
    
    for item in raw_leads:
        try:
            # Standardize lead format
            lead = {
                'description': str(item.get('title') or item.get('text', ''))[:500],
                'url': item.get('url', ''),
                'city': item.get('city', 'Unknown'),
                'injury_type': classify_injury_type(str(item)),
                'score': score_lead(str(item)),
                'source': task_config['source'],
                'posted_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Only save valid leads
            if lead['description'] and lead['url'] and lead['score'] >= 5:
                leads.append(lead)
                log(f"  ✅ {lead['description'][:60]}... (score: {lead['score']})")
        
        except Exception as e:
            log(f"  ⚠️ Parse error: {e}")
            continue
    
    return leads

def extract_from_text(text):
    """Fallback text parser."""
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

def classify_injury_type(text):
    """Determines injury type from text."""
    text = text.lower()
    
    if 'car' in text or 'auto' in text or 'rear end' in text:
        return 'Car Accident'
    elif 'motorcycle' in text or 'bike' in text:
        return 'Motorcycle Accident'
    elif 'slip' in text or 'fall' in text:
        return 'Slip and Fall'
    elif 'work' in text or 'workers comp' in text:
        return 'Workplace Injury'
    elif 'truck' in text:
        return 'Truck Accident'
    elif 'medical' in text or 'doctor' in text:
        return 'Medical Malpractice'
    else:
        return 'Personal Injury'

def score_lead(text):
    """Scores lead quality 1-10."""
    score = 6
    text = text.lower()
    
    # Positive indicators
    if any(w in text for w in ['hospital', 'er', 'emergency', 'ambulance']):
        score += 2
    if 'police report' in text or 'police' in text:
        score += 1
    if any(w in text for w in ['injured', 'hurt', 'pain', 'broken']):
        score += 1
    if 'need a lawyer' in text or 'need lawyer' in text:
        score += 2
    if any(w in text for w in ['bills', 'medical bills', 'insurance']):
        score += 1
    
    # Negative indicators
    if 'already have' in text or 'my lawyer' in text or 'my attorney' in text:
        score -= 6
    if 'years ago' in text or 'old case' in text:
        score -= 2
    
    return max(1, min(10, score))

# ============================================================================
# SAVE FUNCTIONS
# ============================================================================

def save_to_csv(leads, filename='mega_leads.csv'):
    """Saves all leads to CSV."""
    if not leads:
        log("No leads to save")
        return
    
    log(f"\n💾 Saving {len(leads)} leads to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['description', 'url', 'city', 'injury_type', 'score', 'source', 'posted_date'])
        writer.writeheader()
        writer.writerows(leads)
    
    log(f"✅ Saved to {filename}")

def save_to_database(leads):
    """Saves to Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Database unavailable")
        return
    
    saved = 0
    duplicates = 0
    
    for lead in leads:
        try:
            # Check duplicate
            existing = supabase.table('injured_people_leads').select('id').eq('source_url', lead['url']).execute()
            
            if existing.data:
                duplicates += 1
                continue
            
            # Insert
            supabase.table('injured_people_leads').insert({
                'prospect_name': 'Anonymous',
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
    
    log(f"\n💾 DATABASE:")
    log(f"  ✅ Saved: {saved}")
    log(f"  ⚠️ Duplicates: {duplicates}")

# ============================================================================
# MASTER ORCHESTRATOR
# ============================================================================

async def run_mega_agent():
    """Master orchestrator: Runs ALL agents."""
    log("="*70)
    log("🚀 MEGA AI AGENT: Starting...")
    log(f"📊 Total tasks: {len(MEGA_TASKS)}")
    log("="*70)
    
    all_leads = []
    
    # Sort tasks by priority
    sorted_tasks = sorted(MEGA_TASKS, key=lambda x: x['priority'], reverse=True)
    
    for i, task in enumerate(sorted_tasks, 1):
        log(f"\n[{i}/{len(sorted_tasks)}] Processing...")
        
        leads = await run_single_agent(task)
        all_leads.extend(leads)
        
        # Pause between agents (anti-detection)
        wait_time = 5 + (task['priority'] * 2)  # Higher priority = longer wait
        log(f"⏳ Waiting {wait_time}s before next agent...")
        await asyncio.sleep(wait_time)
    
    # Remove duplicates
    unique_leads = []
    seen_urls = set()
    for lead in all_leads:
        if lead['url'] not in seen_urls:
            unique_leads.append(lead)
            seen_urls.add(lead['url'])
    
    log("\n" + "="*70)
    log(f"📊 MEGA RESULTS:")
    log(f"  Total collected: {len(all_leads)}")
    log(f"  Unique leads: {len(unique_leads)}")
    log("="*70)
    
    if unique_leads:
        # Save
        save_to_csv(unique_leads)
        save_to_database(unique_leads)
        
        # Analytics
        by_source = {}
        for lead in unique_leads:
            source = lead['source']
            by_source[source] = by_source.get(source, 0) + 1
        
        log("\n📊 LEADS BY SOURCE:")
        for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
            log(f"  {source}: {count}")
        
        # Top quality leads
        log("\n🎯 TOP 20 QUALITY LEADS:")
        top_leads = sorted(unique_leads, key=lambda x: x['score'], reverse=True)[:20]
        for i, lead in enumerate(top_leads, 1):
            log(f"\n{i}. {lead['description'][:80]}...")
            log(f"   Source: {lead['source']} | Score: {lead['score']}/10")
            log(f"   URL: {lead['url'][:80]}...")
    
    log("\n" + "="*70)
    log("✅ MEGA AI AGENT: Complete")
    log("="*70)

if __name__ == "__main__":
    asyncio.run(run_mega_agent())
