import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile

from backend.app.main import app
from backend.app.models.api import ChatRequest
from backend.app.services.chat_service import ChatService
from backend.app.services.cache_service import ResponseCacheService
from backend.app.services.retrieval_service import RetrievalService

client = TestClient(app)

@pytest.fixture
def chat_service_fixture():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        cache_db = Path(tmp) / "test_chat_cache.db"
        cache = ResponseCacheService(db_path=cache_db)
        retrieval = RetrievalService()
        svc = ChatService(retrieval=retrieval, cache=cache)
        yield svc

@pytest.mark.asyncio
async def test_chat_rights_query(chat_service_fixture):
    req = ChatRequest(message="I did not get paid for my NREGA work", language="en")
    res = await chat_service_fixture.handle_chat(req)

    assert res.is_link_out is False
    assert "MGNREGA" in res.reply_text
    assert len(res.sources) >= 1
    assert "Rural Employment Guarantee Act" in res.sources[0].source_name
    assert "Information only, not legal advice" in res.disclaimer

@pytest.mark.asyncio
async def test_chat_rights_query_kannada(chat_service_fixture):
    req = ChatRequest(message="ವೇತನ ಬಂದಿಲ್ಲ ನರೇಗಾ", language="kn")
    res = await chat_service_fixture.handle_chat(req)

    assert res.is_link_out is False
    assert res.language == "kn"
    assert "ವಿಷಯ" in res.reply_text
    assert "ಕ್ರಮಗಳು" in res.reply_text

@pytest.mark.asyncio
async def test_chat_scheme_query(chat_service_fixture):
    req = ChatRequest(message="Tell me about the synthetic dairy farmer grant", language="en")
    res = await chat_service_fixture.handle_chat(req)

    assert res.is_link_out is False
    assert "Dairy Farmer" in res.reply_text
    assert len(res.sources) >= 1
    assert "Department of Synthetic Welfare" in res.sources[0].source_name

@pytest.mark.asyncio
async def test_chat_tier3_linkout_hallucination_trap(chat_service_fixture):
    # Completely non-existent scheme query
    req = ChatRequest(message="How to claim free gold biscuits from space scheme", language="en")
    res = await chat_service_fixture.handle_chat(req)

    assert res.is_link_out is True
    assert "sevasindhu" in res.sources[0].official_url or "myscheme" in res.sources[0].official_url
    assert "Information only, not legal advice" in res.disclaimer

@pytest.mark.asyncio
async def test_chat_sqlite_response_cache(chat_service_fixture):
    req = ChatRequest(message="How to file RTI application?", language="en")

    # First call: computed and cached
    res1 = await chat_service_fixture.handle_chat(req)

    # Second call: served directly from cache
    res2 = await chat_service_fixture.handle_chat(req)

    assert res1.reply_text == res2.reply_text
    assert res1.sources[0].official_url == res2.sources[0].official_url

def test_api_chat_endpoint():
    payload = {
        "message": "Fair price shop dealer is not giving ration",
        "language": "en"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply_text" in data
    assert "sources" in data
    assert len(data["sources"]) >= 1
    assert "disclaimer" in data
