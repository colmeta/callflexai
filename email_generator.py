# --- email_generator.py ---
# Generates personalized emails for dentists about your chatbot
# Run: python email_generator.py

import os
import sys
from datetime import datetime
from typing import Dict, Tuple

sys.path.append(os.path.dirname(__file__))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

# ============================================================================
# EMAIL TEMPLATE GENERATOR
# ============================================================================

def generate_chatbot_email(dentist: Dict) -> Tuple[str, str]:
    """
    Generates personalized email based on dentist's pain points.
    
    Args:
        dentist: Dentist data from database
    
    Returns:
        Tuple of (subject, body)
    """
    business_name = dentist.get('business_name', 'your practice')
    city = dentist.get('city', 'your area')
    state = dentist.get('state', '')
    pain_points = dentist.get('pain_points', [])
    rating = dentist.get('rating', 0)
    review_count = dentist.get('review_count', 0)
    score = dentist.get('needs_chatbot_score', 5)
    
    # Convert pain_points if it's a string
    if isinstance(pain_points, str):
        pain_points = [p.strip() for p in pain_points.split(',')]
    
    # Select template based on pain points and score
    if score >= 8:
        return high_urgency_template(business_name, city, state, pain_points, rating, review_count)
    elif score >= 6:
        return medium_urgency_template(business_name, city, state, pain_points, rating, review_count)
    else:
        return standard_template(business_name, city, state, pain_points, rating, review_count)

def high_urgency_template(business_name: str, city: str, state: str, 
                         pain_points: list, rating: float, review_count: int) -> Tuple[str, str]:
    """For dentists with urgent automation needs."""
    
    subject = f"Quick question about {business_name}'s patient scheduling"
    
    # Identify main pain point
    main_pain = pain_points[0] if pain_points else "scheduling"
    
    body = f"""Hi there,

I was researching dental practices in {city} and came across {business_name}.

I noticed you have {review_count} reviews on Google (impressive!), but I also saw something that caught my attention: {main_pain}.

I'm reaching out because I built something specifically for this problem.

**It's an AI chatbot that handles:**
• Patient inquiries 24/7 (even when your office is closed)
• Appointment scheduling & confirmations
• Insurance questions
• FAQs about procedures
• Follow-up reminders

**What makes it different:**
✓ Responds in under 60 seconds
✓ Integrates with your existing practice management software
✓ Sounds natural (not robotic)
✓ Learns from your practice's specific procedures

**Results from similar practices:**
• 40% reduction in missed calls
• 3-5 more bookings per week
• 10+ hours saved on phone calls
• Better patient satisfaction scores

The setup takes about 15 minutes, and I offer a 14-day free trial so you can see the results yourself.

Would you be open to a quick 10-minute demo this week? I can show you exactly how it would work for {business_name}.

Best regards,
[Your Name]
[Your Company]
[Your Phone]
[Your Email]

P.S. - First 10 practices in {city} get lifetime priority support at no extra cost."""
    
    return subject, body

def medium_urgency_template(business_name: str, city: str, state: str,
                           pain_points: list, rating: float, review_count: int) -> Tuple[str, str]:
    """For dentists with moderate needs."""
    
    subject = f"Thought for {business_name}"
    
    body = f"""Hi there,

My name is [Your Name], and I help dental practices in {city} automate their patient communication.

I came across {business_name} and was impressed by your {rating}/5 star rating. That's not easy to achieve in such a competitive market.

I'm reaching out because many practices like yours are losing 20-30% of potential patients simply because:
• Calls go to voicemail after hours
• Staff is busy during appointments
• Follow-up messages get delayed

**That's where my AI chatbot comes in:**

It acts as a 24/7 virtual receptionist that:
→ Answers patient questions instantly
→ Books appointments automatically
→ Sends reminders and confirmations
→ Follows up on missed calls

**Real numbers from a practice like yours:**
• Went from 15 to 23 new patient bookings per month
• Reduced no-shows from 18% to 6%
• Saved their front desk 12 hours per week

The best part? It costs less than hiring a part-time receptionist, and it never takes a day off.

Would you be interested in seeing how it works? I can give you a personalized demo in under 10 minutes.

Best regards,
[Your Name]
[Your Company]
[Your Phone] | [Your Email]

P.S. - Setup takes 15 minutes, and you can try it free for 14 days. No credit card required."""
    
    return subject, body

