from sentence_transformers import SentenceTransformer
from supabase import create_client
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

rows = supabase.table("breakout_projects") \
    .select("id, description") \
    .is_("embedding", None) \
    .execute().data

print(len(rows))

for row in rows:
    text = row["description"]
    embedding = model.encode(text).tolist()

    supabase.table("breakout_projects").update({
        "embedding": embedding
    }).eq("id", row["id"]).execute()