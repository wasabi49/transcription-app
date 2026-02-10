FROM python:3.11-slim

# ffmpeg インストール（音声デコードに必要）
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# uv インストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 依存関係のインストール（キャッシュ活用のため先にコピー）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# アプリケーションコード
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
