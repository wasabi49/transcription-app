/**
 * SSE クライアント（fetch + ReadableStream ベース）
 *
 * POST リクエストに対応するSSEクライアント。
 * EventSource はGETのみのため fetch + ReadableStream で実装。
 */

const API_BASE_URL = "";

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export type SSEEventHandler = (event: SSEEvent) => void;

/**
 * 音声ファイルを採譜APIにアップロードし、SSEイベントを受信する
 */
export async function transcribeWithSSE(
  file: File,
  difficulty: string,
  onEvent: SSEEventHandler,
  onError: (error: Error) => void,
  signal?: AbortSignal
): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("difficulty", difficulty);

  try {
    const response = await fetch(`${API_BASE_URL}/api/transcribe`, {
      method: "POST",
      body: formData,
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTPエラー ${response.status}: ${errorText}`);
    }

    if (!response.body) {
      throw new Error("レスポンスボディがありません");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSEイベントをパース（\n\n で区切り）
      const events = buffer.split("\n\n");
      // 最後の不完全なイベントはバッファに残す
      buffer = events.pop() || "";

      for (const eventStr of events) {
        const parsed = parseSSEEvent(eventStr);
        if (parsed) {
          onEvent(parsed);
        }
      }
    }

    // 残りのバッファを処理
    if (buffer.trim()) {
      const parsed = parseSSEEvent(buffer);
      if (parsed) {
        onEvent(parsed);
      }
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return; // キャンセルされた場合は無視
    }
    onError(error instanceof Error ? error : new Error(String(error)));
  }
}

/**
 * MIDI Base64からPDFをダウンロードする
 * ブラウザ表示と同じ _build_score() パスでScoreを構築するため
 * MusicXMLの再パースによる差異が発生しない
 */
export async function downloadPdf(
  midiBase64: string
): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/export-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ midi_base64: midiBase64 }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`PDF生成に失敗しました: ${errorText}`);
  }

  return response.blob();
}

/**
 * SSEイベント文字列をパースする
 */
function parseSSEEvent(eventStr: string): SSEEvent | null {
  const lines = eventStr.trim().split("\n");
  let event = "";
  let data = "";

  for (const line of lines) {
    if (line.startsWith("event: ")) {
      event = line.slice(7);
    } else if (line.startsWith("data: ")) {
      data = line.slice(6);
    }
  }

  if (!event || !data) return null;

  try {
    return { event, data: JSON.parse(data) };
  } catch {
    return null;
  }
}
