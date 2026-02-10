"""アプリケーション設定管理"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """環境変数ベースの設定"""

    # サーバー設定
    app_name: str = "Transcription App API"
    debug: bool = False

    # CORS設定
    cors_origins: list[str] = ["http://localhost:3000"]

    # アップロード設定
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: set[str] = {".mp3", ".wav"}
    allowed_mime_types: set[str] = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/wave",
        "audio/x-wav",
    }

    # レート制限
    rate_limit: str = "3/minute"

    # 同時処理制限
    max_concurrent_transcriptions: int = 1

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
