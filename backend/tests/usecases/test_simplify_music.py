"""簡略化ユースケースのテスト（ポートをモック）"""

from unittest.mock import MagicMock

from src.application.usecases.simplify_music import SimplifyMusicUseCase
from src.domain.entities import Difficulty, MidiData, NoteEvent


def _make_mock_processor():
    processor = MagicMock()
    notes = [
        NoteEvent(pitch=60, start=0.0, end=0.5, velocity=80),
        NoteEvent(pitch=64, start=0.5, end=1.0, velocity=80),
        NoteEvent(pitch=67, start=0.0, end=1.0, velocity=80),
    ]
    midi_data = MidiData(notes=notes, tempo=120.0)
    processor.from_base64.return_value = midi_data
    processor.to_base64.return_value = "bmV3X21pZGk="
    return processor


class TestSimplifyMusicUseCase:
    def test_execute_original(self):
        processor = _make_mock_processor()
        generator = MagicMock()
        generator.generate_musicxml_and_midi.return_value = ("<xml/>", "bmV3X21pZGk=")

        usecase = SimplifyMusicUseCase(
            midi_processor=processor,
            sheet_music_generator=generator,
        )
        result = usecase.execute("dGVzdA==", Difficulty.ORIGINAL)

        processor.from_base64.assert_called_once_with("dGVzdA==")
        assert result.musicxml == "<xml/>"
        assert result.metadata.difficulty == Difficulty.ORIGINAL

    def test_execute_beginner(self):
        processor = _make_mock_processor()
        generator = MagicMock()
        generator.generate_musicxml_and_midi.return_value = ("<xml/>", "bmV3X21pZGk=")

        usecase = SimplifyMusicUseCase(
            midi_processor=processor,
            sheet_music_generator=generator,
        )
        result = usecase.execute("dGVzdA==", Difficulty.BEGINNER)

        assert result.metadata.difficulty == Difficulty.BEGINNER
        # 初級は簡略化されるのでノート数が減る可能性がある
        assert result.metadata.note_count >= 0
