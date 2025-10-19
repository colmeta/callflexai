# --- browseruse_lead_collector.py ---
# AI Agent that browses Avvo/Justia/Reddit like a human and collects leads
# Uses BrowserUse + Claude to navigate websites intelligently

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

# AI Agent Tasks (what you want it to do)
LEAD_COLLECTION_TASKS = [
    # Reddit Tasks
    {
        "task": "Go to old.reddit.com/r/legaladvice, search for 'car accident' in the last week, find 10 posts where people are asking if they need a lawyer, extract the post title and URL",
        "source": "Reddit",
        "injury_type": "Car Accident"
    },
    {
        "task": "Go to old.reddit.com/r/personalinjury, look at the newest 10 posts, extract posts where someone is asking about finding a lawyer, get title and URL",
        "source": "Reddit", 
        "injury_type": "Personal Injury"
    },
    
    # Avvo Tasks (works around blocks)
    {
        "task": "Go to Google and search 'site:avvo.com personal injury question', click on the top 5 Avvo question pages, extract the question text and URL from each page",
        "source": "Avvo",
        "injury_type": "Personal Injury"
    },
    
    # Justia Tasks
    {
        "task": "Go to justia.com/ask-a-lawyer/personal-injury, find 10 recent questions, extract question text and URL",
        "source": "Justia",
        "injury_type": "Personal Injury"
    },
    
    # Facebook Groups (if you're logged in)
    {
        "task": "Go to Facebook, search for posts containing 'car accident lawyer' in the last week in public groups, extract 5 posts with poster name and link",
        "source": "Facebook",
        "injury_type": "Car Accident"
    }
]

async def run_lead_collection_agent(task_config):
    """Runs a single AI agent task to collect leads."""
    log(f"🤖 Starting Agent: {task_config['source']}")
    log(f"📋 Task: {task_config['task'][:80]}...")
    
    # Initialize BrowserUse Agent with Claude
    agent = Agent(
        task=task_config['task'],
        llm=os.getenv("ANTHROPIC_API_KEY")  # Uses Claude Sonnet
    )
    
    try:
        # Run the agent
        result = await agent.run()
        
        log(f"✅ Agent completed task")
        log(f"📊 Result preview: {str(result)[:200]}...")
        
        # Parse agent's findings
        leads = parse_agent_result(result, task_config)
        
        return leads
    
    except Exception as e:
        log(f"❌ Agent failed: {e}")
        return []

def parse_agent_result(result, task_config):
    """Parses the AI agent's findings into structured lead data."""
    # The agent returns structured data or text
    # We need to extract: description, URL, city, injury_type
    
    leads = []
    
    # BrowserUse returns results in various formats
    # Try to extract structured data
    if isinstance(result, dict) and 'extracted_data' in result:
        raw_leads = result['extracted_data']
    elif isinstance(result, list):
        raw_leads = result
    else:
        # Agent returned text, try to parse it
        raw_leads = extract_from_text(str(result))
    
    for item in raw_leads:
        try:
            lead = {
                'description': item.get('title') or item.get('text', '')[:500],
                'url': item.get('url', ''),
                'city': item.get('city', 'Unknown'),
                'injury_type': task_config.get('injury_type', 'Personal Injury'),
                'score': calculate_lead_score(item),
                'source': task_config.get('source', 'Unknown')
            }
            
            # Only save if we have description and URL
            if lead['description'] and lead['url']:
                leads.append(lead)
        
        except Exception as e:
            log(f"  ⚠️ Error parsing item: {e}")
            continue
    
    log(f"  ✅ Extracted {len(leads)} leads from agent result")
    return leads

