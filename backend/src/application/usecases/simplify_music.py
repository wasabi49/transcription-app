"""簡略化ユースケース

既存のMIDIデータ（Base64）を別の難易度に簡略化する。
採譜処理は不要（元MIDIからの再計算のみ、< 1秒）。
"""

import logging

from src.application.ports.midi_processor import MidiProcessorPort
from src.application.ports.sheet_music_generator import SheetMusicGeneratorPort
from src.domain.entities import (
    Difficulty,
    TranscriptionMetadata,
    TranscriptionResult,
)
from src.domain.simplification import simplify
from src.domain.transcription import preprocess_midi

logger = logging.getLogger(__name__)


class SimplifyMusicUseCase:
    """MIDIデータの難易度変更ユースケース"""

    def __init__(
        self,
        midi_processor: MidiProcessorPort,
        sheet_music_generator: SheetMusicGeneratorPort,
    ):
        self._midi_processor = midi_processor
        self._sheet_music_generator = sheet_music_generator

    def execute(
        self,
        midi_base64: str,
        difficulty: Difficulty,
    ) -> TranscriptionResult:
        """難易度変更を実行する

        Args:
            midi_base64: Base64エンコードされた元MIDIデータ
            difficulty: 目標の難易度

        Returns:
            新しい難易度で簡略化された結果
        """
        # 1. Base64 → MIDIデータにデコード
        midi_data = self._midi_processor.from_base64(midi_base64)
        logger.info("MIDIデコード完了: %d ノート", midi_data.note_count)

        # 2. 前処理（量子化済みでも冪等なので再適用して問題なし）
        midi_data = preprocess_midi(midi_data)

        # 3. 難易度に応じた簡略化
        simplified = simplify(midi_data, difficulty)
        logger.info(
            "簡略化完了 (%s): %d → %d ノート",
            difficulty.value,
            midi_data.note_count,
            simplified.note_count,
        )

        # 4. MusicXML + MIDI Base64 を同一 Score から生成（一致保証）
        musicxml, new_midi_base64 = self._sheet_music_generator.generate_musicxml_and_midi(simplified)

        # 5. メタデータ
        metadata = TranscriptionMetadata(
            duration_seconds=simplified.duration,
            note_count=simplified.note_count,
            tempo=simplified.tempo,
            difficulty=difficulty,
        )

        return TranscriptionResult(
            musicxml=musicxml,
            midi_base64=new_midi_base64,
            metadata=metadata,
        )
