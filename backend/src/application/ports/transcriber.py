"""Transcriber ポート: 音声ファイル → MIDIデータ変換の抽象インターフェース

具体実装は infrastructure 層で提供する（例: BasicPitchTranscriber）。
"""

from abc import ABC, abstractmethod
from pathlib import Path

from src.domain.entities import MidiData


class ProgressEvent:
    """進捗イベント"""

    def __init__(self, step: str, progress_percent: int, message: str):
        self.step = step
        self.progress_percent = progress_percent
        self.message = message


class TranscriberPort(ABC):
    """音声ファイルからMIDIデータへの変換ポート"""

    @abstractmethod
    async def transcribe(self, audio_path: Path) -> tuple[MidiData, list[ProgressEvent]]:
        """音声ファイルをMIDIデータに変換する

        Args:
            audio_path: 音声ファイルのパス（MP3 or WAV）

        Returns:
            (MIDIデータ, 進捗イベントリスト) のタプル

        Raises:
            TranscriptionError: 変換に失敗した場合
        """
        ...
