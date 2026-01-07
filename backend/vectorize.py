import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

# ================= ENV =================
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# ================= DATA =================
with open("tickets.json", "r", encoding="utf-8") as f:
    tickets = json.load(f)

# ================= EMBEDDINGS =================
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)

VECTOR_DIM = 1536

# ================= PINECONE =================
pc = Pinecone(api_key=PINECONE_API_KEY)

if INDEX_NAME not in [i["name"] for i in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=VECTOR_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(INDEX_NAME)

# ================= UPSERT (FIXED) =================
vectors = []

for t in tqdm(tickets):
    content = t["Content"]

    vec = embeddings.embed_query(content)

    vectors.append({
        "id": t["Ticket ID"],
        "values": vec,
        "metadata": {
            # 🔑 THIS IS THE FIX
            "text": content,

            # Optional filters / debugging
            "ticket_id": t["Ticket ID"],
            "organization": t["Organization"],
            "category": t["Category"],
            "issue_type": t["issue_type"],
            "support_level": t["support_level"]
        }
    })

for i in range(0, len(vectors), 50):
    index.upsert(vectors=vectors[i:i+50])

print("✅ Vectorization complete with text stored correctly")
