"""採譜アプリ バックエンドエントリーポイント"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings

logger = logging.getLogger(__name__)

# 同時採譜処理制限用セマフォ
transcription_semaphore: asyncio.Semaphore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    global transcription_semaphore

    # Semaphore初期化
    transcription_semaphore = asyncio.Semaphore(settings.max_concurrent_transcriptions)
    logger.info("同時採譜処理上限: %d件", settings.max_concurrent_transcriptions)

    # Basic Pitchモデルのプリロード
    try:
        import logging as _logging

        # TensorFlow の冗長ログを抑制
        _logging.getLogger("tensorflow").setLevel(_logging.ERROR)
        import os

        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

        from basic_pitch import ICASSP_2022_MODEL_PATH  # noqa: F401
        from basic_pitch.inference import predict  # noqa: F401

        logger.info("Basic Pitch モデルのプリロード完了")
    except Exception as e:
        logger.warning("Basic Pitch モデルのプリロードに失敗（初回リクエスト時にロードされます）: %s", e)

    yield

    # クリーンアップ
    transcription_semaphore = None
    logger.info("アプリケーション終了")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーターの登録
from src.api.router import router  # noqa: E402

app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health():
    """ヘルスチェック"""
    return {"status": "ok"}
