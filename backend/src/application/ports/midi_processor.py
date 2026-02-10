"""MidiProcessor ポート: MIDIデータ加工の抽象インターフェース

MIDIデータのシリアライズ/デシリアライズ、テンポ検出等を担当する。
具体実装は infrastructure 層で提供する（例: PrettyMidiProcessor）。
"""

from abc import ABC, abstractmethod

from src.domain.entities import MidiData


class MidiProcessorPort(ABC):
    """MIDIデータ加工ポート"""

    @abstractmethod
    def to_base64(self, midi_data: MidiData) -> str:
        """MIDIデータをBase64エンコードされたMIDIファイルに変換する

        Args:
            midi_data: 内部表現のMIDIデータ

        Returns:
            Base64エンコードされたMIDIファイルデータ
        """
        ...

    @abstractmethod
    def from_base64(self, midi_base64: str) -> MidiData:
        """Base64エンコードされたMIDIファイルをMIDIデータに変換する

        Args:
            midi_base64: Base64エンコードされたMIDIファイルデータ

        Returns:
            内部表現のMIDIデータ
        """
        ...

    @abstractmethod
    def detect_tempo(self, midi_data: MidiData) -> float:
        """MIDIデータからテンポ（BPM）を検出する

        Args:
            midi_data: MIDIデータ

        Returns:
            テンポ（BPM）
        """
        ...
