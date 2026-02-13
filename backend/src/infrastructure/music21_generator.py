"""music21 による SheetMusicGenerator ポートの実装

MIDIデータ（内部表現）から MusicXML 文字列を生成する。
"""

import base64
import logging
from pathlib import Path

import music21

from src.application.ports.sheet_music_generator import SheetMusicGeneratorPort
from src.domain.entities import MidiData

logger = logging.getLogger(__name__)


class Music21Generator(SheetMusicGeneratorPort):
    """music21 を使った MusicXML 生成"""

    def generate_musicxml(self, midi_data: MidiData) -> str:
        """MIDIデータから MusicXML を生成する"""
        score = self._build_score(midi_data)
        musicxml_str = score.write("musicxml").read_text()
        logger.info("MusicXML 生成完了: %d バイト", len(musicxml_str))
        return musicxml_str

    def generate_musicxml_and_midi(self, midi_data: MidiData) -> tuple[str, str]:
        """同一のmusic21 Scoreから MusicXML と MIDI Base64 を生成する

        これにより表示(OSMD)・再生(PianoPlayer)・ダウンロードの
        すべてが同じデータソースから生成され、一致が保証される。
        """
        score = self._build_score(midi_data)

        # MusicXML 生成
        musicxml_str = score.write("musicxml").read_text()
        logger.info("MusicXML 生成完了: %d バイト", len(musicxml_str))

        # MIDI 生成（同一Scoreから）
        midi_path = Path(score.write("midi"))
        midi_bytes = midi_path.read_bytes()
        midi_path.unlink(missing_ok=True)
        midi_base64 = base64.b64encode(midi_bytes).decode("utf-8")
        logger.info("MIDI Base64 生成完了: %d バイト", len(midi_base64))

        return musicxml_str, midi_base64

    def build_score(self, midi_data: MidiData) -> music21.stream.Score:
        """MIDIデータから music21 Score を構築する（公開API）

        PDF出力など、Scoreオブジェクトを直接操作する必要がある場合に使用する。
        converter.parse() による再パースを回避するために公開する。
        """
        return self._build_score(midi_data)

    def _build_score(self, midi_data: MidiData) -> music21.stream.Score:
        """MIDIデータから music21 Score を構築する（内部実装）"""
        score = music21.stream.Score()

        # メタデータ
        score.insert(0, music21.metadata.Metadata())
        score.metadata.title = "Transcription"

        # ノートを右手・左手に分割（ミドルC=60を基準）
        right_hand_notes = [n for n in midi_data.notes if n.pitch >= 60]
        left_hand_notes = [n for n in midi_data.notes if n.pitch < 60]

        # テンポ設定・拍子記号（各パートの先頭に挿入して MusicXML に正しく書き込まれるようにする）
        tempo_mark = music21.tempo.MetronomeMark(number=midi_data.tempo)
        ts = music21.meter.TimeSignature(
            f"{midi_data.time_signature_numerator}/{midi_data.time_signature_denominator}"
        )

        # 右手パート（高音部記号）
        right_part = self._create_part(right_hand_notes, midi_data.tempo, "Right Hand", "treble")
        right_part.insert(0, tempo_mark)
        right_part.insert(0, ts)
        score.insert(0, right_part)

        # 左手パート（低音部記号）
        left_part = self._create_part(left_hand_notes, midi_data.tempo, "Left Hand", "bass")
        score.insert(0, left_part)

        return score

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
