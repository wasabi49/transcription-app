"""採譜のビジネスルール（純粋ロジック、外部依存なし）

Basic Pitchの出力をドメインエンティティに変換する際の
共通前処理（量子化等）を定義する。
"""

from src.domain.entities import MidiData, NoteEvent


def quantize_to_sixteenth(time: float, tempo: float) -> float:
    """時刻を最近接の16分音符に量子化する

    Args:
        time: 量子化対象の時刻（秒）
        tempo: テンポ（BPM）

    Returns:
        量子化後の時刻（秒）
    """
    # 1拍の長さ（秒）
    beat_duration = 60.0 / tempo
    # 16分音符の長さ（秒）
    sixteenth_duration = beat_duration / 4.0

    # 最近接の16分音符に丸める
    quantized = round(time / sixteenth_duration) * sixteenth_duration
    return max(0.0, quantized)


def quantize_notes(midi_data: MidiData) -> MidiData:
    """全ノートのonset/offsetを最近接の16分音符に量子化する

    全難易度共通の前処理。Basic Pitchの浮動小数点時刻を
    記譜に適した離散的な時刻に変換する。

    Args:
        midi_data: 量子化前のMIDIデータ

    Returns:
        量子化後のMIDIデータ
    """
    quantized_notes: list[NoteEvent] = []

    for note in midi_data.notes:
        q_start = quantize_to_sixteenth(note.start, midi_data.tempo)
        q_end = quantize_to_sixteenth(note.end, midi_data.tempo)

        # 量子化後に長さが0になるノートは最小長（16分音符）を確保
        sixteenth_duration = 60.0 / midi_data.tempo / 4.0
        if q_end <= q_start:
            q_end = q_start + sixteenth_duration

        quantized_notes.append(
            NoteEvent(
                pitch=note.pitch,
                start=q_start,
                end=q_end,
                velocity=note.velocity,
            )
        )

    return MidiData(
        notes=quantized_notes,
        tempo=midi_data.tempo,
        time_signature_numerator=midi_data.time_signature_numerator,
        time_signature_denominator=midi_data.time_signature_denominator,
    )


def remove_duplicate_notes(midi_data: MidiData) -> MidiData:
    """量子化後に重複したノートを除去する

    同じピッチ・同じタイミングのノートが量子化によって
    生じた場合に1つにまとめる。

    Args:
        midi_data: 重複除去前のMIDIデータ

    Returns:
        重複除去後のMIDIデータ
    """
    seen: set[tuple[int, float, float]] = set()
    unique_notes: list[NoteEvent] = []

    for note in midi_data.notes:
        key = (note.pitch, round(note.start, 6), round(note.end, 6))
        if key not in seen:
            seen.add(key)
            unique_notes.append(note)

    return MidiData(
        notes=unique_notes,
        tempo=midi_data.tempo,
        time_signature_numerator=midi_data.time_signature_numerator,
        time_signature_denominator=midi_data.time_signature_denominator,
    )


def preprocess_midi(midi_data: MidiData) -> MidiData:
    """採譜結果の共通前処理パイプライン

    1. 16分音符への量子化
    2. 重複ノート除去

    Args:
        midi_data: 前処理前のMIDIデータ

    Returns:
        前処理後のMIDIデータ
    """
    result = quantize_notes(midi_data)
    result = remove_duplicate_notes(result)
    return result
