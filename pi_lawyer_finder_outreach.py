# --- pi_lawyer_finder_outreach.py ---
# Finds PI lawyers (your customers) and generates outreach messages
# Run this BEFORE collecting injured people leads!

import csv
import os
import requests
from datetime import datetime
from typing import List, Dict

import sys
sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# ============================================================================
# TARGET CITIES (High accident rates = more PI cases)
# ============================================================================

TARGET_CITIES = [
    {'city': 'Los Angeles', 'state': 'CA', 'population': '4M'},
    {'city': 'Miami', 'state': 'FL', 'population': '450K'},
    {'city': 'Houston', 'state': 'TX', 'population': '2.3M'},
    {'city': 'Phoenix', 'state': 'AZ', 'population': '1.7M'},
    {'city': 'Dallas', 'state': 'TX', 'population': '1.3M'},
    {'city': 'Chicago', 'state': 'IL', 'population': '2.7M'},
    {'city': 'Atlanta', 'state': 'GA', 'population': '500K'},
    {'city': 'Las Vegas', 'state': 'NV', 'population': '650K'},
    {'city': 'San Diego', 'state': 'CA', 'population': '1.4M'},
    {'city': 'Austin', 'state': 'TX', 'population': '1M'},
]

# ============================================================================
# GOOGLE MAPS SCRAPER (Finds PI Lawyers)
# ============================================================================

