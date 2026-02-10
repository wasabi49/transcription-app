"""Pydantic モデル定義

APIリクエスト/レスポンスのスキーマを定義する。
"""

from pydantic import BaseModel, Field

from src.domain.entities import Difficulty


class SimplifyRequest(BaseModel):
    """難易度変更リクエスト"""

    midi_base64: str = Field(..., description="Base64エンコードされた元MIDIデータ")
    difficulty: Difficulty = Field(..., description="目標の難易度")


class SimplifyResponse(BaseModel):
    """難易度変更レスポンス"""

    musicxml: str = Field(..., description="MusicXML文字列")
    midi_base64: str = Field(..., description="Base64エンコードされた簡略化後MIDIデータ")
    metadata: "MetadataResponse" = Field(..., description="メタデータ")


class MetadataResponse(BaseModel):
    """メタデータレスポンス"""

    duration_seconds: float = Field(..., description="楽曲の長さ（秒）")
    note_count: int = Field(..., description="ノート数")
    tempo: float = Field(..., description="テンポ（BPM）")
    difficulty: Difficulty = Field(..., description="難易度")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""

    status: str = "ok"


class ErrorResponse(BaseModel):
    """エラーレスポンス"""

    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")
