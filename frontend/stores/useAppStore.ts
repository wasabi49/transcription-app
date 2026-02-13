/**
 * zustand ストア: アプリケーション全体の状態管理
 *
 * - 採譜状態（アップロード中/採譜中/完了/エラー）
 * - 再生状態（停止/再生中/一時停止）
 * - 難易度
 * - 結果データ（MusicXML, MIDI Base64）
 */

import { create } from "zustand";

export type TranscriptionStatus =
  | "idle"
  | "uploading"
  | "transcribing"
  | "complete"
  | "error";

export type PlaybackStatus = "stopped" | "playing" | "paused";

export type Difficulty = "original" | "advanced" | "intermediate" | "beginner";

export interface ProgressInfo {
  step: string;
  progressPercent: number;
  message: string;
}

export interface TranscriptionMetadata {
  durationSeconds: number;
  noteCount: number;
  tempo: number;
  difficulty: Difficulty;
}

export interface TranscriptionResult {
  musicxml: string;
  midiBase64: string;
  metadata: TranscriptionMetadata;
}

interface AppState {
  // 採譜状態
  transcriptionStatus: TranscriptionStatus;
  progress: ProgressInfo | null;
  result: TranscriptionResult | null;
  errorMessage: string | null;

  // 再生状態
  playbackStatus: PlaybackStatus;

  // 難易度
  difficulty: Difficulty;

  // アクション
  setTranscriptionStatus: (status: TranscriptionStatus) => void;
  setProgress: (progress: ProgressInfo) => void;
  setResult: (result: TranscriptionResult) => void;
  setErrorMessage: (message: string | null) => void;
  setPlaybackStatus: (status: PlaybackStatus) => void;
  setDifficulty: (difficulty: Difficulty) => void;
  reset: () => void;
}

const initialState = {
  transcriptionStatus: "idle" as TranscriptionStatus,
  progress: null,
  result: null,
  errorMessage: null,
  playbackStatus: "stopped" as PlaybackStatus,
  difficulty: "original" as Difficulty,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  setTranscriptionStatus: (status) => set({ transcriptionStatus: status }),

  setProgress: (progress) => set({ progress }),

  setResult: (result) => set({ result, transcriptionStatus: "complete" }),

  setErrorMessage: (message) =>
    set({ errorMessage: message, transcriptionStatus: message ? "error" : "idle" }),

  setPlaybackStatus: (status) => set({ playbackStatus: status }),

  setDifficulty: (difficulty) => set({ difficulty }),

  reset: () => set(initialState),
}));
