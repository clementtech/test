from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import json

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
# Default to the model name you reported (gemma3:1b). You can override with OLLAMA_MODEL env var.
MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:1b")

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Configurable limits and admin token
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB limit for requests
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN')

# Simple in-memory chat history with JSON persistence
HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'chat_history.json')
chat_history = []

# Exports directory for saved conversations
EXPORTS_DIR = os.path.join(os.path.dirname(__file__), 'exports')
os.makedirs(EXPORTS_DIR, exist_ok=True)

def load_history():
    global chat_history
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                chat_history = json.load(f)
    except Exception:
        chat_history = []

def save_history():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

load_history()

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route('/api/history', methods=['GET'])
def get_history():
    # If ADMIN_TOKEN is set, require X-ADMIN-TOKEN header to access history
    if ADMIN_TOKEN:
        token = request.headers.get('X-ADMIN-TOKEN')
        if not token or token != ADMIN_TOKEN:
            return jsonify({'error': 'unauthorized'}), 401
    return jsonify({'history': chat_history})


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    global chat_history
    if ADMIN_TOKEN:
        token = request.headers.get('X-ADMIN-TOKEN')
        if not token or token != ADMIN_TOKEN:
            return jsonify({'error': 'unauthorized'}), 401
    chat_history = []
    save_history()
    return jsonify({'ok': True})


def _safe_filename(name: str) -> str:
    # keep only safe chars
    import re
    base = re.sub(r'[^A-Za-z0-9_.-]', '_', name or 'conversation')
    return base


@app.route('/api/save-conversation', methods=['POST'])
def save_conversation():
    '''Save a conversation (array of {role, content}) to a text file in exports/ and return its URL.'''
    data = request.get_json() or {}
    conv = data.get('conversation')
    filename = data.get('filename')
    if ADMIN_TOKEN:
        token = request.headers.get('X-ADMIN-TOKEN')
        if not token or token != ADMIN_TOKEN:
            return jsonify({'error': 'unauthorized'}), 401

    if not conv or not isinstance(conv, list):
        return jsonify({'error': 'invalid_conversation'}), 400

    # build text content
    lines = []
    for m in conv:
        role = m.get('role', 'user')
        content = m.get('content', '')
        prefix = 'User' if role == 'user' else 'Assistant'
        lines.append(f"{prefix}: {content}")

    text = '\n'.join(lines)

    # sanitize filename and append timestamp
    import time
    safe = _safe_filename(filename) if filename else 'conversation'
    ts = int(time.time())
    fname = f"{safe}-{ts}.txt"
    path = os.path.join(EXPORTS_DIR, fname)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        return jsonify({'error': 'write_failed', 'details': str(e)}), 500

    # return a relative URL to download
    return jsonify({'ok': True, 'url': f'/exports/{fname}'})


@app.route('/exports/<path:filename>', methods=['GET'])
def serve_export(filename):
    # serve a file from exports directory; protect with ADMIN_TOKEN if set
    if ADMIN_TOKEN:
        token = request.headers.get('X-ADMIN-TOKEN')
        if not token or token != ADMIN_TOKEN:
            return jsonify({'error': 'unauthorized'}), 401
    # ensure filename is safe (no path traversal)
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': 'invalid_filename'}), 400
    return send_from_directory(EXPORTS_DIR, filename, as_attachment=True)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    # Accept either a single message or a messages list
    messages = data.get("messages")
    if messages is None:
        msg = data.get("message") or ""
        messages = [{"role": "user", "content": msg}]
    # Allow per-request model override (falls back to configured MODEL)
    model_name = data.get("model") or MODEL

    # Prepare multiple payload shapes to try in case the local Ollama API expects a different format
    # 1) messages (chat-style)
    # 2) prompt (single string)
    # 3) input (some APIs use 'input')
    # 4) text
    user_text = "\n".join([m.get("content", "") for m in messages if m.get("role") == "user"]) or (messages[-1].get("content") if messages else "")

    payloads = [
        {"model": model_name, "messages": messages},
        {"model": model_name, "prompt": user_text},
        {"model": model_name, "input": user_text},
        {"model": model_name, "text": user_text},
    ]

    raw_responses = []

    def extract_assistant_text(parsed):
        if not isinstance(parsed, dict):
            return None
        # Try common keys
        choices = parsed.get("choices") or parsed.get("generations")
        if choices and isinstance(choices, list) and len(choices) > 0:
            first = choices[0]
            if isinstance(first, dict):
                return (
                    first.get("content")
                    or first.get("text")
                    or (first.get("message") or {}).get("content")
                    or first.get("response")
                )
        return parsed.get("text") or parsed.get("output") or parsed.get("response")

    for payload in payloads:
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
        except requests.RequestException as e:
            # on connection failure, return error immediately
            return jsonify({"error": "Failed to connect to Ollama", "details": str(e)}), 502

        # attempt to parse JSON, but capture text if parsing fails
        parsed = None
        try:
            parsed = resp.json()
        except ValueError:
            parsed = None

        # capture raw text (may contain NDJSON streaming lines)
        body_text = getattr(resp, 'text', None)

        # Try to aggregate NDJSON/streaming 'response' parts from body_text
        ndjson_agg = None
        if body_text:
            parts = []
            for ln in body_text.splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                except Exception:
                    continue
                if isinstance(obj, dict) and 'response' in obj:
                    parts.append(obj.get('response') or '')
            if parts:
                ndjson_agg = ''.join(parts)

        # Save raw response info to help debugging
        raw_responses.append({"payload": payload, "status_code": getattr(resp, 'status_code', None), "body": parsed if parsed is not None else body_text})

        assistant_text = extract_assistant_text(parsed) if parsed is not None else None
        # if no assistant_text, but we found NDJSON streaming chunks, use them
        if not assistant_text and ndjson_agg:
            assistant_text = ndjson_agg
        # If Ollama reports a missing model (HTTP 404 with an error message), return a clear error
        try:
            status = getattr(resp, 'status_code', None)
            if status == 404 and isinstance(parsed, dict):
                err = parsed.get('error') or parsed.get('message') or ''
                if 'not found' in str(err).lower() and 'model' in str(err).lower():
                    model_name = payload.get('model')
                    return jsonify({
                        "error": "model_not_found",
                        "message": f"Model '{model_name}' not found on Ollama.",
                        "help": "Run 'ollama list' to see installed models and 'ollama pull <model>' to install one locally.",
                        "example_install": f"ollama pull {model_name}",
                        "raw_response": parsed
                    }), 404
        except Exception:
            pass
        if assistant_text:
            # record to history: last user message(s) and assistant reply
            try:
                # append each user message as separate entries and then assistant
                for m in messages:
                    if m.get('role') == 'user':
                        chat_history.append({'role': 'user', 'content': m.get('content')})
                chat_history.append({'role': 'assistant', 'content': assistant_text})
                save_history()
            except Exception:
                pass
            return jsonify({"assistant": assistant_text})

    # No assistant text found in any payload attempt — return raw responses for debugging
    return jsonify({"assistant": "", "raw_response": raw_responses}), 200

if __name__ == "__main__":
    # Run with: set OLLAMA_URL and OLLAMA_MODEL if needed, then: python app.py
    app.run(host="127.0.0.1", port=5000, debug=True)
