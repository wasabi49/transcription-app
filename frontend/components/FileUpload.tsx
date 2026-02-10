"use client";

/**
 * ファイルアップロードコンポーネント
 * ドラッグ&ドロップ + クリックでファイル選択
 * 対応形式: MP3, WAV
 */

import { useCallback, useRef, useState } from "react";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

const ACCEPTED_TYPES = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/wave", "audio/x-wav"];
const ACCEPTED_EXTENSIONS = [".mp3", ".wav"];
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export default function FileUpload({ onFileSelect, disabled = false }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    // 拡張子チェック
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return `対応していないファイル形式です: ${ext}。MP3またはWAVファイルを選択してください。`;
    }

    // サイズチェック
    if (file.size > MAX_FILE_SIZE) {
      return `ファイルサイズが大きすぎます（${(file.size / 1024 / 1024).toFixed(1)}MB）。上限は50MBです。`;
    }

    return null;
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      onFileSelect(file);
    },
    [onFileSelect, validateFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [disabled, handleFile]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!disabled) setIsDragging(true);
    },
    [disabled]
  );

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleClick = useCallback(() => {
    if (!disabled) fileInputRef.current?.click();
  }, [disabled]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      // リセットして同じファイルを再選択可能にする
      e.target.value = "";
    },
    [handleFile]
  );

  return (
    <div className="w-full">
      <div
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          flex flex-col items-center justify-center
          w-full h-48 border-2 border-dashed rounded-xl
          cursor-pointer transition-all duration-200
          ${
            isDragging
              ? "border-blue-500 bg-blue-50 dark:bg-blue-950/20"
              : "border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-600"
          }
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        <svg
          className="w-10 h-10 mb-3 text-zinc-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9 8.25H7.5a2.25 2.25 0 0 0-2.25 2.25v9a2.25 2.25 0 0 0 2.25 2.25h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25H15m0-3-3-3m0 0-3 3m3-3V15"
          />
        </svg>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          <span className="font-semibold">クリック</span>または
          <span className="font-semibold">ドラッグ&ドロップ</span>
          でファイルを選択
        </p>
        <p className="mt-1 text-xs text-zinc-500">MP3, WAV（最大50MB）</p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".mp3,.wav,audio/mpeg,audio/wav"
        onChange={handleInputChange}
        className="hidden"
      />

      {error && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
}
