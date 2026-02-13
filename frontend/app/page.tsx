"use client";

/**
 * メインページ: 採譜アプリの統合ページ
 *
 * フロー:
 * 1. 難易度選択
 * 2. ファイルアップロード
 * 3. 採譜処理（SSE進捗表示）
 * 4. 楽譜表示 + ピアノ再生
 */

import { useCallback, useRef } from "react";
import { useAppStore, type Difficulty } from "@/stores/useAppStore";
import { transcribeWithSSE, downloadPdf, type SSEEvent } from "@/lib/api";
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
              setResult({
                musicxml: data.musicxml as string,
                midiBase64: data.midi_base64 as string,
                metadata: {
                  durationSeconds: metadata.duration_seconds as number,
                  noteCount: metadata.note_count as number,
                  tempo: metadata.tempo as number,
                  difficulty: metadata.difficulty as Difficulty,
                },
              });
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
          {/* 難易度選択 + ファイルアップロード */}
          {(transcriptionStatus === "idle" || transcriptionStatus === "error") && (
            <>
              <DifficultySelector />
              <FileUpload onFileSelect={handleFileSelect} disabled={isProcessing} />
            </>
          )}

          {/* 進捗表示 */}
          <ProcessingIndicator />

          {/* 結果表示エリア */}
          {transcriptionStatus === "complete" && result && (
            <>
              {/* 操作バー */}
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div className="flex gap-4 text-xs text-zinc-500">
                  <span>難易度: {result.metadata.difficulty === "original" ? "原曲" : result.metadata.difficulty === "advanced" ? "上級" : result.metadata.difficulty === "intermediate" ? "中級" : "初級"}</span>
                  <span>テンポ: {Math.round(result.metadata.tempo)} BPM</span>
                  <span>ノート数: {result.metadata.noteCount}</span>
                  <span>
                    長さ: {Math.floor(result.metadata.durationSeconds / 60)}:
                    {Math.floor(result.metadata.durationSeconds % 60)
                      .toString()
                      .padStart(2, "0")}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {/* ダウンロードボタン群 */}
                  <button
                    onClick={() => {
                      const blob = new Blob([result.musicxml], { type: "application/vnd.recordare.musicxml+xml" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "score.musicxml";
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-1.5"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    MusicXML
                  </button>
                  <button
                    onClick={() => {
                      const binaryStr = atob(result.midiBase64);
                      const bytes = new Uint8Array(binaryStr.length);
                      for (let i = 0; i < binaryStr.length; i++) {
                        bytes[i] = binaryStr.charCodeAt(i);
                      }
                      const blob = new Blob([bytes], { type: "audio/midi" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "score.mid";
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors flex items-center gap-1.5"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    MIDI
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        const blob = await downloadPdf(result.midiBase64);
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = "score.pdf";
                        a.click();
                        URL.revokeObjectURL(url);
                      } catch (e) {
                        console.error("PDF download error:", e);
                        alert("PDF生成に失敗しました");
                      }
                    }}
                    className="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors flex items-center gap-1.5"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    PDF
                  </button>
                  <button
                    onClick={handleNewUpload}
                    className="px-4 py-2 text-sm font-medium text-zinc-600 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
                  >
                    別のファイルを選択
                  </button>
                </div>
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
