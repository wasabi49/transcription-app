"""DI コンテナ: Port → Adapter の紐付け

FastAPI の Depends を使って各ポートの具体実装を注入する。
ライブラリを差し替える場合はここの実装クラスを変更するだけで済む。
"""

from functools import lru_cache

from src.application.ports.midi_processor import MidiProcessorPort
from src.application.ports.sheet_music_generator import SheetMusicGeneratorPort
from src.application.ports.transcriber import TranscriberPort
from src.application.usecases.simplify_music import SimplifyMusicUseCase
from src.application.usecases.transcribe_music import TranscribeMusicUseCase
from src.infrastructure.basic_pitch_transcriber import BasicPitchTranscriber
from src.infrastructure.music21_generator import Music21Generator
from src.infrastructure.pretty_midi_processor import PrettyMidiProcessor


@lru_cache
def get_transcriber() -> TranscriberPort:
    """Transcriber ポートの具体実装を返す"""
    return BasicPitchTranscriber()


@lru_cache
def get_midi_processor() -> MidiProcessorPort:
    """MidiProcessor ポートの具体実装を返す"""
    return PrettyMidiProcessor()


@lru_cache
def get_sheet_music_generator() -> SheetMusicGeneratorPort:
    """SheetMusicGenerator ポートの具体実装を返す"""
    return Music21Generator()


def get_transcribe_usecase() -> TranscribeMusicUseCase:
    """採譜ユースケースを組み立てて返す"""
    return TranscribeMusicUseCase(
        transcriber=get_transcriber(),
        midi_processor=get_midi_processor(),
        sheet_music_generator=get_sheet_music_generator(),
    )


def get_simplify_usecase() -> SimplifyMusicUseCase:
    """簡略化ユースケースを組み立てて返す"""
    return SimplifyMusicUseCase(
        midi_processor=get_midi_processor(),
        sheet_music_generator=get_sheet_music_generator(),
    )
