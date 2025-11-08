# Ollama Gemma Chat (Flask)

This is a minimal local chat example that proxies messages to a locally running Ollama model (Gemma).

Prerequisites

- Ollama installed and running locally (default API: http://localhost:11434)
- Python 3.10+ recommended

Setup (PowerShell)

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run

```powershell
# if Ollama is running at a non-default URL:
# $env:OLLAMA_URL = 'http://127.0.0.1:11434/api/generate'
# $env:OLLAMA_MODEL = 'gemma'
python app.py
```

Open http://127.0.0.1:5000 in your browser.

Notes

- The backend posts JSON to the Ollama `/api/generate` endpoint. Adjust `OLLAMA_URL` or `OLLAMA_MODEL` via environment variables if needed.
- This project is intentionally minimal; for production, add authentication, rate-limiting, streaming, and safety checks.



https://rewards.bing.com/welcome?rh=6F7344F&ref=rafsrchae
