# --- facebook_finder.py ---
# This finds potential customers asking for services in Facebook groups.
# NOTE: You'll run this manually since Facebook doesn't have a free API.

"""
MANUAL PROCESS (Until you can afford automation tools):

1. Join local Facebook groups for your client's city:
   - "Austin Texas Community"
   - "Austin Moms"
   - "Austin Recommendations"

2. Search within each group for keywords:
   - "dentist"
   - "need a plumber"
   - "looking for HVAC"

3. When you find someone asking, copy their info to a spreadsheet:
   - Name
   - Date of post
   - What they need
   - Link to post

4. Upload that CSV to Supabase using this script.
"""

import csv
from database import get_supabase_client

def log(message):
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def upload_facebook_leads_from_csv(csv_file_path, client_id):
    """
    Uploads leads you manually collected from Facebook groups.
    
    CSV format:
    name,post_date,service_needed,facebook_link,notes
    Sarah Johnson,2025-01-14,dentist,https://facebook.com/...,Needs emergency appt
    """
    log(f"Facebook Finder: Reading CSV file: {csv_file_path}")
    
    supabase = get_supabase_client()
    if not supabase:
        log("ERROR: Cannot connect to database.")
        return
    
    leads_uploaded = 0
    
    with open(csv_file_path, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            lead_data = {
                'client_id': client_id,
                'prospect_name': row['name'],
                'source': 'facebook',
                'service_needed': row['service_needed'],
                'source_url': row['facebook_link'],
                'notes': row.get('notes', ''),
                'status': 'new',
                'quality_score': 7  # Manual finds are usually high quality
            }
            
            try:
                supabase.table('prospect_leads').insert(lead_data).execute()
                leads_uploaded += 1
                log(f"✅ Uploaded: {row['name']}")
            except Exception as e:
                log(f"❌ Error uploading {row['name']}: {e}")
    
    log(f"Facebook Finder: Uploaded {leads_uploaded} leads to database.")

# Example usage:
# upload_facebook_leads_from_csv('facebook_leads.csv', client_id='abc-123')
