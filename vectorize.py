import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

# ============================================================
# LOAD ENV VARIABLES
# ============================================================
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "l1-support-tickets")

if not PINECONE_API_KEY:
    raise ValueError("❌ PINECONE_API_KEY not set")

# ============================================================
# LOAD DATA
# ============================================================
TICKETS_FILE = "tickets.json"

with open(TICKETS_FILE, "r", encoding="utf-8") as f:
    tickets = json.load(f)

print(f"Loaded {len(tickets)} tickets")

# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================
print("Loading embedding model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
VECTOR_DIM = embedder.get_sentence_embedding_dimension()

# ============================================================
# INIT PINECONE CLIENT
# ============================================================
pc = Pinecone(api_key=PINECONE_API_KEY)

# ============================================================
# CREATE INDEX IF NOT EXISTS
# ============================================================
existing_indexes = [i["name"] for i in pc.list_indexes()]

if PINECONE_INDEX_NAME not in existing_indexes:
    print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=VECTOR_DIM,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

index = pc.Index(PINECONE_INDEX_NAME)

# ============================================================
# VECTORIZE + UPSERT
# ============================================================
vectors = []

print("Vectorizing tickets...")

for ticket in tqdm(tickets):
    embedding = embedder.encode(ticket["Content"]).tolist()

    metadata = {
        "ticket_id": ticket["Ticket ID"],
        "organization": ticket["Organization"],
        "category": ticket["Category"],
        "issue_type": ticket["issue_type"],
        "support_level": ticket["support_level"]
    }

    vectors.append({
        "id": ticket["Ticket ID"],
        "values": embedding,
        "metadata": metadata
    })

# ============================================================
# UPSERT IN BATCHES
# ============================================================
BATCH_SIZE = 50

print("Uploading vectors to Pinecone...")

for i in range(0, len(vectors), BATCH_SIZE):
    index.upsert(vectors=vectors[i:i + BATCH_SIZE])

print("✅ Vectorization complete!")
print(index.describe_index_stats())
