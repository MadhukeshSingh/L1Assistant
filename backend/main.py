import os
import logging
from typing import List, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains.retrieval_qa.base import RetrievalQA

from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

# ==========================================================
# LOGGING CONFIGURATION
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("L1-RAG")

# ==========================================================
# ENV & CONFIG
# ==========================================================
logger.info("Loading environment variables...")
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME")

if not OPENAI_API_KEY or not PINECONE_INDEX_NAME:
    logger.error("Missing required environment variables.")
    raise RuntimeError("OPENAI_API_KEY or PINECONE_INDEX_NAME not set")

logger.info("Environment variables loaded successfully")

# ==========================================================
# FASTAPI APP
# ==========================================================
app = FastAPI(title="L1 Support RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("FastAPI app initialized")

# ==========================================================
# EMBEDDINGS & PINECONE
# ==========================================================
logger.info("Initializing embedding model...")
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)
logger.info("Embedding model initialized")

logger.info("Connecting to Pinecone index: %s", PINECONE_INDEX_NAME)
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=PINECONE_INDEX_NAME,
    embedding=embedding_model,
)
logger.info("Connected to Pinecone index successfully")

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)
logger.info("Retriever configured (k=3, similarity search)")

# ==========================================================
# LLM
# ==========================================================
logger.info("Initializing LLM...")
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    api_key=OPENAI_API_KEY
)
logger.info("LLM initialized successfully")

# ==========================================================
# STRICT RAG PROMPT
# ==========================================================
RAG_SYSTEM_PROMPT = """
You are an L1 IT Support Assistant.

STRICT RULES (MANDATORY):
- Answer ONLY using the information present in the provided context.
- Do NOT use general IT knowledge.
- Do NOT assume or infer anything not explicitly stated.
- If the answer is NOT found in the context, reply EXACTLY:
  "This issue is not present in the current L1 knowledge base. Please escalate."

RESPONSE FORMAT (MANDATORY):
- Use clear bullet points
- Professional L1 support tone
- Include sections ONLY if present in context:
  • Issue Summary
  • Likely Cause
  • Resolution Steps
  • Escalation Criteria

CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=RAG_SYSTEM_PROMPT,
)

logger.info("Custom RAG prompt loaded")

# ==========================================================
# RETRIEVAL QA CHAIN
# ==========================================================
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": prompt},
)

logger.info("RetrievalQA chain created")

# ==========================================================
# LANGGRAPH STATE
# ==========================================================
class MessagesState(Dict):
    messages: List[dict]

def call_model(state: MessagesState):
    user_message = state["messages"][-1]["content"]
    logger.info("User query received: %s", user_message)

    # ======================================================
    # 🔍 STEP 1: RAW RETRIEVER DEBUG (CORRECT API)
    # ======================================================
    logger.info("Running raw retriever debug check...")

    docs = retriever.invoke(user_message)
    logger.info("Retriever raw docs count: %d", len(docs))

    for i, d in enumerate(docs, start=1):
        logger.info("Raw Doc %d ticket_id=%s", i, d.metadata.get("ticket_id"))
        logger.info("Raw Doc %d text preview: %s", i, d.page_content[:200])

    # ======================================================
    # 🤖 STEP 2: FULL RAG PIPELINE (Retriever + LLM)
    # ======================================================
    logger.info("Invoking RetrievalQA chain...")
    response = qa_chain.invoke({"query": user_message})

    source_docs = response.get("source_documents", [])
    logger.info("Number of documents passed to LLM: %d", len(source_docs))

    for i, doc in enumerate(source_docs, start=1):
        logger.info("LLM Doc %d preview: %s", i, doc.page_content[:200])

    answer = response["result"]
    logger.info("LLM response generated successfully")

    return {
        "messages": [
            {
                "role": "assistant",
                "content": answer
            }
        ]
    }

workflow = StateGraph(state_schema=MessagesState)
workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)

logger.info("LangGraph workflow compiled with memory")

# ==========================================================
# API SCHEMAS
# ==========================================================
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"

class ChatResponse(BaseModel):
    reply: str

# ==========================================================
# API ROUTES
# ==========================================================
@app.get("/")
def root():
    logger.info("Health check endpoint called")
    return {"status": "L1 Support RAG Chatbot is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    logger.info("Chat request received | session_id=%s", req.session_id)

    state = {
        "messages": [
            {"role": "user", "content": req.message}
        ]
    }

    response = app_graph.invoke(
        state,
        config={"configurable": {"thread_id": req.session_id}}
    )

    assistant_reply = response["messages"][-1]["content"]
    logger.info("Response sent to client successfully")

    return ChatResponse(reply=assistant_reply)
