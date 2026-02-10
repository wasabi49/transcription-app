"""難易度別簡略化のビジネスルール（純粋ロジック、外部依存なし）

各難易度に応じてMIDIデータを簡略化するルールを定義する。
"""

from src.domain.entities import Difficulty, MidiData, NoteEvent


def simplify_advanced(midi_data: MidiData) -> MidiData:
    """上級: 微細な装飾音・超短音符の除去、ベロシティ正規化

    - 32分音符以下（16分音符の半分未満）のノートを除去
    - 極端なベロシティ（20未満, 120超）を正規化
    """
    # 32分音符の長さ（秒）
    thirty_second = 60.0 / midi_data.tempo / 8.0

    filtered_notes: list[NoteEvent] = []
    for note in midi_data.notes:
        # 32分音符以下は除去
        if note.duration < thirty_second * 0.9:  # 少し余裕を持たせる
            continue

        # ベロシティ正規化
        velocity = note.velocity
        velocity = max(30, min(110, velocity))

        filtered_notes.append(
            NoteEvent(
                pitch=note.pitch,
                start=note.start,
                end=note.end,
                velocity=velocity,
            )
        )

    return MidiData(
        notes=filtered_notes,
        tempo=midi_data.tempo,
        time_signature_numerator=midi_data.time_signature_numerator,
        time_signature_denominator=midi_data.time_signature_denominator,
    )


def simplify_intermediate(midi_data: MidiData) -> MidiData:
    """中級: 同時発音数制限、速いパッセージの間引き、オクターブ範囲制限

    - 上級の簡略化を適用した上で追加処理
    - 同時発音数を最大4音に制限（高い音を優先）
    - オクターブ範囲を C2-C7 (36-96) に制限
    """
    # まず上級の簡略化を適用
    data = simplify_advanced(midi_data)

    # オクターブ範囲制限 (C2=36 ~ C7=96)
    range_filtered = [note for note in data.notes if 36 <= note.pitch <= 96]

    # 同時発音数を4音に制限
    # 時間順にソートして、各タイムスタンプで4音以下にする
    limited_notes = _limit_polyphony(range_filtered, max_voices=4)

    return MidiData(
        notes=limited_notes,
        tempo=data.tempo,
        time_signature_numerator=data.time_signature_numerator,
        time_signature_denominator=data.time_signature_denominator,
    )


def simplify_beginner(midi_data: MidiData) -> MidiData:
    """初級: メロディ＋ルート音のみ、同時発音2音以下

    - メロディ（最高音）とルート音（最低音）のみ抽出
    - 同時発音数を2音以下に制限
    - オクターブ範囲を C3-C6 (48-84) に制限
    """
    # まず上級の簡略化を適用
    data = simplify_advanced(midi_data)

    # オクターブ範囲制限 (C3=48 ~ C6=84)
    range_filtered = [note for note in data.notes if 48 <= note.pitch <= 84]

    # 各タイムスタンプで最高音（メロディ）と最低音（ルート）のみ
    melody_bass_notes = _extract_melody_and_bass(range_filtered)

    return MidiData(
        notes=melody_bass_notes,
        tempo=data.tempo,
        time_signature_numerator=data.time_signature_numerator,
        time_signature_denominator=data.time_signature_denominator,
    )


def _limit_polyphony(notes: list[NoteEvent], max_voices: int) -> list[NoteEvent]:
    """同時発音数を制限する

    各時点で鳴っている音が max_voices を超える場合、
    高い音を優先して残す（メロディを保持するため）。

    Args:
        notes: ノートリスト
        max_voices: 最大同時発音数

    Returns:
        制限後のノートリスト
    """
    if not notes:
        return []

    # 開始時刻でソート
    sorted_notes = sorted(notes, key=lambda n: (n.start, -n.pitch))

    # 各ノートについて、開始時点での同時発音を確認
    result: list[NoteEvent] = []
    for note in sorted_notes:
        # 現時点で鳴っているノート数をカウント
        active = sum(1 for n in result if n.start <= note.start < n.end)
        if active < max_voices:
            result.append(note)

    return result


def _extract_melody_and_bass(notes: list[NoteEvent]) -> list[NoteEvent]:
    """各タイムスロットでメロディ（最高音）とベース（最低音）を抽出する

    Args:
        notes: ノートリスト

    Returns:
        メロディ＋ベースのノートリスト
    """
    if not notes:
        return []

    # 開始時刻でグルーピング（16分音符分の許容範囲でグルーピング）
    sorted_notes = sorted(notes, key=lambda n: n.start)
    result: list[NoteEvent] = []

    # 近いonset同士をグルーピング（0.05秒以内は同時と見なす）
    groups: list[list[NoteEvent]] = []
    current_group: list[NoteEvent] = [sorted_notes[0]]

    for note in sorted_notes[1:]:
        if note.start - current_group[0].start < 0.05:
            current_group.append(note)
        else:
            groups.append(current_group)
            current_group = [note]
    groups.append(current_group)

    for group in groups:
        if len(group) == 1:
            result.append(group[0])
        else:
            # 最高音（メロディ）
            melody = max(group, key=lambda n: n.pitch)
            # 最低音（ベース）
            bass = min(group, key=lambda n: n.pitch)
            result.append(melody)
            if bass.pitch != melody.pitch:
                result.append(bass)

    return result


def simplify(midi_data: MidiData, difficulty: Difficulty) -> MidiData:
    """難易度に応じてMIDIデータを簡略化する

    Args:
        midi_data: 前処理済みのMIDIデータ
        difficulty: 目標の難易度

    Returns:
        簡略化後のMIDIデータ
    """
    match difficulty:
        case Difficulty.ORIGINAL:
            return midi_data
        case Difficulty.ADVANCED:
            return simplify_advanced(midi_data)
        case Difficulty.INTERMEDIATE:
            return simplify_intermediate(midi_data)
        case Difficulty.BEGINNER:
            return simplify_beginner(midi_data)
