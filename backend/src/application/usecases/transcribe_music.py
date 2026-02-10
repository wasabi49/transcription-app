"""採譜ユースケース

音声ファイルからMIDIデータへの変換 → 前処理 → 難易度簡略化 → MusicXML生成
の一連フローをポート経由で組み立てる。
"""

import logging
from pathlib import Path

from src.application.ports.midi_processor import MidiProcessorPort
from src.application.ports.sheet_music_generator import SheetMusicGeneratorPort
from src.application.ports.transcriber import TranscriberPort
from src.domain.entities import (
    Difficulty,
    TranscriptionMetadata,
    TranscriptionResult,
)
from src.domain.simplification import simplify
from src.domain.transcription import preprocess_midi

logger = logging.getLogger(__name__)


class TranscribeMusicUseCase:
    """音声ファイルの採譜ユースケース"""

    def __init__(
        self,
        transcriber: TranscriberPort,
        midi_processor: MidiProcessorPort,
        sheet_music_generator: SheetMusicGeneratorPort,
    ):
        self._transcriber = transcriber
        self._midi_processor = midi_processor
        self._sheet_music_generator = sheet_music_generator

    async def execute(
        self,
        audio_path: Path,
        difficulty: Difficulty,
    ) -> TranscriptionResult:
        """採譜を実行する

        Args:
            audio_path: 音声ファイルのパス
            difficulty: 目標の難易度

        Returns:
            採譜結果（MusicXML + Base64 MIDI + メタデータ）
        """
        # 1. 音声 → MIDIデータ（Basic Pitch経由）
        logger.info("採譜開始: %s", audio_path.name)
        midi_data, _ = await self._transcriber.transcribe(audio_path)
        logger.info("採譜完了: %d ノート検出", midi_data.note_count)

        # 2. 共通前処理（16分音符への量子化 + 重複除去）
        midi_data = preprocess_midi(midi_data)
        logger.info("前処理完了: %d ノート", midi_data.note_count)

        # 3. 難易度に応じた簡略化
        simplified = simplify(midi_data, difficulty)
        logger.info(
            "簡略化完了 (%s): %d → %d ノート",
            difficulty.value,
            midi_data.note_count,
            simplified.note_count,
        )

        # 4. MusicXML生成
        musicxml = self._sheet_music_generator.generate_musicxml(simplified)
        logger.info("MusicXML生成完了")

        # 5. Base64 MIDI生成
        midi_base64 = self._midi_processor.to_base64(simplified)

        # 6. メタデータ
        metadata = TranscriptionMetadata(
            duration_seconds=simplified.duration,
            note_count=simplified.note_count,
            tempo=simplified.tempo,
            difficulty=difficulty,
        )

        return TranscriptionResult(
            musicxml=musicxml,
            midi_base64=midi_base64,
            metadata=metadata,
        )
