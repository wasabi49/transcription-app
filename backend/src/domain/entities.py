"""ドメインエンティティ・値オブジェクト定義

外部ライブラリに依存しない純粋なデータ構造。
"""

from dataclasses import dataclass, field
from enum import StrEnum


class Difficulty(StrEnum):
    """難易度レベル"""

    ORIGINAL = "original"
    ADVANCED = "advanced"
    INTERMEDIATE = "intermediate"
    BEGINNER = "beginner"


@dataclass(frozen=True)
class NoteEvent:
    """単一のノートイベント

    Attributes:
        pitch: MIDIノート番号 (0-127)
        start: 開始時刻（秒）
        end: 終了時刻（秒）
        velocity: ベロシティ (0-127)
    """

    pitch: int
    start: float
    end: float
    velocity: int = 100

    @property
    def duration(self) -> float:
        """音符の長さ（秒）"""
        return self.end - self.start


@dataclass
class MidiData:
    """MIDI データの内部表現

    外部ライブラリ（pretty_midi等）に依存しない中間表現。
    Port/Adapterの境界を越えるデータ構造として使用する。

    Attributes:
        notes: ノートイベントのリスト
        tempo: テンポ（BPM）
        time_signature_numerator: 拍子の分子
        time_signature_denominator: 拍子の分母
    """

    notes: list[NoteEvent] = field(default_factory=list)
    tempo: float = 120.0
    time_signature_numerator: int = 4
    time_signature_denominator: int = 4

    @property
    def duration(self) -> float:
        """楽曲の長さ（秒）"""
        if not self.notes:
            return 0.0
        return max(note.end for note in self.notes)

    @property
    def note_count(self) -> int:
        """ノート数"""
        return len(self.notes)


@dataclass(frozen=True)
class TranscriptionMetadata:
    """採譜結果のメタデータ"""

    duration_seconds: float
    note_count: int
    tempo: float
    difficulty: Difficulty


@dataclass
class TranscriptionResult:
    """採譜の最終結果"""

    musicxml: str
    midi_base64: str
    metadata: TranscriptionMetadata
