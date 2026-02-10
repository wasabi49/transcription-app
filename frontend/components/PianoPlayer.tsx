"use client";

/**
 * ピアノ再生コンポーネント
 * Tone.js でサウンドフォントを使ってMIDIデータを再生する。
 * ブラウザのAutoPlay制約により、ユーザー操作で AudioContext を起動する。
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useAppStore } from "@/stores/useAppStore";
import { decodeMidiBase64, extractNotes, getDuration, type MidiNote } from "@/lib/midi";

export default function PianoPlayer() {
  const { result, playbackStatus, setPlaybackStatus } = useAppStore();
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const synthRef = useRef<any>(null);
  const scheduledEventsRef = useRef<number[]>([]);
  const toneRef = useRef<typeof import("tone") | null>(null);
  const animationRef = useRef<number | null>(null);

  // クリーンアップ
  useEffect(() => {
    return () => {
      stopPlayback();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const initTone = useCallback(async () => {
    if (toneRef.current) return toneRef.current;

    const Tone = await import("tone");
    await Tone.start();
    toneRef.current = Tone;
    return Tone;
  }, []);

  const stopPlayback = useCallback(() => {
    if (toneRef.current) {
      toneRef.current.getTransport().stop();
      toneRef.current.getTransport().cancel();
    }
    if (synthRef.current) {
      synthRef.current.releaseAll();
    }
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    scheduledEventsRef.current = [];
    setPlaybackStatus("stopped");
    setCurrentTime(0);
  }, [setPlaybackStatus]);

  const startPlayback = useCallback(async () => {
    if (!result?.midiBase64) return;

    try {
      const Tone = await initTone();

      // MIDI パース
      const midi = decodeMidiBase64(result.midiBase64);
      const notes = extractNotes(midi);
      const totalDuration = getDuration(midi);
      setDuration(totalDuration);

      // 既存の再生をクリア
      const transport = Tone.getTransport();
      transport.stop();
      transport.cancel();
      if (synthRef.current) {
        synthRef.current.releaseAll();
      }

      // シンセ作成（ピアノ音色）
      const synth = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: "triangle" },
        envelope: {
          attack: 0.005,
          decay: 0.3,
          sustain: 0.3,
          release: 0.8,
        },
      }).toDestination();

      synthRef.current = synth;

      // ノートをスケジュール
      for (const note of notes) {
        transport.schedule((time: number) => {
          synth.triggerAttackRelease(
            note.name,
            note.duration,
            time,
            note.velocity
          );
        }, note.time);
      }

      // 再生終了時のスケジュール
      transport.schedule(() => {
        stopPlayback();
      }, totalDuration + 0.5);

      // タイムトラッキング
      const updateTime = () => {
        if (transport.state === "started") {
          setCurrentTime(transport.seconds);
          animationRef.current = requestAnimationFrame(updateTime);
        }
      };

      transport.position = 0;
      transport.start();
      setPlaybackStatus("playing");
      animationRef.current = requestAnimationFrame(updateTime);
    } catch (e) {
      console.error("再生エラー:", e);
      stopPlayback();
    }
  }, [result, initTone, setPlaybackStatus, stopPlayback]);

  const togglePlayback = useCallback(async () => {
    if (playbackStatus === "playing") {
      if (toneRef.current) {
        toneRef.current.getTransport().pause();
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      setPlaybackStatus("paused");
    } else if (playbackStatus === "paused") {
      if (toneRef.current) {
        const transport = toneRef.current.getTransport();
        transport.start();
        const updateTime = () => {
          if (transport.state === "started") {
            setCurrentTime(transport.seconds);
            animationRef.current = requestAnimationFrame(updateTime);
          }
        };
        animationRef.current = requestAnimationFrame(updateTime);
      }
      setPlaybackStatus("playing");
    } else {
      await startPlayback();
    }
  }, [playbackStatus, setPlaybackStatus, startPlayback]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const isDisabled = !result?.midiBase64;

  return (
    <div className="flex items-center gap-4 p-4 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-zinc-50 dark:bg-zinc-900/50">
      {/* 再生/一時停止ボタン */}
      <button
        onClick={togglePlayback}
        disabled={isDisabled}
        className={`
          flex items-center justify-center w-12 h-12 rounded-full
          transition-colors duration-200
          ${
            isDisabled
              ? "bg-zinc-200 dark:bg-zinc-800 text-zinc-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          }
        `}
        aria-label={playbackStatus === "playing" ? "一時停止" : "再生"}
      >
        {playbackStatus === "playing" ? (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="4" width="4" height="16" />
            <rect x="14" y="4" width="4" height="16" />
          </svg>
        ) : (
          <svg className="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
            <polygon points="5,3 19,12 5,21" />
          </svg>
        )}
      </button>

      {/* 停止ボタン */}
      <button
        onClick={stopPlayback}
        disabled={isDisabled || playbackStatus === "stopped"}
        className={`
          flex items-center justify-center w-10 h-10 rounded-full
          transition-colors duration-200
          ${
            isDisabled || playbackStatus === "stopped"
              ? "bg-zinc-200 dark:bg-zinc-800 text-zinc-400 cursor-not-allowed"
              : "bg-zinc-300 dark:bg-zinc-700 hover:bg-zinc-400 dark:hover:bg-zinc-600 text-zinc-700 dark:text-zinc-200"
          }
        `}
        aria-label="停止"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <rect x="4" y="4" width="16" height="16" />
        </svg>
      </button>

      {/* プログレスバー */}
      <div className="flex-1">
        <div className="h-2 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 rounded-full transition-all duration-100"
            style={{
              width: duration > 0 ? `${(currentTime / duration) * 100}%` : "0%",
            }}
          />
        </div>
      </div>

      {/* 時間表示 */}
      <span className="text-xs text-zinc-500 tabular-nums min-w-[80px] text-right">
        {formatTime(currentTime)} / {formatTime(duration)}
      </span>
    </div>
  );
}
