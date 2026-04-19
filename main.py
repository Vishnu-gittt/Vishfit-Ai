from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import httpx
import asyncio
from datetime import datetime

app = FastAPI(title="Vishfit AI Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── CONFIG ───────────────────────────────
OLLAMA_URL  = "http://localhost:11434"
MODEL_NAME  = "mistral"

N8N_WEBHOOK = "https://techhackein.app.n8n.cloud/webhook/vishfit"

SYSTEM_PROMPT = """You are VishFit AI, an elite personal fitness coach and nutritionist.

## Your personality
- Energetic, motivating, science-backed
- Always give specific numbers (reps, sets, calories, duration)
- Never give generic advice — always make it actionable

## Response format
1. Direct answer first (1-2 lines)
2. Step-by-step plan with specifics
3. End with one Pro Tip

## Rules
- Never say "I'm just an AI"
- Always use both metric and imperial units
- If user mentions injury, always suggest safe alternatives
- Keep responses under 200 words unless a full plan is requested"""

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    user_name: Optional[str] = "Guest"
    user_goal: Optional[str] = ""
    session_id: Optional[str] = ""

class ChatResponse(BaseModel):
    reply: str

async def send_to_n8n(user_msg: str, ai_reply: str, user_name: str, user_goal: str, session_id: str):
    try:
        payload = {
            "timestamp":    datetime.utcnow().isoformat(),
            "session_id":   session_id,
            "user_name":    user_name,
            "user_goal":    user_goal,
            "user_message": user_msg,
            "ai_reply":     ai_reply,
            "training_sample": {
                "messages": [
                    {"role": "system",    "content": SYSTEM_PROMPT},
                    {"role": "user",      "content": user_msg},
                    {"role": "assistant", "content": ai_reply}
                ]
            }
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(N8N_WEBHOOK, json=payload)
    except Exception as e:
        print(f"[n8n] Data send failed (non-critical): {e}")

@app.get("/")
def root():
    return {"status": "Vishfit AI is running", "model": MODEL_NAME}

@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            models = [m["name"] for m in res.json().get("models", [])]
            return {"ollama": "running", "models": models, "using": MODEL_NAME}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama not reachable: {e}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": request.message})

        payload = {
            "model":      MODEL_NAME,
            "messages":   messages,
            "stream":     False,
            "keep_alive": "10m"
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            response.raise_for_status()

        reply = response.json()["message"]["content"]

        asyncio.create_task(send_to_n8n(
            user_msg   = request.message,
            ai_reply   = reply,
            user_name  = request.user_name,
            user_goal  = request.user_goal,
            session_id = request.session_id
        ))

        return {"reply": reply}

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Ollama not running. Run: ollama serve")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))