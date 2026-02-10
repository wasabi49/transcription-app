"use client";

/**
 * 楽譜表示コンポーネント
 * OpenSheetMusicDisplay (OSMD) を使って MusicXML を SVG 描画する。
 * Next.js で SSR 不可のため dynamic import で遅延読み込み。
 */

import { useEffect, useRef, useState } from "react";

interface SheetMusicViewerProps {
  musicxml: string | null;
}

export default function SheetMusicViewer({ musicxml }: SheetMusicViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const osmdRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!musicxml || !containerRef.current) return;

    let cancelled = false;

    async function render() {
      setIsLoading(true);
      setError(null);

      try {
        // OSMD をダイナミックインポート（SSR回避）
        const { OpenSheetMusicDisplay } = await import("opensheetmusicdisplay");

        if (cancelled || !containerRef.current) return;

        // 既存のOSMDインスタンスをクリア
        if (osmdRef.current) {
          containerRef.current.innerHTML = "";
        }

        const osmd = new OpenSheetMusicDisplay(containerRef.current, {
          autoResize: true,
          backend: "svg",
          drawTitle: false,
        });

        osmdRef.current = osmd;
        await osmd.load(musicxml!);

        if (cancelled) return;

        osmd.render();
      } catch (e) {
        if (!cancelled) {
          console.error("楽譜表示エラー:", e);
          setError("楽譜の表示に失敗しました");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    render();

    return () => {
      cancelled = true;
    };
  }, [musicxml]);

  if (!musicxml) {
    return (
      <div className="flex items-center justify-center h-64 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-zinc-50 dark:bg-zinc-900/50">
        <p className="text-sm text-zinc-400">楽譜がここに表示されます</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-black/80 z-10 rounded-xl">
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
            楽譜を描画中...
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 rounded-xl">
          {error}
        </div>
      )}

      <div
        ref={containerRef}
        className="w-full overflow-x-auto border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-950 p-4 min-h-[200px]"
      />
    </div>
  );
}
