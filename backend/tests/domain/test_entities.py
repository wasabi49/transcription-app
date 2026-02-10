"""ドメインエンティティのテスト"""

from src.domain.entities import Difficulty, MidiData, NoteEvent, TranscriptionMetadata


class TestNoteEvent:
    def test_duration(self):
        note = NoteEvent(pitch=60, start=1.0, end=2.5, velocity=80)
        assert note.duration == 1.5

    def test_frozen(self):
        note = NoteEvent(pitch=60, start=0.0, end=1.0)
        try:
            note.pitch = 61  # type: ignore[misc]
            raise AssertionError("Should raise FrozenInstanceError")
        except AttributeError:
            pass

    def test_default_velocity(self):
        note = NoteEvent(pitch=60, start=0.0, end=1.0)
        assert note.velocity == 100


class TestMidiData:
    def test_duration_with_notes(self):
        notes = [
            NoteEvent(pitch=60, start=0.0, end=1.0),
            NoteEvent(pitch=64, start=0.5, end=3.0),
        ]
        midi = MidiData(notes=notes, tempo=120.0)
        assert midi.duration == 3.0

    def test_duration_empty(self):
        midi = MidiData()
        assert midi.duration == 0.0

    def test_note_count(self):
        notes = [
            NoteEvent(pitch=60, start=0.0, end=1.0),
            NoteEvent(pitch=64, start=0.0, end=1.0),
        ]
        midi = MidiData(notes=notes)
        assert midi.note_count == 2

    def test_defaults(self):
        midi = MidiData()
        assert midi.tempo == 120.0
        assert midi.time_signature_numerator == 4
        assert midi.time_signature_denominator == 4
        assert midi.notes == []


class TestDifficulty:
    def test_values(self):
        assert Difficulty.ORIGINAL.value == "original"
        assert Difficulty.ADVANCED.value == "advanced"
        assert Difficulty.INTERMEDIATE.value == "intermediate"
        assert Difficulty.BEGINNER.value == "beginner"

    def test_from_string(self):
        assert Difficulty("original") == Difficulty.ORIGINAL


class TestTranscriptionMetadata:
    def test_creation(self):
        meta = TranscriptionMetadata(
            duration_seconds=30.0,
            note_count=100,
            tempo=120.0,
            difficulty=Difficulty.ORIGINAL,
        )
        assert meta.duration_seconds == 30.0
        assert meta.note_count == 100
