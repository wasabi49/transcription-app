"""API ルーター

SSE採譜エンドポイント + 難易度変更エンドポイント。
ファイルバリデーション・レート制限・Semaphore制御を含む。
"""

import asyncio
import json
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.dependencies import get_midi_processor, get_sheet_music_generator, get_simplify_usecase, get_transcribe_usecase
from src.application.ports.midi_processor import MidiProcessorPort
from src.application.ports.sheet_music_generator import SheetMusicGeneratorPort
from src.api.schemas import ExportPdfRequest, MetadataResponse, SimplifyRequest, SimplifyResponse
from src.application.usecases.simplify_music import SimplifyMusicUseCase
from src.application.usecases.transcribe_music import TranscribeMusicUseCase
from src.core.config import settings
from src.core.exceptions import (
    InvalidFileError,
    TranscriptionAppError,
)
from src.domain.entities import Difficulty

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# MP3/WAV のマジックバイト
MAGIC_BYTES = {
    b"\xff\xfb": "audio/mpeg",  # MP3 (MPEG frame sync)
    b"\xff\xf3": "audio/mpeg",  # MP3 (MPEG frame sync variant)
    b"\xff\xf2": "audio/mpeg",  # MP3 (MPEG frame sync variant)
    b"ID3": "audio/mpeg",  # MP3 (ID3 tag)
    b"RIFF": "audio/wav",  # WAV
}


def _validate_file(file: UploadFile) -> None:
    """アップロードファイルのバリデーション

    - 拡張子チェック
    - MIMEタイプ検証
    - ファイルサイズ制限は FastAPI/uvicorn 側で制御
    """
    if not file.filename:
        raise InvalidFileError("ファイル名が空です")

    # 拡張子チェック
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        allowed = ", ".join(settings.allowed_extensions)
        raise InvalidFileError(f"対応していないファイル形式です: {ext}。対応形式: {allowed}")

    # MIMEタイプチェック
    if file.content_type and file.content_type not in settings.allowed_mime_types:
        raise InvalidFileError(f"対応していないMIMEタイプです: {file.content_type}")


async def _validate_magic_bytes(file: UploadFile) -> None:
    """ファイルヘッダー（マジックバイト）を検証する"""
    header = await file.read(4)
    await file.seek(0)  # 読み取り位置をリセット

    if not header:
        raise InvalidFileError("空のファイルです")

    valid = any(header.startswith(magic) for magic in MAGIC_BYTES)
    if not valid:
        raise InvalidFileError("ファイルの内容が音声ファイルとして認識できません")


def _sanitize_filename(filename: str) -> str:
    """ファイル名をサニタイズする（パストラバーサル防止）"""
    # パス区切り文字を除去
    name = Path(filename).name
    # 危険な文字を除去
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    sanitized = "".join(c if c in safe_chars else "_" for c in name)
    return sanitized or "upload"


