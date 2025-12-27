import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
load_dotenv()

# -----------------------------
# Load Gemini API key
# -----------------------------
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not set in environment!")

# -----------------------------
# Initialize FastAPI
# -----------------------------
app = FastAPI(title="Customer Support Chatbot API")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Initialize Gemini LLM
# -----------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # make sure this model exists
    api_key=api_key,
    temperature=0.3,
)

# -----------------------------
# In-memory knowledge base
# -----------------------------
knowledge_chunks = []

# -----------------------------
# Request models
# -----------------------------
class Question(BaseModel):
    question: str

# -----------------------------
# Ingest CV + repo link
# -----------------------------
@app.post("/ingest")
async def ingest(
    cv: UploadFile = File(...),
    repo_link: str = Form(None)
):
    """
    Upload CV file and optionally provide a GitHub repo link.
    """
    global knowledge_chunks

    text = (await cv.read()).decode("utf-8", errors="ignore")
    sentences = text.split(".")
    knowledge_chunks = [s.strip() for s in sentences if len(s.strip()) > 20]

    if repo_link:
        knowledge_chunks.append(f"GitHub Repository: {repo_link}")

    return {
        "status": "Knowledge base built",
        "chunks": len(knowledge_chunks)
    }

# -----------------------------
# Ask questions
# -----------------------------
@app.post("/ask")
async def ask(q: Question):
    if not knowledge_chunks:
        return {"answer": "Knowledge base is empty. Upload CV first."}

    # Simple RAG retrieval: pick top 3 matching chunks
    words = q.question.lower().split()
    scored = sorted(
        knowledge_chunks,
        key=lambda c: sum(w in c.lower() for w in words),
        reverse=True
    )
    context = " ".join(scored[:3])

    # Create system + user messages for LLM
    SYSTEM_PROMPT = SystemMessage(
        content=(
            "You are an expert portfolio assistant. "
            "Use the given CV and GitHub repository info to answer the user's question clearly and concisely."
        )
    )
    user_msg = HumanMessage(content=f"Question: {q.question}\n\nContext: {context}")

    response = llm.invoke([SYSTEM_PROMPT, user_msg])

    return {"answer": response.content}
