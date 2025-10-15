# --- deduplication.py ---
# Prevents contacting the same person twice across all clients

from database import get_supabase_client
import hashlib

def log(message):
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def generate_prospect_fingerprint(name, source_url):
    """
    Creates a unique ID for a prospect based on their identifiable info.
    This prevents duplicate outreach.
    
    Args:
        name (str): Prospect's name or username
        source_url (str): Link to their Facebook/Reddit post
    
    Returns:
        str: Unique fingerprint hash
    """
    # Normalize data
    clean_name = name.lower().strip()
    clean_url = source_url.lower().strip()
    
    # Create unique hash
    data_string = f"{clean_name}|{clean_url}"
    fingerprint = hashlib.md5(data_string.encode()).hexdigest()
    
    return fingerprint

def check_if_prospect_exists(fingerprint):
    """
    Checks if we've already contacted this person for ANY client.
    
    Returns:
        bool: True if already contacted, False if new
    """
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        response = supabase.table('prospect_leads').select('id').eq('fingerprint', fingerprint).execute()
        
        if response.data:
            log(f"⚠️ DUPLICATE DETECTED: This prospect is already in our system")
            return True
        else:
            return False
    
    except Exception as e:
        log(f"Error checking duplicate: {e}")
        return False

def save_prospect_with_fingerprint(client_id, prospect_data):
    """
    Saves a new prospect ONLY if they haven't been contacted before.
    
    Args:
        client_id (str): Which client this lead is for
        prospect_data (dict): All prospect info
    
    Returns:
        bool: True if saved, False if duplicate
    """
    # Generate fingerprint
    fingerprint = generate_prospect_fingerprint(
        prospect_data['name'],
        prospect_data['source_url']
    )
    
    # Check for duplicate
    if check_if_prospect_exists(fingerprint):
        log(f"Skipping duplicate: {prospect_data['name']}")
        return False
    
    # Save to database with fingerprint
    supabase = get_supabase_client()
    lead_data = {
        'client_id': client_id,
        'prospect_name': prospect_data['name'],
        'prospect_email': prospect_data.get('email'),
        'prospect_phone': prospect_data.get('phone'),
        'source': prospect_data['source'],
        'source_url': prospect_data['source_url'],
        'service_needed': prospect_data['service_needed'],
        'notes': prospect_data.get('notes', ''),
        'quality_score': prospect_data.get('quality_score', 5),
        'status': 'new',
        'fingerprint': fingerprint  # This prevents duplicates
    }
    
    try:
        supabase.table('prospect_leads').insert(lead_data).execute()
        log(f"✅ Saved new prospect: {prospect_data['name']}")
        return True
    except Exception as e:
        log(f"❌ Error saving prospect: {e}")
        return False

# Example usage:
# prospect = {
#     'name': 'Sarah Johnson',
#     'source': 'facebook',
#     'source_url': 'https://facebook.com/groups/austin/posts/12345',
#     'service_needed': 'dentist',
#     'notes': 'Needs emergency root canal'
# }
# save_prospect_with_fingerprint(client_id='abc-123', prospect_data=prospect)
