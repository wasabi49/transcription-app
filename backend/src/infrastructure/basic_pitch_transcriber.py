"""Basic Pitch による Transcriber ポートの実装

Spotify の Basic Pitch ライブラリを使って音声ファイルを MIDI データに変換する。
"""

import asyncio
import logging
from pathlib import Path

from src.application.ports.transcriber import ProgressEvent, TranscriberPort
from src.core.exceptions import TranscriptionError
from src.domain.entities import MidiData, NoteEvent

logger = logging.getLogger(__name__)


class BasicPitchTranscriber(TranscriberPort):
    """Basic Pitch を使った音声→MIDI変換"""

    async def transcribe(self, audio_path: Path) -> tuple[MidiData, list[ProgressEvent]]:
        """音声ファイルをMIDIデータに変換する

        CPU-bound 処理のため asyncio.to_thread() で実行する。
        """
        progress_events: list[ProgressEvent] = []

        progress_events.append(
            ProgressEvent(
                step="transcription",
                progress_percent=10,
                message="採譜処理を開始しています...",
            )
        )

        try:
            # CPU-bound 処理をスレッドプールで実行
            midi_data = await asyncio.to_thread(self._transcribe_sync, audio_path)
        except Exception as e:
            logger.error("Basic Pitch 採譜エラー: %s", e)
            raise TranscriptionError(f"採譜処理に失敗しました: {e}") from e

        progress_events.append(
            ProgressEvent(
                step="transcription",
                progress_percent=80,
                message="採譜処理が完了しました",
            )
        )

        return midi_data, progress_events

    def _transcribe_sync(self, audio_path: Path) -> MidiData:
        """同期的に採譜を実行する（スレッドプール内で呼ばれる）"""
        from basic_pitch import ICASSP_2022_MODEL_PATH
        from basic_pitch.inference import predict

        logger.info("Basic Pitch 推論開始: %s", audio_path.name)

        # Basic Pitch で推論
        model_output, midi_object, note_events = predict(
            str(audio_path),
            ICASSP_2022_MODEL_PATH,
        )

        logger.info(
            "Basic Pitch 推論完了: %d ノート検出",
            len(midi_object.instruments[0].notes) if midi_object.instruments else 0,
        )

        # pretty_midi オブジェクトから内部表現に変換
        notes: list[NoteEvent] = []
        if midi_object.instruments:
            for instrument in midi_object.instruments:
                for note in instrument.notes:
                    notes.append(
                        NoteEvent(
                            pitch=note.pitch,
                            start=note.start,
                            end=note.end,
                            velocity=note.velocity,
                        )
                    )

        # テンポ検出
        tempo_times, tempos = midi_object.get_tempo_changes()
        tempo = tempos[0] if len(tempos) > 0 else 120.0

        return MidiData(
            notes=notes,
            tempo=float(tempo),
        )
