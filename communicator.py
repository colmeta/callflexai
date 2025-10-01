# --- communicator.py (Smart Template Version - NO AI) ---
# This module is responsible for generating personalized outreach using templates.

def log(message):
    """A simple logging function for this module."""
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def generate_outreach_email_from_template(business_name, pain_points_str):
    """
    Generates a personalized email by inserting pain points into a template.
    This is our fast, free, no-AI method.
    """
    log(f"Communicator: Preparing to write template email for '{business_name}'...")

    try:
        # Split the comma-separated string into a list of pain points
        pain_points = [p.strip() for p in pain_points_str.split(',')]
        
        # --- The Smart Template Logic ---
        # We can create multiple templates and choose based on the pain points found.
        # For now, we will use one powerful, universal template.
        
        pain_point_sentence = ""
        if pain_points:
            # Weave the customer's specific pain points into the email copy naturally.
            if len(pain_points) > 1:
                # e.g., "issues with 'no call' and 'scheduling'"
                pains_formatted = "' and '".join(pain_points)
                pain_point_sentence = f"I noticed a few customer reviews mentioning challenges with '{pains_formatted}'."
            else:
                # e.g., "issues with 'communication'"
                pain_point_sentence = f"I noticed a few customer reviews mentioning challenges with '{pain_points[0]}'."
        else:
            # A fallback if for some reason pain_points are empty.
            pain_point_sentence = "I was looking at your online presence and had an idea about your customer follow-ups."

        # --- The Email Content ---
        subject = f"A quick thought for {business_name}"
        
        body = f"""Hi there,

My name is Collin, and I help local service businesses like yours thrive. I was looking at your company online and was really impressed with your ratings.

{pain_point_sentence} It's a common challenge when you're busy delivering great service.

Our system, CallFlex AI, ensures you never lose a lead from a missed call again. It automatically follows up with every caller so you can capture the business without stopping your work.

Would you be open to a brief 10-minute chat next week to see how it works?

Best,

Collin
Founder, CallFlex AI
"""

        log(f"Communicator: SUCCESS - Email for '{business_name}' generated from template.")
        return subject, body

    except Exception as e:
        log(f"Communicator: CRITICAL ERROR during email template generation: {e}")
        return None, None
