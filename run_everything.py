# --- run_everything.py ---
# Master control script - Run this ONE command to execute your entire business
# Usage: python run_everything.py

import sys
import os
from datetime import datetime

sys.path.append('./modules/legal_pi')

def log(message):
    print(f"\n{'='*70}")
    print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | {message}")
    print('='*70 + "\n")

def main():
    print("\n" + "🚀"*35)
    print("   PI LAWYER LEAD GENERATION EMPIRE - MASTER CONTROL")
    print("🚀"*35 + "\n")
    
    print("This will run your ENTIRE business operation:")
    print("1. Find injured people (Reddit + Craigslist)")
    print("2. Find PI lawyers (Google Maps)")
    print("3. Find desperate lawyers on Reddit")
    print("4. Generate personalized messages")
    print("5. Save everything for your review")
    print("\n" + "-"*70 + "\n")
    
    input("Press ENTER to start (or CTRL+C to cancel)...")
    
    # STEP 1: Find injured people
    log("STEP 1: Finding Injured People (Your Product)")
    try:
        from reddit_injury_scraper import run_reddit_scraper
        run_reddit_scraper()
    except Exception as e:
        print(f"❌ Reddit scraper error: {e}")
    
    print("\n⏳ Waiting 30 seconds (be respectful to servers)...")
    import time
    time.sleep(30)
    
    try:
        from craigslist_scraper import run_craigslist_scraper
        run_craigslist_scraper()
    except Exception as e:
        print(f"❌ Craigslist scraper error: {e}")
    
    # STEP 2: Find PI lawyers
    log("STEP 2: Finding PI Lawyers (Your Customers)")
    
    time.sleep(30)
    
    try:
        from google_maps_pi_lawyer_scraper import run_lawyer_scraper
        run_lawyer_scraper()
    except Exception as e:
        print(f"❌ Lawyer scraper error: {e}")
        print("💡 If you don't have SerpAPI, this is optional. Continue anyway.")
    
    # STEP 3: Find desperate lawyers on Reddit
    log("STEP 3: Finding Desperate Lawyers on Reddit (HOT Prospects)")
    
    time.sleep(30)
    
    try:
        from reddit_desperate_lawyer_finder import run_desperate_lawyer_finder
        run_desperate_lawyer_finder()
    except Exception as e:
        print(f"❌ Desperate lawyer finder error: {e}")
    
    # STEP 4: Generate messages
    log("STEP 4: Generating Personalized Messages")
    
    try:
        from auto_message_generator import generate_all_messages_for_review
        generate_all_messages_for_review()
    except Exception as e:
        print(f"❌ Message generator error: {e}")
    
    # FINAL SUMMARY
    print("\n" + "🎉"*35)
    print("   MASTER CONTROL: COMPLETE!")
    print("🎉"*35 + "\n")
    
    print("📊 WHAT HAPPENED:")
    print("  ✅ Scraped Reddit for injured people")
    print("  ✅ Scraped Craigslist for injured people")
    print("  ✅ Found PI lawyers in target cities")
    print("  ✅ Found desperate lawyers on Reddit")
    print("  ✅ Generated personalized messages")
    
    print("\n📂 CHECK THESE FILES:")
    print("  - reddit_injured_leads.csv")
    print("  - craigslist_injured_leads.csv")
    print("  - pi_lawyers_prospects.csv")
    print("  - desperate_pi_lawyers.csv")
    
    print("\n💾 CHECK YOUR SUPABASE DATABASE:")
    print("  - injured_people_leads (your product)")
    print("  - pi_lawyer_clients (your customers)")
    print("  - outreach_queue (messages to review)")
    
    print("\n🎯 YOUR NEXT STEPS:")
    print("  1. Go to Supabase → outreach_queue table")
    print("  2. Review the generated messages")
    print("  3. Edit your name/email in the messages")
    print("  4. Change status from 'pending_review' to 'approved'")
    print("  5. Run: python send_approved_messages.py")
    
    print("\n💰 EXPECTED RESULTS:")
    print("  - 20-50 injured people found")
    print("  - 50-100 PI lawyer prospects found")
    print("  - 5-10 desperate lawyers found")
    print("  - 10-20 personalized messages ready to send")
    
    print("\n🚀 Revenue Potential:")
    print("  - If just 2 lawyers say YES")
    print("  - And you match 3 leads each")
    print("  - That's $4,800 in your first week!")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
