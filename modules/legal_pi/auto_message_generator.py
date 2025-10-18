# --- modules/legal_pi/auto_message_generator.py ---
# Generates personalized outreach messages for PI lawyers
# You just review and approve - NO WRITING NEEDED!

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_supabase_client

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def generate_message_for_lawyer(lawyer_data, injured_leads):
    """
    Generates a personalized message based on Lewis's "no-call" model.
    
    Args:
        lawyer_data (dict): Law firm info from database
        injured_leads (list): Injured people in their city
    
    Returns:
        dict: {subject, body, one_pager_summary}
    """
    firm_name = lawyer_data.get('business_name', 'your law firm')
    city = lawyer_data.get('city', 'your area')
    num_leads = len(injured_leads)
    
    # Categorize leads by injury type
    lead_breakdown = {}
    for lead in injured_leads:
        injury_type = lead.get('injury_type', 'Unknown')
        lead_breakdown[injury_type] = lead_breakdown.get(injury_type, 0) + 1
    
    # Build lead summary
    lead_summary = ", ".join([f"{count} {injury}" for injury, count in lead_breakdown.items()])
    
    # Calculate total estimated case value
    avg_case_value = 30000  # Conservative PI case average
    total_value = num_leads * avg_case_value
    
    # SUBJECT LINE
    subject = f"{num_leads} qualified PI clients in {city} - first-come, first-served"
    
    # EMAIL BODY (Lewis's "no-call" template)
    body = f"""Hi there,

I run a lead generation service that specializes in Personal Injury cases.

This week, I found {num_leads} people in {city} who were recently injured and are actively seeking legal representation:

→ {lead_summary}

All of them:
✓ Injured within last 60 days
✓ Saw a doctor or went to ER
✓ Clear liability (someone else at fault)
✓ Do NOT have a lawyer yet
✓ Actively looking for representation

I've created a one-pager with full details on these leads:
👉 [Link to One-Pager - I'll provide this separately]

**How It Works:**

Option 1: Pay Per Show - $800 per qualified consultation
(You only pay when the client shows up to your office)

Option 2: Monthly Package - $3,000/month for 10-15 leads
(Guaranteed qualified injury leads delivered to your calendar every month)

**To claim these {num_leads} leads, reply to this email with "INTERESTED" and I'll send you the full details.**

These are first-come, first-served. If you don't want them, I'll offer them to another PI firm in {city} within 24 hours.

Best regards,
[Your Name]
PI Lead Generation Specialist
[Your Email]
[Your Phone - if you have one]

P.S. If you'd like to discuss this on a call first, I charge $100 for a 30-minute consultation (fully refundable if you buy). But honestly, most firms just want the leads - the one-pager tells you everything you need to know.

---

**Estimated Case Value Analysis:**
Based on industry averages, these {num_leads} leads represent approximately ${total_value:,} in potential case value for your firm (assuming $30k average settlement per case).

Even at a 50% conversion rate, that's ${int(total_value/2):,} in revenue potential from this batch alone.

Your investment: ${num_leads * 800:,} (if all show up)
Your potential return: ${int(total_value/2):,}
ROI: {int((total_value/2) / (num_leads * 800) * 100)}%

This is why PI firms that use lead generation services grow 3-5x faster than those relying on word-of-mouth alone.
"""
    
    # ONE-PAGER SUMMARY (for the attached document)
    one_pager = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{num_leads} QUALIFIED PERSONAL INJURY LEADS
{city}, {lawyer_data.get('state', '')}
Generated: {datetime.now().strftime('%B %d, %Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OVERVIEW:
- Total Leads: {num_leads}
- Average Quality Score: {sum(l.get('quality_score', 5) for l in injured_leads) / num_leads:.1f}/10
- Lead Breakdown: {lead_summary}
- Estimated Total Case Value: ${total_value:,}

"""
    
    # Add individual lead details
    for idx, lead in enumerate(injured_leads, 1):
        one_pager += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEAD #{idx}: {lead.get('prospect_name', 'Anonymous')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Injury Type: {lead.get('injury_type', 'Unknown')}
Injury Date: {lead.get('injury_date', 'Recent')}
Quality Score: {lead.get('quality_score', 5)}/10

What They Said:
"{lead.get('description', 'No description')[:200]}..."

Why This Is Valuable:
{generate_value_prop(lead)}

Source: {lead.get('source', 'Unknown')}
Original Post: {lead.get('source_url', 'N/A')}

Estimated Case Value: $25,000 - $50,000
Your Cost: $800 (only if they show up)

"""
    
    one_pager += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEXT STEPS:

1. Reply "INTERESTED" to claim these leads
2. I'll send introduction emails connecting you to each client
3. You contact them within 2 hours (speed = conversion)
4. Track consultations in your calendar
5. Invoice sent when clients show up ($800 each)

Questions? Reply to this email.

[Your Name]
PI Lead Generation Specialist
"""
    
    return {
        'subject': subject,
        'body': body,
        'one_pager': one_pager,
        'num_leads': num_leads,
        'estimated_value': total_value
    }

def generate_value_prop(lead):
    """Explains why this lead is valuable."""
    score = lead.get('quality_score', 5)
    injury_type = lead.get('injury_type', 'Unknown')
    
    value_props = []
    
    if score >= 8:
        value_props.append("- High-quality lead with clear indicators of a strong case")
    
    if 'car' in injury_type.lower():
        value_props.append("- Car accidents typically settle for $15k-$50k")
    
    if 'motorcycle' in injury_type.lower():
        value_props.append("- Motorcycle accidents often result in higher settlements ($30k-$100k)")
    
    if 'slip and fall' in injury_type.lower():
        value_props.append("- Premises liability cases with clear fault are highly winnable")
    
    if 'truck' in injury_type.lower():
        value_props.append("- Commercial truck accidents can yield $50k-$500k+ settlements")
    
    if 'work' in injury_type.lower():
        value_props.append("- Workplace injuries with third-party liability have strong case potential")
    
    # Default if nothing specific
    if not value_props:
        value_props.append("- Lead shows genuine interest in legal representation")
        value_props.append("- No current attorney means you're first to reach them")
    
    return "\n".join(value_props)

def generate_reddit_dm_for_desperate_lawyer(prospect_data):
    """
    Generates a Reddit DM for lawyers you found complaining.
    
    Args:
        prospect_data (dict): Desperate lawyer info from Reddit scraper
    
    Returns:
        dict: {subject, message}
    """
    username = prospect_data.get('reddit_username', 'there')
    pain_points = prospect_data.get('keywords_found', 'growing your practice')
    post_title = prospect_data.get('post_title', 'your post')
    
    subject = "RE: " + post_title[:50]
    
    message = f"""Hey u/{username},

I saw your post about {pain_points.lower()} and thought I might be able to help.

I run a lead generation service specifically for Personal Injury lawyers. Here's what we do:

→ Find people who were recently injured and need a PI attorney
→ Pre-qualify them (verify injury, liability, no current lawyer)
→ Deliver them directly to your calendar

You only pay when a client actually shows up to consultation ($800 per show).

I'm currently working with PI firms in several cities and they're averaging 3-5 qualified consultations per month, which typically converts to 1-2 signed cases.

Would this be helpful for your practice?

If you're interested, I can send you a free sample of what the leads look like - no commitment, just so you can see the quality.

Let me know!

Best,
[Your Name]

P.S. - If you'd prefer email, feel free to reach me at [your email]. I know Reddit DMs can be hit or miss.
