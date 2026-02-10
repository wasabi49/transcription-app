"""music21 による SheetMusicGenerator ポートの実装

MIDIデータ（内部表現）から MusicXML 文字列を生成する。
"""

import logging

import music21

from src.application.ports.sheet_music_generator import SheetMusicGeneratorPort
from src.domain.entities import MidiData

logger = logging.getLogger(__name__)


class Music21Generator(SheetMusicGeneratorPort):
    """music21 を使った MusicXML 生成"""

    def generate_musicxml(self, midi_data: MidiData) -> str:
        """MIDIデータから MusicXML を生成する"""
        score = music21.stream.Score()

        # メタデータ
        score.insert(0, music21.metadata.Metadata())
        score.metadata.title = "Transcription"

        # テンポ設定
        tempo_mark = music21.tempo.MetronomeMark(number=midi_data.tempo)
        score.insert(0, tempo_mark)

        # 拍子記号
        ts = music21.meter.TimeSignature(
            f"{midi_data.time_signature_numerator}/{midi_data.time_signature_denominator}"
        )
        score.insert(0, ts)

        # ノートを右手・左手に分割（ミドルC=60を基準）
        right_hand_notes = [n for n in midi_data.notes if n.pitch >= 60]
        left_hand_notes = [n for n in midi_data.notes if n.pitch < 60]

        # 右手パート（高音部記号）
        right_part = self._create_part(right_hand_notes, midi_data.tempo, "Right Hand", "treble")
        score.insert(0, right_part)

        # 左手パート（低音部記号）
        left_part = self._create_part(left_hand_notes, midi_data.tempo, "Left Hand", "bass")
        score.insert(0, left_part)

        # MusicXML に変換
        musicxml_str = score.write("musicxml").read_text()

        logger.info("MusicXML 生成完了: %d バイト", len(musicxml_str))
        return musicxml_str

    def _create_part(
        self,
        notes: list,
        tempo: float,
        part_name: str,
        clef_type: str,
    ) -> music21.stream.Part:
        """パート（右手 or 左手）を作成する"""
        part = music21.stream.Part()
        part.partName = part_name

        # 音部記号設定
        if clef_type == "treble":
            part.insert(0, music21.clef.TrebleClef())
        else:
            part.insert(0, music21.clef.BassClef())

        if not notes:
            # 空パートには全休符を入れる
            rest = music21.note.Rest(quarterLength=4.0)
            part.append(rest)
            return part

        # 1拍の長さ（秒）
        beat_duration = 60.0 / tempo

        for note_event in notes:
            # 長さを四分音符単位に変換
            duration_quarters = note_event.duration / beat_duration
            # 最小長：16分音符（0.25四分音符）
            duration_quarters = max(0.25, duration_quarters)

            n = music21.note.Note(note_event.pitch)
            n.quarterLength = duration_quarters
            n.volume.velocity = note_event.velocity

            # オフセット（開始位置）を四分音符単位で設定
            offset_quarters = note_event.start / beat_duration
            part.insert(offset_quarters, n)

        # ストリームを整形（タイ、小節線等を自動調整）
        part.makeRests(fillGaps=True, inPlace=True)

        return part
