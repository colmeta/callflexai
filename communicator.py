# --- communicator.py ---
# This module is responsible for generating personalized outreach.

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def log(message):
    from datetime import datetime
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def generate_outreach_email(business_name, pain_points):
    """
    Uses an AI model to generate a personalized cold email subject and body.
    """
    log(f"Communicator: Preparing to write email for '{business_name}'...")
    
    if not GEMINI_API_KEY:
        log("Communicator: ERROR - Gemini API key is missing. Cannot generate email.")
        return None, None
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Using the most modern, efficient model
        
        # We craft a highly specific prompt to get the best results.
        prompt = f"""
        You are an expert copywriter for a company called CallFlex AI.
        Your goal is to write a short, compelling, and friendly cold email to a local business owner.
        
        Business Name: "{business_name}"
        Identified Pain Points: Your customers have mentioned issues with "{pain_points}".
        
        Based on this, generate a JSON object with two fields: "subject" and "body".
        - The subject should be intriguing and personalized, under 7 words.
        - The body should be under 150 words. It must start by acknowledging their good reputation, subtly mention the communication pain point you identified, and offer CallFlex AI's automated callback system as a solution to never lose a lead again. End with a simple call to action, like asking for a brief chat.
        
        Respond with ONLY the valid JSON object. Example format:
        {{"subject": "A quick thought on your calls", "body": "Hi [Business Owner Name], ..."}}
        """

        response = model.generate_content(prompt)
        raw_text_output = response.text
        log(f"Communicator: RAW AI Output received:\n---\n{raw_text_output}\n---")
        
        # Clean the response to ensure it's a valid JSON object
        import json
        cleaned_text = raw_text_output.strip().replace('```json', '').replace('```', '').strip()
        
        if '{' in cleaned_text and '}' in cleaned_text:
            start = cleaned_text.find('{')
            end = cleaned_text.rfind('}') + 1
            cleaned_text = cleaned_text[start:end]
            
            email_data = json.loads(cleaned_text)
            
            if 'subject' in email_data and 'body' in email_data:
                log(f"Communicator: SUCCESS - Email for '{business_name}' generated.")
                return email_data['subject'], email_data['body']
        
        log(f"Communicator: ERROR - Failed to parse valid JSON from AI response.")
        return None, None

    except Exception as e:
        log(f"Communicator: CRITICAL AI ERROR during email generation: {e}")
        return None, None