@router.post("/transcribe")
@limiter.limit(settings.rate_limit)
async def transcribe(
    request: Request,
    file: UploadFile = File(...),  # noqa: B008
    difficulty: Difficulty = Form(Difficulty.ORIGINAL),  # noqa: B008
    usecase: TranscribeMusicUseCase = Depends(get_transcribe_usecase),  # noqa: B008
):
    """音声ファイルを採譜してSSEで結果を返す

    - 対応形式: MP3, WAV
    - 同時処理制限: 1件（ビジー時は503）
    - レート制限: 1分あたり3リクエスト
    """
    # ファイルバリデーション
    try:
        _validate_file(file)
        await _validate_magic_bytes(file)
    except InvalidFileError as e:
        raise HTTPException(status_code=400, detail=e.message) from e

    # Semaphore でビジーチェック
    from main import transcription_semaphore

    if transcription_semaphore is None:
        raise HTTPException(status_code=500, detail="サーバー初期化中です")

    async def event_stream():
        """SSE イベントストリーム"""
        tmp_path: Path | None = None

        try:
            # Semaphore 取得を試みる（即座に）
            transcription_semaphore.locked()
            if transcription_semaphore._value == 0:  # noqa: SLF001
                msg = "サーバーがビジーです。しばらく待ってから再試行してください"
                yield _sse_event(
                    "error",
                    {"code": "SERVICE_BUSY", "message": msg},
                )
                return

            async with transcription_semaphore:
                # 進捗: アップロード受信
                yield _sse_event(
                    "progress",
                    {"step": "upload", "progress_percent": 5, "message": "ファイルを受信しました"},
                )

                # 一時ファイルに保存
                suffix = Path(file.filename or "upload").suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    content = await file.read()

                    # サイズチェック
                    if len(content) > settings.max_file_size:
                        max_mb = settings.max_file_size // 1024 // 1024
                        yield _sse_event(
                            "error",
                            {
                                "code": "FILE_TOO_LARGE",
                                "message": f"ファイルサイズが上限（{max_mb}MB）を超えています",
                            },
                        )
                        return

                    tmp.write(content)
                    tmp_path = Path(tmp.name)

                yield _sse_event(
                    "progress",
                    {
                        "step": "transcription",
                        "progress_percent": 10,
                        "message": "採譜処理を開始します...",
                    },
                )

                # 採譜実行
                result = await usecase.execute(tmp_path, difficulty)

                yield _sse_event(
                    "progress",
                    {"step": "complete", "progress_percent": 100, "message": "完了しました"},
                )

                # 完了イベント
                yield _sse_event(
                    "complete",
                    {
                        "musicxml": result.musicxml,
                        "midi_base64": result.midi_base64,
                        "metadata": {
                            "duration_seconds": result.metadata.duration_seconds,
                            "note_count": result.metadata.note_count,
                            "tempo": result.metadata.tempo,
                            "difficulty": result.metadata.difficulty.value,
                        },
                    },
                )

        except TranscriptionAppError as e:
            logger.error("採譜エラー: %s", e.message)
            yield _sse_event("error", {"code": e.code, "message": e.message})
        except Exception:
            logger.exception("予期しないエラー")
            yield _sse_event(
                "error",
                {"code": "INTERNAL_ERROR", "message": "予期しないエラーが発生しました"},
            )
        finally:
            # 一時ファイルの即時削除（権利関係リスク回避）
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
                logger.info("一時ファイル削除: %s", tmp_path)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/simplify", response_model=SimplifyResponse)
async def simplify_endpoint(
    request_body: SimplifyRequest,
    usecase: SimplifyMusicUseCase = Depends(get_simplify_usecase),  # noqa: B008
):
    """難易度を変更する（同期API、< 1秒）"""
    try:
        result = await asyncio.to_thread(
            usecase.execute, request_body.midi_base64, request_body.difficulty
        )

        return SimplifyResponse(
            musicxml=result.musicxml,
            midi_base64=result.midi_base64,
            metadata=MetadataResponse(
                duration_seconds=result.metadata.duration_seconds,
                note_count=result.metadata.note_count,
                tempo=result.metadata.tempo,
                difficulty=result.metadata.difficulty,
            ),
        )
    except TranscriptionAppError as e:
        raise HTTPException(status_code=400, detail=e.message) from e
    except Exception as exc:
        logger.exception("簡略化エラー")
        raise HTTPException(
            status_code=500,
            detail="簡略化処理中にエラーが発生しました",
        ) from exc


@router.post("/export-pdf")
async def export_pdf(
    request_body: ExportPdfRequest,
    midi_processor: MidiProcessorPort = Depends(get_midi_processor),  # noqa: B008
    sheet_music_generator: SheetMusicGeneratorPort = Depends(get_sheet_music_generator),  # noqa: B008
):
    """MIDI Base64 から PDF を生成して返す

    converter.parse() による MusicXML 再パースを回避するため、
    _build_score() と同じパスで Score を構築してから PDF を書き出す。
    """
    try:
        def _generate_pdf() -> bytes:
            # Base64 → MidiData（ブラウザ表示と同じデータソース）
            midi_data = midi_processor.from_base64(request_body.midi_base64)
            # _build_score() と同じパスで Score 構築（再パース回避）
            score = sheet_music_generator.build_score(midi_data)
            pdf_path = score.write("lily.pdf")
            pdf_bytes = Path(pdf_path).read_bytes()
            return pdf_bytes

        pdf_bytes = await asyncio.to_thread(_generate_pdf)

        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="score.pdf"'},
        )
    except Exception as exc:
        logger.exception("PDF生成エラー")
        raise HTTPException(
            status_code=500,
            detail="PDF生成中にエラーが発生しました",
        ) from exc


def _sse_event(event: str, data: dict) -> str:
    """SSE フォーマットのイベント文字列を生成する"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
