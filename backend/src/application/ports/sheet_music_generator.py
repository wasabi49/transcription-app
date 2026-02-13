"""SheetMusicGenerator ポート: MIDIデータ → MusicXML変換の抽象インターフェース

具体実装は infrastructure 層で提供する（例: Music21Generator）。
"""

from abc import ABC, abstractmethod
from typing import Any

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

    @abstractmethod
    def generate_musicxml_and_midi(self, midi_data: MidiData) -> tuple[str, str]:
        """MIDIデータからMusicXMLとMIDI Base64を同一Scoreから生成する

        同じ music21 Score オブジェクトから両方を出力するため、
        MusicXML（表示用）と MIDI（再生用）の内容が一致する。

        Args:
            midi_data: 内部表現のMIDIデータ

        Returns:
            (MusicXML文字列, Base64エンコードされたMIDIデータ)
        """
        ...

    @abstractmethod
    def build_score(self, midi_data: MidiData) -> Any:
        """MIDIデータから music21 Score オブジェクトを構築する

        PDF出力など、Scoreオブジェクトを直接操作する必要がある場合に使用する。
        converter.parse() による再パースを回避するために公開する。

        Args:
            midi_data: 内部表現のMIDIデータ

        Returns:
            music21 Score オブジェクト
        """
        ...
