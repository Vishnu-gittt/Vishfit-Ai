# Vishfit AI Chatbot
## FastAPI + Ollama + Mistral (100% Free, Runs Locally)

---

## Project Structure

```
vishfit-ai/
├── main.py              ← FastAPI backend (Python)
├── requirements.txt     ← Python dependencies
├── static/
│   └── index.html       ← Frontend chatbot UI
└── README.md
```

---

## Setup Steps (Run Once)

### 1. Install Ollama
Download from: https://ollama.com/download

### 2. Pull Mistral Model
```bash
ollama pull mistral
```

### 3. Create Virtual Environment in VS Code
```bash
python -m venv venv
```

Activate it:
- Windows:  `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Run the Project

### Terminal 1 — Start Ollama
```bash
ollama serve
```

### Terminal 2 — Start FastAPI
```bash
uvicorn main:app --reload
```

---

## Open in Browser

```
http://localhost:8000/static/index.html
```

Or test the API directly:
```
http://localhost:8000/docs    ← Swagger UI
http://localhost:8000/health  ← Check Ollama status
```

---

## API Endpoints

| Method | Endpoint  | Description          |
|--------|-----------|----------------------|
| GET    | /         | Health check         |
| GET    | /health   | Check Ollama models  |
| POST   | /chat     | Send a chat message  |

### Example API Call
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Give me a chest workout plan", "history": []}'
```

---

## Change the AI Model

In `main.py`, change this line:
```python
MODEL_NAME = "mistral"   # Change to: llama3, gemma, phi3, etc.
```

Then pull the new model:
```bash
ollama pull llama3
```