"use client";

/**
 * 処理進捗表示コンポーネント
 * SSEの進捗イベントをプログレスバーとメッセージで表示する
 */

import { useAppStore } from "@/stores/useAppStore";

export default function ProcessingIndicator() {
  const { transcriptionStatus, progress, errorMessage } = useAppStore();

  if (transcriptionStatus === "idle" || transcriptionStatus === "complete") {
    return null;
  }

  if (transcriptionStatus === "error") {
    return (
      <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-xl">
        <svg className="w-5 h-5 text-red-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
        </svg>
        <div>
          <p className="text-sm font-medium text-red-800 dark:text-red-200">エラーが発生しました</p>
          <p className="text-xs text-red-600 dark:text-red-400 mt-0.5">
            {errorMessage || "不明なエラー"}
          </p>
        </div>
      </div>
    );
  }

  const percent = progress?.progressPercent ?? 0;

  return (
    <div className="flex flex-col gap-3 p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-xl">
      <div className="flex items-center gap-3">
        <svg className="animate-spin h-5 w-5 text-blue-600" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
            fill="none"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
        <div className="flex-1">
          <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
            {progress?.message || "処理中..."}
          </p>
        </div>
        <span className="text-sm font-mono text-blue-600 dark:text-blue-400">
          {percent}%
        </span>
      </div>

      {/* プログレスバー */}
      <div className="h-2 bg-blue-100 dark:bg-blue-900 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-600 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
