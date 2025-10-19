# --- database.py (FINAL - NO PROXY) ---
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client():
    """Returns initialized Supabase client (no proxy)."""
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing Supabase credentials")
        return None
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Database connected!")
        return client
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None
