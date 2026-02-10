"""API エンドポイントの統合テスト"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.domain.entities import (
    Difficulty,
    TranscriptionMetadata,
    TranscriptionResult,
)


@pytest.fixture(autouse=True)
def _setup_semaphore():
    """テスト用にセマフォを設定"""
    import main as main_module

    main_module.transcription_semaphore = asyncio.Semaphore(1)
    yield
    main_module.transcription_semaphore = None


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """テストごとにレート制限をリセット"""
    from src.api.router import limiter

    limiter.reset()
    yield


@pytest.fixture
def mock_transcribe_usecase():
    usecase = AsyncMock()
    result = TranscriptionResult(
        musicxml="<score/>",
        midi_base64="dGVzdA==",
        metadata=TranscriptionMetadata(
            duration_seconds=10.0,
            note_count=50,
            tempo=120.0,
            difficulty=Difficulty.ORIGINAL,
        ),
    )
    usecase.execute.return_value = result
    return usecase


@pytest.fixture
def mock_simplify_usecase():
    usecase = MagicMock()
    result = TranscriptionResult(
        musicxml="<score/>",
        midi_base64="bmV3",
        metadata=TranscriptionMetadata(
            duration_seconds=10.0,
            note_count=30,
            tempo=120.0,
            difficulty=Difficulty.BEGINNER,
        ),
    )
    usecase.execute.return_value = result
    return usecase


@pytest.fixture
def client(mock_transcribe_usecase, mock_simplify_usecase):
    from main import app
    from src.api.dependencies import get_simplify_usecase, get_transcribe_usecase

    app.dependency_overrides[get_transcribe_usecase] = lambda: mock_transcribe_usecase
    app.dependency_overrides[get_simplify_usecase] = lambda: mock_simplify_usecase

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestTranscribeEndpoint:
    def test_rejects_no_file(self, client):
        resp = client.post("/api/transcribe")
        assert resp.status_code == 422  # Validation error

    def test_rejects_invalid_extension(self, client):
        resp = client.post(
            "/api/transcribe",
            files={"file": ("test.txt", b"hello", "text/plain")},
            data={"difficulty": "original"},
        )
        assert resp.status_code == 400

    def test_rejects_empty_file(self, client):
        resp = client.post(
            "/api/transcribe",
            files={"file": ("test.mp3", b"", "audio/mpeg")},
            data={"difficulty": "original"},
        )
        assert resp.status_code == 400

    def test_rejects_invalid_magic_bytes(self, client):
        resp = client.post(
            "/api/transcribe",
            files={"file": ("test.mp3", b"\x00\x00\x00\x00", "audio/mpeg")},
            data={"difficulty": "original"},
        )
        assert resp.status_code == 400

    def test_accepts_mp3_with_id3(self, client):
        # ID3タグで始まるMP3ファイル
        content = b"ID3" + b"\x00" * 100
        resp = client.post(
            "/api/transcribe",
            files={"file": ("test.mp3", content, "audio/mpeg")},
            data={"difficulty": "original"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

    def test_accepts_wav(self, client):
        content = b"RIFF" + b"\x00" * 100
        resp = client.post(
            "/api/transcribe",
            files={"file": ("test.wav", content, "audio/wav")},
            data={"difficulty": "original"},
        )
        assert resp.status_code == 200

    def test_sse_contains_complete_event(self, client):
        content = b"ID3" + b"\x00" * 100
        resp = client.post(
            "/api/transcribe",
            files={"file": ("test.mp3", content, "audio/mpeg")},
            data={"difficulty": "original"},
        )
        body = resp.text
        assert "event: complete" in body
        assert "event: progress" in body


class TestSimplifyEndpoint:
    def test_simplify_success(self, client):
        resp = client.post(
            "/api/simplify",
            json={"midi_base64": "dGVzdA==", "difficulty": "beginner"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "musicxml" in data
        assert "midi_base64" in data
        assert data["metadata"]["difficulty"] == "beginner"

    def test_simplify_invalid_difficulty(self, client):
        resp = client.post(
            "/api/simplify",
            json={"midi_base64": "dGVzdA==", "difficulty": "invalid"},
        )
        assert resp.status_code == 422
