# --- database.py (FIXED - NO PROXY!) ---
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

supabase: Client = None

try:
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        # CRITICAL: Remove ANY proxy arguments!
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Database connected!")
    else:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
except Exception as e:
    print(f"❌ Database error: {e}")

def get_supabase_client():
    return supabase
