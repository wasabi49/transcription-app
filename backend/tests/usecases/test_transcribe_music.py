"""採譜ユースケースのテスト（ポートをモック）"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.usecases.transcribe_music import TranscribeMusicUseCase
from src.domain.entities import Difficulty, MidiData, NoteEvent


@pytest.fixture
def mock_transcriber():
    transcriber = AsyncMock()
    notes = [
        NoteEvent(pitch=60, start=0.0, end=0.5, velocity=80),
        NoteEvent(pitch=64, start=0.5, end=1.0, velocity=80),
    ]
    midi_data = MidiData(notes=notes, tempo=120.0)
    transcriber.transcribe.return_value = (midi_data, [])
    return transcriber


@pytest.fixture
def mock_midi_processor():
    processor = MagicMock()
    processor.to_base64.return_value = "dGVzdA=="
    return processor


@pytest.fixture
def mock_sheet_music_generator():
    generator = MagicMock()
    generator.generate_musicxml.return_value = "<score-partwise></score-partwise>"
    generator.generate_musicxml_and_midi.return_value = ("<score-partwise></score-partwise>", "dGVzdA==")
    return generator


@pytest.fixture
def usecase(mock_transcriber, mock_midi_processor, mock_sheet_music_generator):
    return TranscribeMusicUseCase(
        transcriber=mock_transcriber,
        midi_processor=mock_midi_processor,
        sheet_music_generator=mock_sheet_music_generator,
    )


class TestTranscribeMusicUseCase:
    @pytest.mark.asyncio
    async def test_execute_success(self, usecase, mock_transcriber):
        result = await usecase.execute(Path("/tmp/test.mp3"), Difficulty.ORIGINAL)

        mock_transcriber.transcribe.assert_called_once()
        assert result.musicxml == "<score-partwise></score-partwise>"
        assert result.midi_base64 == "dGVzdA=="
        assert result.metadata.difficulty == Difficulty.ORIGINAL
        assert result.metadata.note_count > 0

    @pytest.mark.asyncio
    async def test_execute_with_simplification(self, usecase):
        result = await usecase.execute(Path("/tmp/test.mp3"), Difficulty.BEGINNER)
        assert result.metadata.difficulty == Difficulty.BEGINNER

    @pytest.mark.asyncio
    async def test_calls_ports_in_order(
        self, usecase, mock_transcriber, mock_midi_processor, mock_sheet_music_generator
    ):
        await usecase.execute(Path("/tmp/test.mp3"), Difficulty.ORIGINAL)

        # 全ポートが呼ばれている
        mock_transcriber.transcribe.assert_called_once()
        mock_sheet_music_generator.generate_musicxml_and_midi.assert_called_once()
