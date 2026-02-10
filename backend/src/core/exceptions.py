"""カスタム例外定義"""


class TranscriptionAppError(Exception):
    """アプリケーション基底例外"""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class InvalidFileError(TranscriptionAppError):
    """無効なファイルアップロード"""

    def __init__(self, message: str = "無効なファイルです"):
        super().__init__(message=message, code="INVALID_FILE")


class FileTooLargeError(TranscriptionAppError):
    """ファイルサイズ超過"""

    def __init__(self, message: str = "ファイルサイズが上限を超えています"):
        super().__init__(message=message, code="FILE_TOO_LARGE")


class TranscriptionError(TranscriptionAppError):
    """採譜処理エラー"""

    def __init__(self, message: str = "採譜処理中にエラーが発生しました"):
        super().__init__(message=message, code="TRANSCRIPTION_ERROR")


class SimplificationError(TranscriptionAppError):
    """簡略化処理エラー"""

    def __init__(self, message: str = "簡略化処理中にエラーが発生しました"):
        super().__init__(message=message, code="SIMPLIFICATION_ERROR")


class ServiceBusyError(TranscriptionAppError):
    """同時処理上限到達"""

    def __init__(self, message: str = "サーバーがビジーです。しばらく待ってから再試行してください"):
        super().__init__(message=message, code="SERVICE_BUSY")
