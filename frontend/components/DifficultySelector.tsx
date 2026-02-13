"use client";

/**
 * 難易度セレクター
 * 原曲 / 上級 / 中級 / 初級 の4段階を楽譜生成前に選択する
 */

import { useAppStore, type Difficulty } from "@/stores/useAppStore";
import { useCallback } from "react";

const DIFFICULTIES: { value: Difficulty; label: string; description: string }[] = [
  { value: "original", label: "原曲", description: "採譜結果そのまま" },
  { value: "advanced", label: "上級", description: "装飾音除去・ベロシティ正規化" },
  { value: "intermediate", label: "中級", description: "最大4音・範囲制限" },
  { value: "beginner", label: "初級", description: "メロディ+ベースのみ" },
];

interface DifficultySelectorProps {
  disabled?: boolean;
}

export default function DifficultySelector({ disabled = false }: DifficultySelectorProps) {
  const { difficulty, setDifficulty } = useAppStore();

  const handleChange = useCallback(
    (newDifficulty: Difficulty) => {
      if (newDifficulty === difficulty || disabled) return;
      setDifficulty(newDifficulty);
    },
    [difficulty, disabled, setDifficulty]
  );

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
            disabled={disabled}
            title={d.description}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium
              transition-all duration-200
              ${
                difficulty === d.value
                  ? "bg-blue-600 text-white shadow-sm"
                  : disabled
                    ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-400 cursor-not-allowed"
                    : "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
              }
            `}
          >
            {d.label}
          </button>
        ))}
      </div>
    </div>
  );
}
