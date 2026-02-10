"""pretty_midi による MidiProcessor ポートの実装

MIDI データの Base64 エンコード/デコード、テンポ検出などを担当する。
"""

import base64
import io
import logging

import pretty_midi

from src.application.ports.midi_processor import MidiProcessorPort
from src.domain.entities import MidiData, NoteEvent

logger = logging.getLogger(__name__)


class PrettyMidiProcessor(MidiProcessorPort):
    """pretty_midi を使った MIDI データ加工"""

    def to_base64(self, midi_data: MidiData) -> str:
        """MIDIデータを Base64 エンコードされた MIDI ファイルに変換する"""
        pm = self._to_pretty_midi(midi_data)

        # メモリ上に MIDI ファイルを書き出す
        buffer = io.BytesIO()
        pm.write(buffer)
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode("utf-8")

    def from_base64(self, midi_base64: str) -> MidiData:
        """Base64 エンコードされた MIDI ファイルを MIDIデータに変換する"""
        raw = base64.b64decode(midi_base64)
        buffer = io.BytesIO(raw)

        pm = pretty_midi.PrettyMIDI(buffer)

        notes: list[NoteEvent] = []
        for instrument in pm.instruments:
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
        tempo_times, tempos = pm.get_tempo_changes()
        tempo = tempos[0] if len(tempos) > 0 else 120.0

        return MidiData(
            notes=notes,
            tempo=float(tempo),
        )

    def detect_tempo(self, midi_data: MidiData) -> float:
        """テンポを返す（既にMidiDataに含まれている）"""
        return midi_data.tempo

    def _to_pretty_midi(self, midi_data: MidiData) -> pretty_midi.PrettyMIDI:
        """内部表現を pretty_midi オブジェクトに変換する"""
        pm = pretty_midi.PrettyMIDI(
            initial_tempo=midi_data.tempo,
        )

        # タイムシグネチャ設定
        ts = pretty_midi.containers.TimeSignature(
            numerator=midi_data.time_signature_numerator,
            denominator=midi_data.time_signature_denominator,
            time=0,
        )
        pm.time_signature_changes.append(ts)

        # ピアノインストゥルメント
        instrument = pretty_midi.Instrument(program=0, is_drum=False, name="Piano")

        for note in midi_data.notes:
            midi_note = pretty_midi.Note(
                velocity=note.velocity,
                pitch=note.pitch,
                start=note.start,
                end=note.end,
            )
            instrument.notes.append(midi_note)

        pm.instruments.append(instrument)
        return pm
