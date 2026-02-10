"use client";

/**
 * 難易度セレクター
 * 原曲 / 上級 / 中級 / 初級 の4段階を切り替える
 */

import { useAppStore, type Difficulty } from "@/stores/useAppStore";
import { simplifyMusic } from "@/lib/api";
import { useCallback, useState } from "react";

const DIFFICULTIES: { value: Difficulty; label: string; description: string }[] = [
  { value: "original", label: "原曲", description: "採譜結果そのまま" },
  { value: "advanced", label: "上級", description: "装飾音除去・ベロシティ正規化" },
  { value: "intermediate", label: "中級", description: "最大4音・範囲制限" },
  { value: "beginner", label: "初級", description: "メロディ+ベースのみ" },
];

export default function DifficultySelector() {
  const {
    difficulty,
    setDifficulty,
    originalMidiBase64,
    setResult,
    transcriptionStatus,
  } = useAppStore();
  const [isChanging, setIsChanging] = useState(false);

  const handleChange = useCallback(
    async (newDifficulty: Difficulty) => {
      if (newDifficulty === difficulty || !originalMidiBase64 || isChanging) return;

      setIsChanging(true);
      setDifficulty(newDifficulty);

      try {
        const response = await simplifyMusic(originalMidiBase64, newDifficulty);
        setResult({
          musicxml: response.musicxml,
          midiBase64: response.midi_base64,
          metadata: {
            durationSeconds: response.metadata.duration_seconds,
            noteCount: response.metadata.note_count,
            tempo: response.metadata.tempo,
            difficulty: response.metadata.difficulty as Difficulty,
          },
        });
      } catch (e) {
        console.error("難易度変更エラー:", e);
        // 元の難易度に戻す
        setDifficulty(difficulty);
      } finally {
        setIsChanging(false);
      }
    },
    [difficulty, originalMidiBase64, isChanging, setDifficulty, setResult]
  );

  const isDisabled = transcriptionStatus !== "complete";

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
        難易度
      </label>
      <div className="flex gap-2">
        {DIFFICULTIES.map((d) => (
          <button
            key={d.value}
            onClick={() => handleChange(d.value)}
            disabled={isDisabled || isChanging}
            title={d.description}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium
              transition-all duration-200
              ${
                difficulty === d.value
                  ? "bg-blue-600 text-white shadow-sm"
                  : isDisabled || isChanging
                    ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-400 cursor-not-allowed"
                    : "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
              }
            `}
          >
            {d.label}
          </button>
        ))}
      </div>
      {isChanging && (
        <p className="text-xs text-zinc-500">難易度を変更中...</p>
      )}
    </div>
  );
}
