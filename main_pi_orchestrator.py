# --- main_pi_orchestrator.py ---
# Master controller for PI lawyer lead generation system

from datetime import datetime
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def get_injured_people_by_city():
    """
    Groups all new injured people leads by city.
    
    Returns:
        dict: {'Los Angeles': [lead1, lead2], 'Miami': [lead3, lead4]}
    """
    supabase = get_supabase_client()
    if not supabase:
        log("ERROR: Cannot connect to database.")
        return {}
    
    try:
        # Get all new injured people (not yet matched to a lawyer)
        response = supabase.table('injured_people_leads').select('*').eq('status', 'new').order('quality_score', desc=True).execute()
        
        leads = response.data
        
        if not leads:
            log("No new injured people found.")
            return {}
        
        # Group by city
        by_city = {}
        for lead in leads:
            city = lead.get('city', 'Unknown')
            if city not in by_city:
                by_city[city] = []
            by_city[city].append(lead)
        
        return by_city
    
    except Exception as e:
        log(f"ERROR: {e}")
        return {}

def get_pi_lawyers_in_city(city):
    """
    Finds PI lawyers you're targeting in a specific city.
    
    Returns:
        list: PI lawyer prospects from your database
    """
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    try:
        # Assuming you have a separate table for PI lawyer prospects
        response = supabase.table('pi_lawyer_clients').select('*').eq('city', city).eq('status', 'active').execute()
        
        return response.data
    
    except Exception as e:
        log(f"ERROR: {e}")
        return []

def generate_lead_summary(injured_people):
    """
    Creates a summary of injured people for the one-pager.
    
    Args:
        injured_people (list): List of injured people leads
    
    Returns:
        str: Formatted summary
    """
    summary = f"Found {len(injured_people)} injured people seeking legal representation:\n\n"
    
    for idx, person in enumerate(injured_people, 1):
        summary += f"{idx}. {person['description']}\n"
        summary += f"   Injury Type: {person['injury_type']}\n"
        summary += f"   Quality Score: {person['quality_score']}/10\n"
        summary += f"   Source: {person['source']}\n"
        summary += f"   Link: {person['source_url']}\n\n"
    
    return summary

def run_pi_orchestrator():
    """
    Main workflow:
    1. Get all injured people, grouped by city
    2. For each city with leads, notify you
    3. You can then manually send the one-pager to lawyers
    """
    log("="*60)
    log("PI LAWYER ORCHESTRATOR: Starting...")
    log("="*60)
    
    injured_by_city = get_injured_people_by_city()
    
    if not injured_by_city:
        log("No injured people to process today.")
        return
    
    log(f"\nFound injured people in {len(injured_by_city)} cities:")
    
    for city, people in injured_by_city.items():
        log(f"\n{'='*60}")
        log(f"CITY: {city}")
        log(f"{'='*60}")
        log(f"Injured people: {len(people)}")
        
        # Print summary
        summary = generate_lead_summary(people)
        log(summary)
        
        # Find lawyers in this city (if you have any)
        lawyers = get_pi_lawyers_in_city(city)
        
        if lawyers:
            log(f"\nYou have {len(lawyers)} PI lawyer client(s) in {city}:")
            for lawyer in lawyers:
                log(f"  - {lawyer.get('business_name')} ({lawyer.get('contact_email')})")
        else:
            log(f"\n⚠️ No PI lawyer clients in {city} yet.")
            log(f"💡 ACTION: Find PI lawyers in {city} and send them the one-pager!")
    
    log("\n" + "="*60)
    log
