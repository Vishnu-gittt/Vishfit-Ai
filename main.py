from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import httpx

# ─────────────────────────────────────────
#  VISHFIT AI — FastAPI + Ollama + Mistral
# ─────────────────────────────────────────

app = FastAPI(title="Vishfit AI Chatbot")

# Allow frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend HTML file
app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── Ollama Config ────────────────────────
OLLAMA_URL  = "http://localhost:11434"
MODEL_NAME  = "mistral"

SYSTEM_PROMPT = """You are Vishfit AI, an expert personal fitness coach and nutritionist.
Your personality is energetic, motivating, and knowledgeable.
Give practical, safe, and science-backed advice on:
- Workouts and exercise plans
- Nutrition and diet
- Weight loss and muscle building
- Healthy lifestyle habits
Keep responses concise, clear, and actionable.
Always motivate and encourage the user."""

# ─── Request / Response Models ────────────
class Message(BaseModel):
    role: str      # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []   # full conversation history

class ChatResponse(BaseModel):
    reply: str

# ─── Health Check ─────────────────────────
@app.get("/")
def root():
    return {"status": "Vishfit AI is running 💪", "model": MODEL_NAME}

# ─── Check if Ollama is alive ─────────────
@app.get("/health")
async def health_check():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            models = res.json().get("models", [])
            model_names = [m["name"] for m in models]
            return {
                "ollama": "running",
                "available_models": model_names,
                "using": MODEL_NAME
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama not reachable: {e}")

# ─── Main Chat Endpoint ───────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Build message list: system + history + new user message
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add the new user message
        messages.append({"role": "user", "content": request.message})

        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload
            )
            response.raise_for_status()

        data  = response.json()
        reply = data["message"]["content"]
        return {"reply": reply}

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Run: ollama serve"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")