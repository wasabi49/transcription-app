"""難易度別簡略化のテスト"""

from src.domain.entities import Difficulty, MidiData, NoteEvent
from src.domain.simplification import (
    simplify,
    simplify_advanced,
    simplify_beginner,
    simplify_intermediate,
)


def _make_midi(notes: list[NoteEvent], tempo: float = 120.0) -> MidiData:
    return MidiData(notes=notes, tempo=tempo)


class TestSimplifyAdvanced:
    def test_removes_very_short_notes(self):
        """32分音符以下のノートを除去"""
        tempo = 120.0
        thirty_second = 60.0 / tempo / 8.0  # ≈ 0.0625s

        notes = [
            NoteEvent(pitch=60, start=0.0, end=thirty_second * 0.5),  # 除去対象
            NoteEvent(pitch=64, start=0.0, end=0.5),  # 残る
        ]
        result = simplify_advanced(_make_midi(notes, tempo))
        assert result.note_count == 1
        assert result.notes[0].pitch == 64

    def test_normalizes_velocity(self):
        """極端なベロシティを正規化"""
        notes = [
            NoteEvent(pitch=60, start=0.0, end=0.5, velocity=10),
            NoteEvent(pitch=64, start=0.0, end=0.5, velocity=127),
        ]
        result = simplify_advanced(_make_midi(notes))
        assert result.notes[0].velocity >= 30
        assert result.notes[1].velocity <= 110


class TestSimplifyIntermediate:
    def test_limits_polyphony_to_4(self):
        """同時発音数が4以下に制限される"""
        notes = [NoteEvent(pitch=60 + i, start=0.0, end=1.0) for i in range(6)]
        result = simplify_intermediate(_make_midi(notes))
        # 同時発音数が4以下
        active_at_zero = [n for n in result.notes if n.start <= 0.0 < n.end]
        assert len(active_at_zero) <= 4

    def test_octave_range_c2_c7(self):
        """オクターブ範囲がC2-C7に制限される"""
        notes = [
            NoteEvent(pitch=20, start=0.0, end=0.5),  # C2未満 → 除去
            NoteEvent(pitch=60, start=0.0, end=0.5),  # 範囲内
            NoteEvent(pitch=100, start=0.0, end=0.5),  # C7超 → 除去
        ]
        result = simplify_intermediate(_make_midi(notes))
        for n in result.notes:
            assert 36 <= n.pitch <= 96


class TestSimplifyBeginner:
    def test_max_2_voices(self):
        """同時発音数が2以下"""
        notes = [NoteEvent(pitch=48 + i * 4, start=0.0, end=1.0) for i in range(5)]
        result = simplify_beginner(_make_midi(notes))
        active_at_zero = [n for n in result.notes if n.start <= 0.0 < n.end]
        assert len(active_at_zero) <= 2

    def test_octave_range_c3_c6(self):
        """オクターブ範囲がC3-C6に制限される"""
        notes = [
            NoteEvent(pitch=40, start=0.0, end=0.5),  # C3未満
            NoteEvent(pitch=60, start=0.0, end=0.5),  # 範囲内
            NoteEvent(pitch=90, start=0.0, end=0.5),  # C6超
        ]
        result = simplify_beginner(_make_midi(notes))
        for n in result.notes:
            assert 48 <= n.pitch <= 84

    def test_keeps_melody_and_bass(self):
        """メロディ（最高音）とベース（最低音）を保持"""
        notes = [
            NoteEvent(pitch=48, start=0.0, end=0.5),  # bass
            NoteEvent(pitch=60, start=0.0, end=0.5),  # middle
            NoteEvent(pitch=72, start=0.0, end=0.5),  # melody
        ]
        result = simplify_beginner(_make_midi(notes))
        pitches = {n.pitch for n in result.notes}
        assert 72 in pitches  # melody
        assert 48 in pitches  # bass


class TestSimplifyDispatcher:
    def test_original_returns_unchanged(self):
        notes = [NoteEvent(pitch=60, start=0.0, end=0.5)]
        midi = _make_midi(notes)
        result = simplify(midi, Difficulty.ORIGINAL)
        assert result.note_count == midi.note_count

    def test_dispatches_correctly(self):
        notes = [NoteEvent(pitch=60, start=0.0, end=0.5)]
        midi = _make_midi(notes)
        for diff in Difficulty:
            result = simplify(midi, diff)
            assert isinstance(result, MidiData)
