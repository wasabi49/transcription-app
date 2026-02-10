"use client";

/**
 * メインページ: 採譜アプリの統合ページ
 *
 * フロー:
 * 1. ファイルアップロード
 * 2. 採譜処理（SSE進捗表示）
 * 3. 楽譜表示 + ピアノ再生 + 難易度切替
 */

import { useCallback, useRef } from "react";
import { useAppStore, type Difficulty } from "@/stores/useAppStore";
import { transcribeWithSSE, type SSEEvent } from "@/lib/api";
import FileUpload from "@/components/FileUpload";
import SheetMusicViewer from "@/components/SheetMusicViewer";
import PianoPlayer from "@/components/PianoPlayer";
import DifficultySelector from "@/components/DifficultySelector";
import ProcessingIndicator from "@/components/ProcessingIndicator";

export default function Home() {
  const {
    transcriptionStatus,
    result,
    difficulty,
    setTranscriptionStatus,
    setProgress,
    setResult,
    setOriginalMidiBase64,
    setErrorMessage,
    reset,
  } = useAppStore();

  const abortRef = useRef<AbortController | null>(null);

  const handleFileSelect = useCallback(
    async (file: File) => {
      // 既存の処理をキャンセル
      abortRef.current?.abort();
      const abortController = new AbortController();
      abortRef.current = abortController;

      reset();
      setTranscriptionStatus("uploading");

      await transcribeWithSSE(
        file,
        difficulty,
        (event: SSEEvent) => {
          switch (event.event) {
            case "progress":
              setTranscriptionStatus("transcribing");
              setProgress({
                step: event.data.step as string,
                progressPercent: event.data.progress_percent as number,
                message: event.data.message as string,
              });
              break;

            case "complete": {
              const data = event.data;
              const metadata = data.metadata as Record<string, unknown>;
              const resultData = {
                musicxml: data.musicxml as string,
                midiBase64: data.midi_base64 as string,
                metadata: {
                  durationSeconds: metadata.duration_seconds as number,
                  noteCount: metadata.note_count as number,
                  tempo: metadata.tempo as number,
                  difficulty: metadata.difficulty as Difficulty,
                },
              };
              setResult(resultData);
              // 原曲のMIDIを保持（難易度変更の元データ）
              setOriginalMidiBase64(data.midi_base64 as string);
              break;
            }

            case "error":
              setErrorMessage(event.data.message as string);
              break;
          }
        },
        (error: Error) => {
          setErrorMessage(error.message);
        },
        abortController.signal
      );
    },
    [
      difficulty,
      reset,
      setTranscriptionStatus,
      setProgress,
      setResult,
      setOriginalMidiBase64,
      setErrorMessage,
    ]
  );

  const handleNewUpload = useCallback(() => {
    abortRef.current?.abort();
    reset();
  }, [reset]);

  const isProcessing =
    transcriptionStatus === "uploading" || transcriptionStatus === "transcribing";

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* ヘッダー */}
        <header className="mb-10">
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
            採譜アプリ
          </h1>
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">
            楽曲ファイルからピアノ楽譜を生成します
          </p>
        </header>

        <div className="flex flex-col gap-6">
          {/* ファイルアップロード */}
          {(transcriptionStatus === "idle" || transcriptionStatus === "error") && (
            <FileUpload onFileSelect={handleFileSelect} disabled={isProcessing} />
          )}

          {/* 進捗表示 */}
          <ProcessingIndicator />

          {/* 結果表示エリア */}
          {transcriptionStatus === "complete" && result && (
            <>
              {/* 操作バー */}
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <DifficultySelector />
                <button
                  onClick={handleNewUpload}
                  className="px-4 py-2 text-sm font-medium text-zinc-600 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
                >
                  別のファイルを選択
                </button>
              </div>

              {/* メタ情報 */}
              <div className="flex gap-4 text-xs text-zinc-500">
                <span>テンポ: {Math.round(result.metadata.tempo)} BPM</span>
                <span>ノート数: {result.metadata.noteCount}</span>
                <span>
                  長さ: {Math.floor(result.metadata.durationSeconds / 60)}:
                  {Math.floor(result.metadata.durationSeconds % 60)
                    .toString()
                    .padStart(2, "0")}
                </span>
              </div>

              {/* ピアノ再生 */}
              <PianoPlayer />

              {/* 楽譜表示 */}
              <SheetMusicViewer musicxml={result.musicxml} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
