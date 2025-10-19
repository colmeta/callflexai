# --- manual_lead_importer.py ---
# Import leads from a simple text file

import csv
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def import_from_csv(csv_file):
    """Imports leads from CSV format:
    
    description,url,city,injury_type
    "I was rear-ended...",https://...,Miami,Car Accident
    """
    log(f"📂 Importing from {csv_file}...")
    
    leads = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)
    
    log(f"✅ Read {len(leads)} leads from CSV")
    return leads

def save_to_database(leads):
    """Saves to Supabase."""
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
                'city': lead.get('city', 'Unknown'),
                'injury_type': lead.get('injury_type', 'Personal Injury'),
                'injury_date': 'Recent',
                'description': lead['description'][:500],
                'source': lead.get('source', 'Manual'),
                'source_url': lead['url'],
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'quality_score': int(lead.get('score', 7)),
                'status': 'new'
            }).execute()
            
            saved += 1
            log(f"  ✅ Saved: {lead['description'][:60]}...")
        
        except Exception as e:
            log(f"  ❌ Error: {e}")
    
    log(f"\n📊 RESULTS:")
    log(f"  Saved: {saved}")
    log(f"  Duplicates skipped: {duplicates}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        log("Usage: python manual_lead_importer.py leads.csv")
        sys.exit(1)
    
    leads = import_from_csv(sys.argv[1])
    save_to_database(leads)
