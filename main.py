import os
from fastapi import FastAPI
from typing import List, Dict
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.chains import RetrievalQA
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

# ---------------------- ENV & CONFIG ----------------------
load_dotenv()

# ---------------------- FASTAPI ---------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------- PINECONE SETUP --------------------
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.environ["OPENAI_API_KEY"]
)

# LangChain automatically reads PINECONE_API_KEY from env
index_name = os.environ["PINECONE_INDEX_NAME"]

# Connect to existing Pinecone index
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embedding_model,
)

# Retriever setup
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# ---------- LLM + RETRIEVAL QA ----------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.5,
    api_key=os.environ["OPENAI_API_KEY"]
)

# Chain that retrieves context from Pinecone before answering
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=False
)

# ---------- LANGGRAPH WRAPPER ----------
class MessagesState(Dict):
    messages: List[dict]

def call_model(state: MessagesState):
    user_message = state["messages"][-1]["content"]
    response = qa_chain.invoke({"query": user_message})
    return {"messages": [{"role": "assistant", "content": response["result"]}]}

workflow = StateGraph(state_schema=MessagesState)
workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)

# ---------- FASTAPI ROUTES ----------
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"

class ChatResponse(BaseModel):
    reply: str

@app.get("/")
def read_root():
    return {"message": "Hello, I am your Pinecone-powered Agent!"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    state = {"messages": [{"role": "user", "content": req.message}]}
    response = app_graph.invoke(state, config={"configurable": {"thread_id": req.session_id}})
    assistant_reply = response["messages"][-1]["content"]
    return ChatResponse(reply=assistant_reply)