def extract_from_text(text):
    """Fallback: Extract leads from agent's text response."""
    # Simple parser for when agent returns unstructured text
    leads = []
    
    # Split by common delimiters
    lines = text.split('\n')
    
    current_lead = {}
    for line in lines:
        line = line.strip()
        
        # Look for URLs
        if 'http' in line:
            if 'url' not in current_lead:
                current_lead['url'] = line
        
        # Look for titles/descriptions
        elif len(line) > 20 and not line.startswith('Task:'):
            if 'text' not in current_lead:
                current_lead['text'] = line
        
        # If we have both, save it
        if 'url' in current_lead and 'text' in current_lead:
            leads.append(current_lead)
            current_lead = {}
    
    return leads

def calculate_lead_score(item):
    """Scores lead quality 1-10."""
    score = 6
    
    text = str(item).lower()
    
    # Positive indicators
    if any(w in text for w in ['hospital', 'er', 'doctor']):
        score += 2
    if 'need a lawyer' in text or 'should i get a lawyer' in text:
        score += 2
    if any(w in text for w in ['injured', 'hurt', 'accident']):
        score += 1
    
    # Negative indicators
    if 'already have' in text or 'my attorney' in text:
        score -= 5
    
    return max(1, min(10, score))

def save_leads_to_csv(all_leads, filename='agent_collected_leads.csv'):
    """Saves collected leads to CSV."""
    if not all_leads:
        log("No leads to save")
        return
    
    log(f"💾 Saving {len(all_leads)} leads to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['description', 'url', 'city', 'injury_type', 'score', 'source'])
        writer.writeheader()
        writer.writerows(all_leads)
    
    log(f"✅ Saved to {filename}")

def save_leads_to_database(leads):
    """Saves leads to Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Database connection failed")
        return
    
    saved = 0
    duplicates = 0
    
    for lead in leads:
        try:
            # Check duplicate
            existing = supabase.table('injured_people_leads')\
                .select('id')\
                .eq('source_url', lead['url'])\
                .execute()
            
            if existing.data:
                duplicates += 1
                continue
            
            # Insert
            supabase.table('injured_people_leads').insert({
                'prospect_name': 'Anonymous',
                'city': lead['city'],
                'injury_type': lead['injury_type'],
                'injury_date': 'Recent',
                'description': lead['description'][:500],
                'source': lead['source'],
                'source_url': lead['url'],
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'quality_score': lead['score'],
                'status': 'new'
            }).execute()
            
            saved += 1
            log(f"  ✅ Saved: {lead['description'][:60]}...")
        
        except Exception as e:
            log(f"  ❌ Error: {e}")
    
    log(f"\n📊 DATABASE RESULTS:")
    log(f"  Saved: {saved}")
    log(f"  Duplicates: {duplicates}")

async def run_all_agents():
    """Master orchestrator: Runs all lead collection agents."""
    log("="*70)
    log("🤖 AI AGENT LEAD COLLECTOR: Starting...")
    log("="*70)
    
    all_leads = []
    
    # Run each agent task
    for task_config in LEAD_COLLECTION_TASKS:
        leads = await run_lead_collection_agent(task_config)
        all_leads.extend(leads)
        
        # Pause between agents (be respectful)
        log("⏳ Waiting 10 seconds before next agent...")
        await asyncio.sleep(10)
    
    log(f"\n📊 TOTAL LEADS COLLECTED: {len(all_leads)}")
    
    if all_leads:
        # Save to CSV
        save_leads_to_csv(all_leads)
        
        # Save to database
        save_leads_to_database(all_leads)
        
        # Print top leads
        log("\n🎯 TOP 10 QUALITY LEADS:")
        top = sorted(all_leads, key=lambda x: x['score'], reverse=True)[:10]
        for i, lead in enumerate(top, 1):
            log(f"\n{i}. {lead['description'][:80]}...")
            log(f"   Source: {lead['source']}")
            log(f"   Score: {lead['score']}/10")
            log(f"   URL: {lead['url']}")
    
    log("\n" + "="*70)
    log("✅ AI AGENT: Complete")
    log("="*70)

if __name__ == "__main__":
    # Run the async agent orchestrator
    asyncio.run(run_all_agents())
