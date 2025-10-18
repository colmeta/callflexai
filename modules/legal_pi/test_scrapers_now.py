# --- test_scrapers_now.py ---
# Manual test script - Run this from your terminal to test scrapers NOW
# Usage: python test_scrapers_now.py

import sys
import os

# Add modules to path
sys.path.append('./modules/legal_pi')

from reddit_injury_scraper import run_reddit_scraper
from craigslist_scraper import run_craigslist_scraper

def main():
    print("\n" + "="*70)
    print("🧪 MANUAL SCRAPER TEST - Running Both Scrapers")
    print("="*70 + "\n")
    
    print("This will:")
    print("1. Search Reddit for injured people in top 5 USA cities")
    print("2. Search Craigslist for injury-related posts")
    print("3. Save results to CSV files (for your review)")
    print("4. Save results to Supabase database")
    print("\n" + "-"*70 + "\n")
    
    input("Press ENTER to start scraping (or CTRL+C to cancel)...")
    
    print("\n🔍 STEP 1: Running Reddit Scraper...")
    print("-"*70)
    try:
        run_reddit_scraper()
        print("\n✅ Reddit scraper completed successfully!")
    except Exception as e:
        print(f"\n❌ Reddit scraper failed: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("\n⏳ Waiting 10 seconds before Craigslist (be respectful)...")
    import time
    time.sleep(10)
    
    print("\n🔍 STEP 2: Running Craigslist Scraper...")
    print("-"*70)
    try:
        run_craigslist_scraper()
        print("\n✅ Craigslist scraper completed successfully!")
    except Exception as e:
        print(f"\n❌ Craigslist scraper failed: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("\n" + "="*70)
    print("🎉 TEST COMPLETE!")
    print("="*70)
    print("\n📊 Check these files:")
    print("  - reddit_injured_leads.csv")
    print("  - craigslist_injured_leads.csv")
    print("\n💾 Check your Supabase database:")
    print("  - Go to: https://supabase.com/dashboard/project/_/editor")
    print("  - Select table: injured_people_leads")
    print("  - You should see new rows!")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    # Check if .env exists
    if not os.path.exists('.env'):
        print("\n❌ ERROR: .env file not found!")
        print("Create a .env file with:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_SERVICE_KEY=your_service_key")
        sys.exit(1)
    
    main()
