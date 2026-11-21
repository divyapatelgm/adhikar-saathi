from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_speech_providers():
    response = client.get("/api/speech/providers")
    assert response.status_code == 200
    data = response.json()
    assert "web_speech" in data
    assert "gnani" in data
    assert data["web_speech"]["supported_languages"] == ["en", "hi", "kn"]

def test_stt_endpoint():
    response = client.post("/api/stt", data={"language": "kn"})
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert data["language"] == "kn"

def test_tts_endpoint():
    payload = {"text": "ನಮಸ್ಕಾರ", "language": "kn"}
    response = client.post("/api/tts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "ನಮಸ್ಕಾರ"
    assert data["language"] == "kn"
    assert "provider" in data