def standard_template(business_name: str, city: str, state: str,
                     pain_points: list, rating: float, review_count: int) -> Tuple[str, str]:
    """Standard template for all dentists."""
    
    subject = f"AI assistant for {business_name}?"
    
    body = f"""Hi there,

I help dental practices like {business_name} capture more patients without adding staff.

Here's the problem I solve:

**Every day, your practice probably:**
• Misses calls during appointments
• Loses patients who call after hours
• Spends hours on repetitive questions
• Deals with no-shows and cancellations

**My AI chatbot handles all of this automatically:**

✓ Responds to inquiries in under 60 seconds (24/7)
✓ Books appointments while you sleep
✓ Answers insurance and procedure questions
✓ Sends automated reminders
✓ Follows up with missed calls

**What dentists are saying:**
"We went from 3-4 missed calls per day to zero. The chatbot caught every single one." - Dr. Sarah M., Austin TX

"Our bookings increased 35% in the first month. Best ROI we've ever seen." - Dr. James K., Miami FL

**Pricing:**
$297/month (less than 1 patient booking)
14-day free trial
Cancel anytime

Would you be open to a quick 10-minute demo? I can show you exactly how it would work for {business_name}.

Best regards,
[Your Name]
[Your Company]
[Your Phone] | [Your Email]

P.S. - Setup takes 15 minutes. I'll configure everything for you."""
    
    return subject, body

# ============================================================================
# BATCH EMAIL GENERATION
# ============================================================================

def generate_emails_for_all_dentists():
    """
    Generates emails for all dentists in database and saves to outreach queue.
    """
    log("="*70)
    log("📧 EMAIL GENERATOR: Starting...")
    log("="*70)
    
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Database connection failed")
        return
    
    try:
        # Get all dentists with status 'new' who have email addresses
        log("\n🔍 Fetching dentists from database...")
        
        response = supabase.table('dentists')\
            .select('*')\
            .eq('status', 'new')\
            .not_.is_('contact_email', 'null')\
            .order('needs_chatbot_score', desc=True)\
            .execute()
        
        dentists = response.data
        
        if not dentists:
            log("⚠️ No dentists found with status 'new' and email address")
            log("💡 Run: python dentist_scraper.py first")
            return
        
        log(f"✅ Found {len(dentists)} dentists ready for outreach")
        
        # Generate emails
        log(f"\n📝 Generating personalized emails...")
        
        generated = 0
        skipped = 0
        
        for dentist in dentists:
            dentist_id = dentist.get('id')
            business_name = dentist.get('business_name')
            email = dentist.get('contact_email')
            
            if not email or email == '':
                log(f"  ⚠️ Skipping {business_name} - no email")
                skipped += 1
                continue
            
            try:
                # Generate email
                subject, body = generate_chatbot_email(dentist)
                
                # Save to outreach queue
                supabase.table('outreach_queue').insert({
                    'dentist_id': dentist_id,
                    'recipient_email': email,
                    'recipient_name': business_name,
                    'email_subject': subject,
                    'email_body': body,
                    'status': 'pending'
                }).execute()
                
                generated += 1
                log(f"  ✅ Generated for {business_name}")
                
            except Exception as e:
                log(f"  ❌ Error generating for {business_name}: {e}")
                skipped += 1
        
        log(f"\n{'='*70}")
        log(f"📊 RESULTS:")
        log(f"  Generated: {generated}")
        log(f"  Skipped: {skipped}")
        log(f"{'='*70}")
        
        if generated > 0:
            log("\n✅ SUCCESS! Emails are ready in the outreach_queue table")
            log("\n📋 NEXT STEPS:")
            log("1. Go to Supabase → outreach_queue table")
            log("2. Review the generated emails")
            log("3. Edit [Your Name], [Your Company], etc. with your info")
            log("4. Run: python send_emails.py (to send them)")
        
    except Exception as e:
        log(f"❌ Critical error: {e}")
        import traceback
        log(traceback.format_exc())

# ============================================================================
# SINGLE EMAIL PREVIEW
# ============================================================================

def preview_email_for_dentist(business_name: str):
    """
    Generates and prints a preview of an email for a specific dentist.
    
    Args:
        business_name: Name of the dental practice
    """
    supabase = get_supabase_client()
    if not supabase:
        log("❌ Database connection failed")
        return
    
    try:
        response = supabase.table('dentists')\
            .select('*')\
            .ilike('business_name', f'%{business_name}%')\
            .limit(1)\
            .execute()
        
        if not response.data:
            log(f"❌ Dentist '{business_name}' not found in database")
            return
        
        dentist = response.data[0]
        subject, body = generate_chatbot_email(dentist)
        
        log("\n" + "="*70)
        log(f"📧 EMAIL PREVIEW: {dentist['business_name']}")
        log("="*70)
        log(f"\n📍 Location: {dentist['city']}, {dentist['state']}")
        log(f"⭐ Rating: {dentist['rating']}/5 ({dentist['review_count']} reviews)")
        log(f"🤖 Chatbot Need Score: {dentist['needs_chatbot_score']}/10")
        log(f"💡 Pain Points: {', '.join(dentist.get('pain_points', []))}")
        log("\n" + "-"*70)
        log(f"SUBJECT: {subject}")
        log("-"*70)
        log(body)
        log("="*70 + "\n")
        
    except Exception as e:
        log(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Preview mode: python email_generator.py "Practice Name"
        practice_name = ' '.join(sys.argv[1:])
        log(f"🔍 Previewing email for: {practice_name}")
        preview_email_for_dentist(practice_name)
    else:
        # Batch mode: generate for all dentists
        generate_emails_for_all_dentists()
