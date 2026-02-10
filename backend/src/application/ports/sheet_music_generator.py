"""SheetMusicGenerator ポート: MIDIデータ → MusicXML変換の抽象インターフェース

具体実装は infrastructure 層で提供する（例: Music21Generator）。
"""

from abc import ABC, abstractmethod

from src.domain.entities import MidiData


class SheetMusicGeneratorPort(ABC):
    """楽譜生成ポート"""

    @abstractmethod
    def generate_musicxml(self, midi_data: MidiData) -> str:
        """MIDIデータからMusicXMLを生成する

        Args:
            midi_data: 内部表現のMIDIデータ

        Returns:
            MusicXML文字列
        """
        ...
