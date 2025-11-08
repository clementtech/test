import json
import pytest
from app import app

class DummyResp:
    def __init__(self, data):
        self._data = data
        self.status_code = 200
        self.text = str(data)
    def json(self):
        return self._data

def test_chat_simple(monkeypatch):
    def fake_post(url, json, timeout):
        return DummyResp({"choices": [{"content": "Hello from Gemma"}]})
    monkeypatch.setattr('requests.post', fake_post)
    client = app.test_client()
    rv = client.post('/api/chat', json={'message': 'Hi'})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['assistant'] == 'Hello from Gemma'


def test_chat_messages_array(monkeypatch):
    def fake_post(url, json, timeout):
        # return different shape
        return DummyResp({'text': 'Reply to conversation'})
    monkeypatch.setattr('requests.post', fake_post)
    client = app.test_client()
    rv = client.post('/api/chat', json={'messages': [{'role': 'user', 'content': 'Hi there'}]})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['assistant'] == 'Reply to conversation'


def test_history_and_clear(monkeypatch, tmp_path):
    # fake a gemma response
    def fake_post(url, json, timeout):
        return DummyResp({'text': 'History reply'})
    monkeypatch.setattr('requests.post', fake_post)

    client = app.test_client()

    # ensure clear first
    client.post('/api/clear-history')

    # send a message
    rv = client.post('/api/chat', json={'message': 'Hello history'})
    assert rv.status_code == 200

    # check history contains entries
    rv2 = client.get('/api/history')
    assert rv2.status_code == 200
    data = rv2.get_json()
    hist = data.get('history')
    assert isinstance(hist, list)
    # should have at least one assistant reply
    assert any(h.get('role') == 'assistant' and 'History reply' in h.get('content','') for h in hist)

    # clear history
    rv3 = client.post('/api/clear-history')
    assert rv3.status_code == 200
    rv4 = client.get('/api/history')
    assert rv4.get_json().get('history') == []


def test_homework_system_message(monkeypatch):
    captured = {}
    def fake_post(url, json, timeout):
        # capture the payload for assertion
        captured['payload'] = json
        return DummyResp({'text': 'Homework answer'})

    monkeypatch.setattr('requests.post', fake_post)
    client = app.test_client()

    # send messages as array including a system role
    rv = client.post('/api/chat', json={'messages': [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Solve 2+2 step by step.'}
    ]})
    assert rv.status_code == 200
    assert 'payload' in captured
    payload = captured['payload']
    # the server should have forwarded the messages array to Ollama
    assert isinstance(payload, dict)
    assert 'messages' in payload
    assert any(m.get('role') == 'system' for m in payload['messages'])
