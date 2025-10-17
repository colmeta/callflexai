# --- database.py (FIXED FOR SUPABASE v2) ---
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables for local testing
load_dotenv()

# Get secrets from environment
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Initialize a global variable for the client
supabase: Client = None

try:
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        # FIXED: Removed proxy parameter (not supported in supabase-py v2)
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("Database client initialized successfully.")
    else:
        print("DATABASE ERROR: URL or Service Key is missing.")
except Exception as e:
    print(f"DATABASE CRITICAL ERROR: Could not initialize Supabase client: {e}")

def get_supabase_client():
    """Returns the initialized Supabase client."""
    return supabase