def find_pi_lawyers_google_maps(city: str, state: str, limit: int = 50) -> List[Dict]:
    """
    Finds PI lawyers using Google Maps/SerpAPI.
    
    Returns: List of lawyer firms with contact info
    """
    log(f"\n{'='*70}")
    log(f"🔍 Finding PI Lawyers in {city}, {state}")
    log(f"{'='*70}")
    
    SERPAPI_KEY = os.getenv('SERPAPI_API_KEY')
    
    if not SERPAPI_KEY:
        log("⚠️ SERPAPI_API_KEY not found - using manual fallback")
        return manual_google_maps_instructions(city, state)
    
    try:
        from serpapi import GoogleSearch
        
        search_params = {
            "engine": "google_maps",
            "q": f"personal injury lawyer {city} {state}",
            "type": "search",
            "api_key": SERPAPI_KEY
        }
        
        log("🚀 Searching Google Maps...")
        search = GoogleSearch(search_params)
        results = search.get_dict()
        
        local_results = results.get("local_results", [])
        
        if not local_results:
            log(f"⚠️ No results for {city}")
            return []
        
        lawyers = []
        
        for result in local_results[:limit]:
            lawyer = {
                'business_name': result.get('title', 'Unknown'),
                'city': city,
                'state': state,
                'address': result.get('address', ''),
                'phone': result.get('phone', ''),
                'website': result.get('website', ''),
                'rating': result.get('rating', 0),
                'review_count': result.get('reviews', 0),
                'google_maps_url': result.get('link', ''),
                
                # Calculate desperation score (how badly they need leads)
                'desperation_score': calculate_desperation_score(result),
                
                # Guess contact email
                'contact_email': guess_email(result.get('website', ''), result.get('title', '')),
                
                'status': 'prospect',
                'found_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            lawyers.append(lawyer)
            log(f"  ✅ {lawyer['business_name']} | Desperation: {lawyer['desperation_score']}/10")
        
        log(f"\n✅ Found {len(lawyers)} PI lawyers in {city}")
        return lawyers
        
    except ImportError:
        log("⚠️ SerpAPI not installed. Install: pip install google-search-results")
        return manual_google_maps_instructions(city, state)
    except Exception as e:
        log(f"❌ Error: {e}")
        return []

def calculate_desperation_score(result: Dict) -> int:
    """
    Scores how desperately a lawyer needs leads (1-10).
    Higher = more desperate = more likely to buy.
    """
    score = 5  # Base
    
    rating = result.get('rating', 0)
    review_count = result.get('reviews', 0)
    
    # Low reviews = not much business
    if review_count < 50:
        score += 3
    elif review_count < 100:
        score += 2
    elif review_count < 200:
        score += 1
    
    # Lower rating = communication problems (our value prop!)
    if rating < 4.0:
        score += 2
    elif rating < 4.3:
        score += 1
    
    # No website = not investing in marketing
    if not result.get('website'):
        score += 1
    
    return min(10, score)

def guess_email(website: str, business_name: str) -> str:
    """Guesses contact email."""
    if not website:
        return ''
    
    domain = website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
    
    # Common patterns for law firms
    return f"info@{domain}"

def manual_google_maps_instructions(city: str, state: str) -> List[Dict]:
    """Instructions for manual scraping."""
    log(f"\n{'📋'*35}")
    log(f"MANUAL INSTRUCTIONS: {city}, {state}")
    log(f"{'📋'*35}")
    log(f"\n1. Open Google Maps")
    log(f"2. Search: 'personal injury lawyer {city} {state}'")
    log(f"3. Copy top 50 results to CSV:")
    log(f"   - Business Name")
    log(f"   - Phone Number")
    log(f"   - Website")
    log(f"   - Rating")
    log(f"   - Review Count")
    log(f"4. Save as: pi_lawyers_{city.lower().replace(' ', '_')}.csv")
    log(f"5. Run: python upload_manual_lawyers.py pi_lawyers_{city.lower().replace(' ', '_')}.csv\n")
    
    return []

# ============================================================================
# OUTREACH MESSAGE GENERATOR
# ============================================================================

def generate_outreach_email(lawyer: Dict, injured_people_count: int = 0) -> Dict:
    """
    Generates personalized cold email to PI lawyer.
    
    Args:
        lawyer: Lawyer data from Google Maps
        injured_people_count: How many leads you have in their city
    
    Returns:
        Dict with subject, body, follow_up
    """
    firm_name = lawyer['business_name']
    city = lawyer['city']
    state = lawyer['state']
    desperation = lawyer['desperation_score']
    
    # Tailor message based on desperation score
    if desperation >= 8:
        # VERY desperate - direct approach
        subject = f"50+ qualified PI clients in {city} waiting for representation"
        
        body = f"""Hi there,

I run a lead generation service for Personal Injury lawyers, and I noticed {firm_name} on Google Maps.

I have something that might interest you:

**I currently have {injured_people_count or '50+'} people in {city} who were recently injured and are actively looking for PI representation.**

All of them:
✓ Injured within last 60 days
✓ Clear liability (not their fault)
✓ Went to doctor/ER
✓ Do NOT have a lawyer yet
✓ Ready to hire THIS WEEK

**Pricing:** You only pay when a client actually shows up to consultation - $800 per show.

No upfront cost. No monthly fees. Just qualified consultations delivered to your calendar.

These are first-come, first-served. If you don't want them, I'll offer them to another PI firm in {city} within 24 hours.

Want to see the full list? Reply "YES" and I'll send you the details.

Best regards,
[Your Name]
Lead Generation Specialist
[Your Phone]
[Your Email]

P.S. - {firm_name} has {lawyer['review_count']} reviews on Google. Most firms I work with see 20-30% more consultations within the first month. Just something to consider."""

    elif desperation >= 6:
        # Moderately desperate - value-focused
        subject = f"Thought for {firm_name}'s client acquisition"
        
        body = f"""Hi there,

I came across {firm_name} while researching top PI firms in {city}, and I wanted to reach out.

I specialize in helping Personal Injury lawyers get more qualified consultations without spending more on marketing.

Here's what I do:

→ Find people who were recently injured (car accidents, slip & falls, etc.)
→ Pre-qualify them (verify injury, liability, no current lawyer)
→ Deliver them directly to your calendar

You only pay when they actually show up: $800 per consultation.

**Current pipeline:** I have {injured_people_count or '40+'} qualified injury victims in {city} area looking for representation right now.

Most of my clients book 10-15 consultations per month, which typically converts to 3-5 signed cases.

Would you be open to a quick 10-minute call this week to discuss how this could work for {firm_name}?

Best regards,
[Your Name]
[Your Phone] | [Your Email]"""

    else:
        # Less desperate - soft approach
        subject = f"Quick question about {firm_name}"
        
        body = f"""Hi there,

My name is [Your Name], and I help PI lawyers in {city} capture more qualified leads.

I noticed {firm_name} has a strong reputation ({lawyer['rating']}/5 stars), which is impressive in such a competitive market.

I'm reaching out because I've built a system that helps firms like yours:

• Respond to injury inquiries within minutes (24/7)
• Qualify leads automatically
• Book consultations directly to your calendar
• Follow up so no lead falls through the cracks

The firms I work with typically see 15-20% more consultations without hiring additional staff.

Would you be interested in a brief 10-minute demo? I can show you exactly how it works for {firm_name}.

Best regards,
[Your Name]
[Your Phone] | [Your Email]"""
    
    # Follow-up message (send 3 days later if no response)
    follow_up = f"""Hi again,

Just following up on my email from a few days ago.

I still have those {injured_people_count or '40+'} injured people in {city} looking for PI representation.

Quick question: Is lead generation something {firm_name} is interested in, or should I focus on other firms in the area?

Either way is fine - just want to make sure I'm not bothering you if this isn't a fit.

Thanks,
[Your Name]"""
    
    return {
        'subject': subject,
        'body': body,
        'follow_up': follow_up,
        'desperation_score': desperation
    }

# ============================================================================
# SAVE FUNCTIONS
# ============================================================================

def save_lawyers_to_csv(lawyers: List[Dict], filename: str = 'pi_lawyers_prospects.csv'):
    """Saves lawyers to CSV for review."""
    if not lawyers:
        return
    
    log(f"\n💾 Saving {len(lawyers)} lawyers to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['business_name', 'city', 'state', 'phone', 'website', 
                     'contact_email', 'rating', 'review_count', 'desperation_score', 
                     'google_maps_url', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for lawyer in lawyers:
            row = {k: lawyer.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    log(f"✅ Saved to {filename}")

def save_lawyers_to_database(lawyers: List[Dict]):
    """Saves lawyers to Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Database unavailable")
        return
    
    saved = 0
    duplicates = 0
    
    for lawyer in lawyers:
        try:
            # Check duplicate
            existing = supabase.table('pi_lawyer_clients')\
                .select('id')\
                .eq('business_name', lawyer['business_name'])\
                .eq('city', lawyer['city'])\
                .execute()
            
            if existing.data:
                duplicates += 1
                continue
            
            # Save
            supabase.table('pi_lawyer_clients').insert({
                'business_name': lawyer['business_name'],
                'contact_email': lawyer['contact_email'],
                'contact_phone': lawyer.get('phone'),
                'city': lawyer['city'],
                'state': lawyer['state'],
                'website': lawyer.get('website'),
                'rating': lawyer.get('rating'),
                'review_count': lawyer.get('review_count'),
                'desperation_score': lawyer.get('desperation_score'),
                'status': 'prospect',
                'price_per_lead': 800.00,
                'found_date': lawyer.get('found_date')
            }).execute()
            
            saved += 1
            log(f"  ✅ Saved: {lawyer['business_name']}")
            
        except Exception as e:
            log(f"  ❌ Error: {e}")
    
    log(f"\n💾 DATABASE: Saved {saved}, Duplicates {duplicates}")

def generate_outreach_queue(lawyers: List[Dict], injured_count_by_city: Dict = None):
    """Generates outreach messages and saves to database."""
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Database unavailable")
        return
    
    log(f"\n{'='*70}")
    log("📧 Generating Outreach Messages")
    log(f"{'='*70}")
    
    generated = 0
    
    for lawyer in lawyers:
        city = lawyer['city']
        injured_count = injured_count_by_city.get(city, 0) if injured_count_by_city else 0
        
        # Generate message
        message = generate_outreach_email(lawyer, injured_count)
        
        try:
            # Save to outreach queue
            supabase.table('outreach_queue').insert({
                'lawyer_id': lawyer.get('id'),  # If saved to DB first
                'business_name': lawyer['business_name'],
                'recipient_email': lawyer['contact_email'],
                'email_subject': message['subject'],
                'email_body': message['body'],
                'follow_up_body': message['follow_up'],
                'desperation_score': message['desperation_score'],
                'status': 'pending_review',  # Review before sending
                'created_at': datetime.now().isoformat()
            }).execute()
            
            generated += 1
            log(f"  ✅ Generated message for {lawyer['business_name']}")
            
        except Exception as e:
            log(f"  ❌ Error: {e}")
    
    log(f"\n✅ Generated {generated} outreach messages")
    log("📋 Go to Supabase → outreach_queue → Review messages")
    log("✏️ Edit with your name/phone/email")
    log("✅ Change status to 'approved' when ready to send")

# ============================================================================
# MASTER ORCHESTRATOR
# ============================================================================

def run_lawyer_finder():
    """Main function: Finds PI lawyers in all target cities."""
    log("="*70)
    log("🎯 PI LAWYER FINDER: Finding Your Customers")
    log("="*70)
    
    all_lawyers = []
    
    # Find lawyers in top 5 cities first
    for location in TARGET_CITIES[:5]:
        lawyers = find_pi_lawyers_google_maps(
            location['city'], 
            location['state'], 
            limit=50
        )
        
        all_lawyers.extend(lawyers)
        
        # Delay between cities
        import time
        time.sleep(5)
    
    log(f"\n{'='*70}")
    log(f"📊 TOTAL LAWYERS FOUND: {len(all_lawyers)}")
    log(f"{'='*70}")
    
    if all_lawyers:
        # Save to CSV and database
        save_lawyers_to_csv(all_lawyers)
        save_lawyers_to_database(all_lawyers)
        
        # Generate outreach messages
        generate_outreach_queue(all_lawyers)
        
        # Print top prospects
        log(f"\n🎯 TOP 10 PROSPECTS (Most Desperate for Leads):")
        top_prospects = sorted(all_lawyers, key=lambda x: x['desperation_score'], reverse=True)[:10]
        
        for i, lawyer in enumerate(top_prospects, 1):
            log(f"\n{i}. {lawyer['business_name']}")
            log(f"   📍 {lawyer['city']}, {lawyer['state']}")
            log(f"   ⭐ Rating: {lawyer['rating']}/5 ({lawyer['review_count']} reviews)")
            log(f"   📞 {lawyer['phone']}")
            log(f"   📧 {lawyer['contact_email']}")
            log(f"   🔥 Desperation: {lawyer['desperation_score']}/10")
    
    log("\n" + "="*70)
    log("✅ LAWYER FINDER: Complete")
    log("="*70)
    log("\n📋 NEXT STEPS:")
    log("1. Review CSV file: pi_lawyers_prospects.csv")
    log("2. Check Supabase: pi_lawyer_clients table")
    log("3. Review messages: outreach_queue table")
    log("4. Edit messages with your info")
    log("5. Approve messages (change status to 'approved')")
    log("6. Run: python send_approved_outreach.py")

if __name__ == "__main__":
    run_lawyer_finder()
