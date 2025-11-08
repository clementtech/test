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
- This project is intentionally minimal; for production, add authentication, rate-limiting, streaming, and safety checks

## Security & Privacy

- Admin token: you can protect history and exported files by setting an environment variable `ADMIN_TOKEN` to a secret string. When set, the endpoints `/api/history`, `/api/clear-history`, `/api/save-conversation` and `/exports/<filename>` require the `X-ADMIN-TOKEN` header with the same value.

- Disable persistent history: to avoid writing conversation history to disk, you can extend the app to respect `DISABLE_PERSIST_HISTORY=true` and avoid saving `chat_history.json`.

- HTTPS: when deploying, run behind HTTPS (nginx/Cloud provider) so traffic is encrypted.

- Content-Security-Policy and other secure headers should be added in production (Talisman or custom headers in Flask).
