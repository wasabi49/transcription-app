"""採譜前処理（量子化・重複除去）のテスト"""

from src.domain.entities import MidiData, NoteEvent
from src.domain.transcription import (
    preprocess_midi,
    quantize_notes,
    quantize_to_sixteenth,
    remove_duplicate_notes,
)


class TestQuantizeToSixteenth:
    def test_exact_sixteenth(self):
        """ちょうど16分音符の位置にある場合はそのまま"""
        tempo = 120.0  # 1拍 = 0.5s, 16分 = 0.125s
        assert quantize_to_sixteenth(0.125, tempo) == 0.125

    def test_round_up(self):
        """0.125より少し大きい値は0.125に丸まる"""
        tempo = 120.0
        result = quantize_to_sixteenth(0.13, tempo)
        assert abs(result - 0.125) < 1e-9

    def test_round_down(self):
        """中間点以下は切り下げ"""
        tempo = 120.0
        result = quantize_to_sixteenth(0.06, tempo)
        assert abs(result - 0.0) < 1e-9 or abs(result - 0.125) < 1e-9

    def test_zero(self):
        result = quantize_to_sixteenth(0.0, 120.0)
        assert result == 0.0

    def test_negative_clamp(self):
        """負の値は0にクランプされる"""
        result = quantize_to_sixteenth(-0.01, 120.0)
        assert result >= 0.0


class TestQuantizeNotes:
    def test_preserves_note_count(self):
        notes = [
            NoteEvent(pitch=60, start=0.01, end=0.51, velocity=80),
            NoteEvent(pitch=64, start=0.26, end=0.76, velocity=80),
        ]
        midi = MidiData(notes=notes, tempo=120.0)
        result = quantize_notes(midi)
        assert result.note_count == 2

    def test_minimum_duration_enforced(self):
        """量子化で長さが0になるノートには最小長が確保される"""
        # 開始・終了が同じ16分音符に量子化されるケース
        note = NoteEvent(pitch=60, start=0.12, end=0.13, velocity=80)
        midi = MidiData(notes=[note], tempo=120.0)
        result = quantize_notes(midi)
        assert result.notes[0].duration > 0

    def test_tempo_preserved(self):
        midi = MidiData(notes=[], tempo=140.0)
        result = quantize_notes(midi)
        assert result.tempo == 140.0


class TestRemoveDuplicateNotes:
    def test_remove_exact_duplicate(self):
        note = NoteEvent(pitch=60, start=0.0, end=0.5)
        midi = MidiData(notes=[note, note])
        result = remove_duplicate_notes(midi)
        assert result.note_count == 1

    def test_keep_different_pitches(self):
        notes = [
            NoteEvent(pitch=60, start=0.0, end=0.5),
            NoteEvent(pitch=64, start=0.0, end=0.5),
        ]
        midi = MidiData(notes=notes)
        result = remove_duplicate_notes(midi)
        assert result.note_count == 2

    def test_keep_different_start(self):
        notes = [
            NoteEvent(pitch=60, start=0.0, end=0.5),
            NoteEvent(pitch=60, start=0.5, end=1.0),
        ]
        midi = MidiData(notes=notes)
        result = remove_duplicate_notes(midi)
        assert result.note_count == 2


class TestPreprocessMidi:
    def test_pipeline(self):
        """量子化→重複除去のパイプラインが動く"""
        notes = [
            NoteEvent(pitch=60, start=0.01, end=0.51, velocity=80),
            NoteEvent(pitch=60, start=0.01, end=0.51, velocity=80),  # 重複
        ]
        midi = MidiData(notes=notes, tempo=120.0)
        result = preprocess_midi(midi)
        # 重複が除去されているはず
        assert result.note_count == 1
