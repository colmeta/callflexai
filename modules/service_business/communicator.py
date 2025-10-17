# --- communicator.py (MULTI-TEMPLATE VERSION) ---
# This module generates personalized outreach using context-aware templates.

def log(message):
    """Simple logging function."""
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def select_template(pain_points, opportunity_score):
    """
    Selects the best email template based on the pain points detected.
    
    Args:
        pain_points (list): List of keywords found in reviews
        opportunity_score (int): The lead's score (1-10)
    
    Returns:
        str: Template name to use
    """
    pain_points_lower = [p.lower() for p in pain_points]
    
    # High-urgency template (missed calls, no response, unreachable)
    if any(keyword in pain_points_lower for keyword in ['no call', 'never called', 'unreachable', 'no response']):
        return 'high_urgency'
    
    # Scheduling/appointment template
    elif any(keyword in pain_points_lower for keyword in ['scheduling', 'appointment', 'no show']):
        return 'scheduling_focused'
    
    # Communication template (general)
    elif 'communication' in pain_points_lower or 'phone' in pain_points_lower:
        return 'communication_focused'
    
    # Default template (when pain points are vague)
    else:
        return 'default'

def generate_outreach_email_from_template(business_name, pain_points_str, opportunity_score=5):
    """
    Generates a personalized email by selecting and filling the right template.
    
    Args:
        business_name (str): Name of the target business
        pain_points_str (str): Comma-separated pain points
        opportunity_score (int): Lead quality score (1-10)
    
    Returns:
        tuple: (subject, body) or (None, None) if error
    """
    log(f"Communicator: Generating email for '{business_name}'...")
    
    try:
        # Parse pain points
        pain_points = [p.strip() for p in pain_points_str.split(',') if p.strip()]
        
        # Select the best template
        template_type = select_template(pain_points, opportunity_score)
        log(f"Communicator: Using '{template_type}' template.")
        
        # Generate email based on template type
        if template_type == 'high_urgency':
            subject, body = template_high_urgency(business_name, pain_points)
        elif template_type == 'scheduling_focused':
            subject, body = template_scheduling(business_name, pain_points)
        elif template_type == 'communication_focused':
            subject, body = template_communication(business_name, pain_points)
        else:
            subject, body = template_default(business_name, pain_points)
        
        log(f"Communicator: SUCCESS - Email generated.")
        return subject, body
    
    except Exception as e:
        log(f"Communicator: ERROR: {e}")
        return None, None

# --- TEMPLATE LIBRARY ---

def template_high_urgency(business_name, pain_points):
    """Template for businesses with critical communication failures."""
    subject = f"Quick question about {business_name}'s missed calls"
    
    body = f"""Hi there,

I was researching local service businesses and came across {business_name}. Your ratings are impressive, but I noticed something in a few reviews that caught my attention.

It looks like some customers mentioned challenges reaching your team or getting callbacks. I know how frustrating that can be—especially when you're busy delivering great service and can't always get to the phone.

That's exactly why I built CallFlex AI. It ensures every single caller gets an instant response, even when you're with a customer, on a job, or after hours.

Here's what it does:
• Responds to missed calls within 60 seconds (via text or email)
• Qualifies leads automatically so you know who's hot and who's just browsing
• Sends you a morning briefing with prioritized leads ready to close

Most of our clients recover 2-3 extra jobs per week that they would've lost to competitors who answered first.

Would you be open to a quick 10-minute call this week? I can show you exactly how it works and we can see if it's a fit for {business_name}.

Best,
Collin
Founder, CallFlex AI
P.S. - First 5 businesses in your area get a 30-day free trial. No credit card required."""
    
    return subject, body

def template_scheduling(business_name, pain_points):
    """Template for businesses with appointment/scheduling issues."""
    subject = f"Thought for {business_name}'s scheduling process"
    
    body = f"""Hi there,

I came across {business_name} while researching top-rated local businesses, and I was impressed by your reputation.

I did notice a few customer mentions of scheduling challenges—getting appointments booked, coordinating times, that sort of thing. It's a common issue when you're juggling a busy schedule.

CallFlex AI was built specifically to solve this. It automates your entire intake process:

• Instantly responds when someone requests an appointment
• Asks qualifying questions to understand their needs
• Presents available time slots based on your calendar
• Confirms bookings and sends reminders

One of our clients (a dental practice) went from 12% no-shows to less than 3% just by having consistent automated reminders and follow-ups.

Would you be interested in a brief demo? I can show you how {business_name} could book 20-30% more appointments without adding staff.

Best,
Collin
Founder, CallFlex AI"""
    
    return subject, body

def template_communication(business_name, pain_points):
    """Template for general communication/follow-up issues."""
    subject = f"A quick thought for {business_name}"
    
    body = f"""Hi there,

I'm Collin, and I help local service businesses like {business_name} capture more leads without hiring more staff.

I was looking at your online presence and noticed you've built a strong reputation. That's not easy in a competitive market.

I did see a few customer reviews mentioning communication or follow-up challenges. No judgment—when you're busy delivering great service, it's hard to stay on top of every inquiry.

That's where CallFlex AI comes in. Think of it as your 24/7 digital assistant that:

• Responds to every inquiry within minutes
• Qualifies leads so you only talk to serious buyers
• Follows up automatically so no one falls through the cracks

It's like having a full-time receptionist for a fraction of the cost.

Would you be open to a 10-minute call this week to see how it works? I think {business_name} could easily capture 3-5 more customers per month.

Best,
Collin
Founder, CallFlex AI"""
    
    return subject, body

def template_default(business_name, pain_points):
    """Fallback template when pain points are unclear."""
    subject = f"Opportunity for {business_name}"
    
    body = f"""Hi there,

My name is Collin, and I help service businesses like yours thrive in competitive markets.

I came across {business_name} and was genuinely impressed with your ratings and reputation. That kind of consistent quality doesn't happen by accident.

I'm reaching out because I've built something that's helping local businesses like yours capture 15-20% more leads without adding headcount.

CallFlex AI is a fully automated lead response system that:
• Responds to inquiries 24/7 (even when you're closed)
• Qualifies leads so you focus on the best opportunities
• Sends you a daily briefing of hot leads ready to close

Most of our clients see ROI within the first month because they're no longer losing leads to competitors who respond faster.

Would you be open to a brief 10-minute call this week? I can show you exactly how it works for businesses like {business_name}.

Best,
Collin
Founder, CallFlex AI
P.S. - The first 5 businesses in your area get a 30-day trial at no cost."""
    
    return subject, body
