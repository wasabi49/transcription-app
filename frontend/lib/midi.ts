/**
 * Base64 MIDI デコード・パースユーティリティ
 *
 * サーバーから受信した Base64 エンコード MIDI データを
 * Tone.js で再生可能な形式に変換する。
 */

import { Midi } from "@tonejs/midi";

/**
 * Base64 エンコードされた MIDI を Midi オブジェクトに変換する
 */
export function decodeMidiBase64(midiBase64: string): Midi {
  const binaryStr = atob(midiBase64);
  const bytes = new Uint8Array(binaryStr.length);
  for (let i = 0; i < binaryStr.length; i++) {
    bytes[i] = binaryStr.charCodeAt(i);
  }
  return new Midi(bytes.buffer);
}

/**
 * Midi オブジェクトからノート情報を抽出する
 */
export interface MidiNote {
  name: string; // e.g. "C4"
  midi: number; // MIDI note number
  time: number; // seconds
  duration: number; // seconds
  velocity: number; // 0-1
}

export function extractNotes(midi: Midi): MidiNote[] {
  const notes: MidiNote[] = [];
  for (const track of midi.tracks) {
    for (const note of track.notes) {
      notes.push({
        name: note.name,
        midi: note.midi,
        time: note.time,
        duration: note.duration,
        velocity: note.velocity,
      });
    }
  }
  return notes.sort((a, b) => a.time - b.time);
}

/**
 * MIDI のテンポ（BPM）を取得する
 */
export function getTempo(midi: Midi): number {
  if (midi.header.tempos.length > 0) {
    return midi.header.tempos[0].bpm;
  }
  return 120; // デフォルト
}

/**
 * MIDI の総再生時間（秒）を取得する
 */
export function getDuration(midi: Midi): number {
  return midi.duration;
}
