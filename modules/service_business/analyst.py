# --- analyst.py ---
# This module contains the logic for analyzing business leads.

def log(message):
    """A simple logging function for this module."""
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def analyze_opportunity_with_keywords(business_name, reviews_text):
    """
    Analyzes review text for keywords to generate an opportunity score.
    This is our fast, free, no-AI method.
    """
    log(f"Analyst: Analyzing '{business_name}' with keyword matching...")
    
    keywords = {
        'call back': 3, 'callback': 3, 'never called': 4, 'no call': 2,
        'communication': 2, 'no response': 4, 'unreachable': 3, 'unresponsive': 3,
        'scheduling': 2, 'appointment': 1, 'no show': 4, 'follow-up': 2,
        'phone': 1, 'answer': 1, 'reach': 1, 'contact': 1, 'quote': 2
    }
    
    score = 0
    pain_points_found = []
    reviews_lower = reviews_text.lower()
    
    for keyword, points in keywords.items():
        if keyword in reviews_lower:
            score += points
            if keyword not in pain_points_found:
                 pain_points_found.append(keyword)
    
    final_score = min(score, 10)
    
    if final_score == 0:
        final_score = 3
        summary = "No specific communication pain points found via keywords."
    else:
        summary = f"Found {len(pain_points_found)} communication-related issues via keywords."
    
    analysis_result = {
        "opportunity_score": final_score,
        "pain_points": pain_points_found[:3],
        "summary": summary
    }
    
    log(f"Analyst: SUCCESS - Keyword analysis complete. Score: {analysis_result['opportunity_score']}")
    return analysis_result
