# 採譜アプリ
- 楽曲ファイルからピアノ楽譜を生成するアプリ

## 機能概要
- mp3などの楽曲ファイルから楽譜に変換できる
- 楽譜をユーザーが選択した難易度に応じて簡略化できる
- 生成した楽譜をピアノで再生できる

## アーキテクチャ

```
[ユーザー] → MP3アップロード
     ↓
[Next.js Frontend]
     ↓ POST /api/transcribe (multipart + SSE)
[FastAPI Backend]
     ├→ Basic Pitch: MP3 → MIDI (note events)
     ├→ pretty_midi: 難易度フィルタリング
     ├→ music21: MIDI → MusicXML
     └→ SSEで進捗 + 結果を送出
     ↓
[Next.js Frontend]
     ├→ OSMD: MusicXML → 楽譜表示 (SVG)
     ├→ Tone.js + MIDI: ピアノ再生
     └→ 難易度変更 → POST /api/simplify（同期・高速）
```

## 技術スタック

| レイヤー | 技術 |
|---|---|
| バックエンド | FastAPI + uvicorn |
| 採譜エンジン | Basic Pitch (Spotify) |
| MIDI操作 | pretty_midi |
| 楽譜生成 | music21 → MusicXML |
| 依存管理 | uv + pyproject.toml |
| フロントエンド | Next.js 16 + React 19 + Tailwind CSS v4 |
| 状態管理 | zustand |
| 楽譜表示 | OpenSheetMusicDisplay (OSMD) |
| ピアノ再生 | Tone.js + サウンドフォント（セルフホスト） |
| 進捗通知 | SSE (Server-Sent Events) |
| CI/CD | GitHub Actions（テスト・リント・ビルド） |
| リンター (Python) | ruff |

## 採譜関連ライブラリ比較

### 採譜エンジン（音声 → MIDI）

| ライブラリ | 特徴 | モデル基盤 | サイズ | 精度 | 備考 |
|---|---|---|---|---|---|
| **Basic Pitch** (Spotify) ✅ | CPU対応、pip一発、汎用楽器対応 | TensorFlow Lite | ~1GB (TF含む) | ○ | 最終リリース2024年、更新頻度低下傾向 |
| piano_transcription_inference | ピアノ特化で高精度 | PyTorch | ~1.5GB (PyTorch含む) | ◎ | ピアノ以外は非対応 |
| Onsets and Frames (Magenta) | Google製、ピアノ特化 | TensorFlow | ~2GB | ◎ | セットアップが複雑、APIが低レベル |
| Whisper + 後処理 | 音声認識転用 | PyTorch | ~1.5GB | △ | 音楽採譜には不向き |

**選定: Basic Pitch** — CPU動作・導入容易性・汎用性のバランスが最も良い。Clean Architectureのポート経由で利用するため、精度不足時に piano_transcription_inference 等へ差し替え可能。

### MIDI操作

| ライブラリ | 特徴 | 用途 |
|---|---|---|
| **pretty_midi** ✅ | ノートイベントの操作APIがシンプル | フィルタリング・量子化・同時発音数制限 |
| midiutil | MIDI生成特化（読み込み不可） | MIDI新規作成のみ |
| mido | 低レベルMIDIメッセージ操作 | ノート単位の操作には冗長 |

**選定: pretty_midi** — ノート単位の操作（ピッチ・ベロシティ・時間のフィルタリング）に最適なAPI。難易度別簡略化処理に直接活用。

### 楽譜生成（MIDI → MusicXML）

| ライブラリ | 特徴 | 出力形式 |
|---|---|---|
| **music21** ✅ | MIT発の音楽学ライブラリ、理論的操作も可能 | MusicXML, MIDI, LilyPond |
| mingus | 音楽理論ライブラリ（楽譜出力は弱い） | MIDI, LilyPond |
| abjad | LilyPond特化の記譜ライブラリ | LilyPond (PDF) |

**選定: music21** — MusicXML出力に対応する唯一の実用的Pythonライブラリ。OSMDとの連携に必須。

### 楽譜表示（MusicXML → 画面描画）

| ライブラリ | 特徴 | バンドルサイズ | 備考 |
|---|---|---|---|
| **OSMD** ✅ | Web上でMusicXMLをSVG描画 | ~2MB (min) | 唯一の実用的OSS選択肢 |
| VexFlow | 低レベル楽譜描画（MusicXML非対応） | ~500KB | MusicXMLパースを自前実装する必要あり |
| abcjs | ABC記譜法専用 | ~300KB | MusicXML非対応 |

**選定: OSMD** — MusicXMLを直接表示できる唯一のOSSライブラリ。Next.jsでは `dynamic import` + `ssr: false` で遅延読み込み必須。

### ピアノ再生

| ライブラリ | 特徴 | 備考 |
|---|---|---|
| **Tone.js** ✅ | Web Audio APIの高レベルラッパー | デファクトスタンダード |
| **@tonejs/midi** ✅ | MIDIパーサー（Tone.js連携） | 最終更新が古いが機能は十分 |
| soundfont-player | サウンドフォント再生 | Tone.jsより機能が限定的 |

**選定: Tone.js + @tonejs/midi** — Web Audio APIのデファクト。ブラウザのAutoPlay制約により、再生ボタン押下時に `Tone.start()` を呼ぶUI設計が必須。

### SSEクライアント

| 方式 | 特徴 | 備考 |
|---|---|---|
| EventSource API | ブラウザ標準、自動再接続 | **GETのみ対応、POSTリクエストに使えない** |
| **fetch + ReadableStream** ✅ | POST対応、エラーハンドリングが柔軟 | 再接続ロジックは自前実装 |

**選定: fetch + ReadableStream** — `/api/transcribe` は POST（multipart）のためEventSourceは使用不可。fetchベースで実装。

## 決定事項

- 採譜エンジン: Basic Pitch（CPU対応、pip一発、Spotify製で信頼性高い）
- 楽譜フォーマット: MusicXML（OSMDとの互換性が最も高い）
- 進捗通知: SSE（採譜は一方向通知で十分、WebSocketより実装がシンプル）
- 難易度: 原曲 + 3段階の簡略化（上級→中級→初級の順に簡単に）
- 再生: フロントエンド（Tone.js + サウンドフォント）
- サウンドフォント: セルフホスト（public/ に配置、外部CDN非依存）
- 難易度変更API: 同期（元MIDIからの再計算は < 1秒で完了するため）
- 依存管理: uv + pyproject.toml
- 一時ファイル: リクエスト完了時に即削除（権利関係のリスク回避。サーバーにファイルを残さない）
- 状態管理: zustand（軽量でコンポーネント間のデータ共有が容易）
- 対応デバイス: PCのみ（モバイル対応は不要）
- バックエンド設計: Clean Architecture（ライブラリ差し替えが容易なPort/Adapter構成）
- CI/CD: GitHub Actionsでテスト・リント・ビルドの自動実行
- 同時採譜処理数: 1件（asyncio.Semaphoreで制御。メモリ~1GBのため同時実行は危険）
- 対応入力フォーマット: MP3 / WAV のみ
- CPU-bound処理: asyncio.to_thread() でイベントループをブロックしない
- SSEエラーイベント: `event: error` + `{ code, message }` 形式で送出
- ベース量子化: 全難易度共通の前処理としてonset/offsetを最近接の16分音符に量子化
- 環境変数: pydantic-settings で管理、.env.example を配置

## 難易度設計

| レベル | 内容 |
|---|---|
| 原曲 | Basic Pitchの出力そのまま |
| 上級 | 微細な装飾音・超短音符（32分音符以下）を除去、極端なベロシティの正規化 |
| 中級 | 同時発音数を制限（最大4音）、速いパッセージの間引き、オクターブ範囲制限 |
| 初級 | メロディ（最高音）＋ルート音のみ抽出、同時発音2音以下、簡素なリズムに量子化 |

※ 全レベル共通の前処理として、Basic Pitchの浮動小数点onset/offsetを最近接の16分音符に量子化する。

## API設計

### POST /api/transcribe
- Request: multipart/form-data { file: MP3/WAV, difficulty: "original"|"advanced"|"intermediate"|"beginner" }
- Response: SSEストリーム
  - 進捗イベント: `event: progress` + `{ step, progress_percent, message }`
  - 完了イベント: `event: complete` + `{ musicxml, midi_base64, metadata }`
  - エラーイベント: `event: error` + `{ code, message }`
- 同時処理制限: 1件（ビジー時は 503 Service Unavailable を返す）

### POST /api/simplify
- Request: { midi_base64: string, difficulty: string }
- Response: { musicxml: string, midi_base64: string }
- 同期API（< 1秒）

### GET /api/health
- Response: { status: "ok" }

## ディレクトリ構成

バックエンドはClean Architectureを採用。domain層は外部ライブラリに依存せず、
application層のPort（抽象インターフェース）を介してinfrastructure層のAdapter（具体実装）を利用する。
これによりBasic Pitch→別エンジン、music21→別ライブラリ等の差し替えが容易になる。

```
transcription-app/
├── docker-compose.yml
├── plan.md
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── main.py
│   ├── src/
│   │   ├── domain/               # ドメイン層（外部依存なし）
│   │   │   ├── entities.py        #   MidiData, SheetMusic, Difficulty 等の値オブジェクト
│   │   │   ├── transcription.py   #   採譜のビジネスルール（純粋ロジック）
│   │   │   └── simplification.py  #   難易度別簡略化のビジネスルール（純粋ロジック）
│   │   ├── application/           # ユースケース層
│   │   │   ├── ports/             #   Port（抽象インターフェース）
│   │   │   │   ├── transcriber.py  #     ABC: 音声→MIDI変換
│   │   │   │   ├── midi_processor.py #   ABC: MIDI加工
│   │   │   │   └── sheet_music_generator.py # ABC: MusicXML生成
│   │   │   └── usecases/          #   ユースケース（ポートを通じて処理を組み立て）
│   │   │       ├── transcribe_music.py
│   │   │       └── simplify_music.py
│   │   ├── infrastructure/        # インフラ層（外部ライブラリの具体実装）
│   │   │   ├── basic_pitch_transcriber.py  # Basic Pitch実装
│   │   │   ├── pretty_midi_processor.py    # pretty_midi実装
│   │   │   └── music21_generator.py        # music21実装
│   │   ├── api/                   # プレゼンテーション層
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   └── dependencies.py    # DIコンテナ（Port→Adapter の紐付け）
│   │   └── core/
│   │       ├── config.py
│   │       └── exceptions.py
│   └── tests/
│       ├── test_transcription.py
│       ├── test_simplification.py
│       ├── test_usecases.py
│       └── test_api.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── FileUpload.tsx
│   │   ├── SheetMusicViewer.tsx
│   │   ├── PianoPlayer.tsx
│   │   ├── DifficultySelector.tsx
│   │   └── ProcessingIndicator.tsx
│   ├── hooks/
│   │   ├── useTranscription.ts
│   │   └── usePianoPlayer.ts
│   ├── stores/
│   │   └── useAppStore.ts         # zustand ストア
│   ├── lib/
│   │   ├── api.ts
│   │   └── midi.ts
│   └── public/
```

## 実装ステップ

### Phase 1: バックエンド基盤
- [x] 1. `pyproject.toml` を作成（fastapi, uvicorn, python-multipart, basic-pitch, music21, pretty_midi, numpy, pydantic, ruff）
- [x] 2. `ffmpeg` のインストール確認（Basic PitchのMP3デコードに必須）
- [x] 3. `main.py` を拡充（CORS設定、APIRouter include、アップロードサイズ制限50MB、lifespan でBasic Pitchモデルプリロード、Semaphore初期化）
- [x] 4. `backend/src/core/config.py` — 設定管理（pydantic-settings、MAX_FILE_SIZE, ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES, CORS_ORIGINS等）
   `.env.example` — 環境変数テンプレート
- [x] 5. `backend/src/core/exceptions.py` — カスタム例外（TranscriptionError, InvalidFileError等）

### Phase 2: ドメイン層・ユースケース層
- [x] 6. `backend/src/domain/entities.py` — MidiData, Difficulty 等の値オブジェクト定義
- [x] 7. `backend/src/domain/transcription.py` — 採譜のビジネスルール（純粋ロジック、外部依存なし）
- [x] 8. `backend/src/domain/simplification.py` — 難易度別簡略化のビジネスルール（純粋ロジック）
- [x] 9. `backend/src/application/ports/` — 抽象インターフェース定義（Transcriber, MidiProcessor, SheetMusicGenerator）
- [x] 10. `backend/src/application/usecases/transcribe_music.py` — 採譜ユースケース（ポート経由で処理組み立て）
- [x] 11. `backend/src/application/usecases/simplify_music.py` — 簡略化ユースケース

### Phase 3: インフラ層（外部ライブラリ実装）
- [x] 12. `backend/src/infrastructure/basic_pitch_transcriber.py` — Transcriberポートの実装
- [x] 13. `backend/src/infrastructure/pretty_midi_processor.py` — MidiProcessorポートの実装
- [x] 14. `backend/src/infrastructure/music21_generator.py` — SheetMusicGeneratorポートの実装

### Phase 4: API層
- [x] 15. `backend/src/api/dependencies.py` — DIコンテナ（Port → Adapter の紐付け）
- [x] 16. `backend/src/api/schemas.py` — Pydanticモデル定義
- [x] 17. `backend/src/api/router.py` — SSE採譜エンドポイント + 難易度変更エンドポイント（ファイルバリデーション・レート制限含む）

### Phase 5: フロントエンド基盤
- [x] 18. パッケージ追加（opensheetmusicdisplay, tone, @tonejs/midi, zustand）
- [x] 19. `frontend/stores/useAppStore.ts` — zustandストア（採譜状態・再生状態・難易度の管理）
- [x] 20. `frontend/lib/api.ts` — SSEクライアント（fetch + ReadableStreamベース、切断時のリカバリ含む）
- [x] 21. `frontend/lib/midi.ts` — Base64 MIDI デコード・パース

### Phase 6: フロントエンドUIコンポーネント
- [x] 22. `frontend/components/FileUpload.tsx` — ドラッグ&ドロップアップロード
- [x] 23. `frontend/components/SheetMusicViewer.tsx` — OSMD楽譜表示
- [x] 24. `frontend/components/PianoPlayer.tsx` — Tone.jsピアノ再生（ユーザー操作でAudioContext起動）
- [x] 25. `frontend/components/DifficultySelector.tsx` — 難易度切替（原曲/上級/中級/初級）
- [x] 26. `frontend/components/ProcessingIndicator.tsx` — SSE進捗表示
- [x] 27. `frontend/app/page.tsx` — メインページ統合

### Phase 7: インフラ・仕上げ
- [x] 28. Docker構成（docker-compose.yml + 各Dockerfile、ffmpegインストール含む）
- [x] 29. テスト（pytest によるユニットテスト + ユースケーステスト + API統合テスト）
- [x] 30. CI/CD（GitHub Actions: ruff lint/format, pytest, next build）

## 検証方法

- `uv sync && uv run uvicorn main:app --reload` でバックエンド起動確認
- `curl -X POST http://localhost:8000/api/health` で疎通確認
- 短いMP3（10秒程度のピアノ曲）で `POST /api/transcribe` のSSEイベント受信を確認
- フロントエンドでMP3アップロード → 楽譜表示 → 再生 → 難易度切替の一連フローを手動テスト
- `pytest backend/tests/` で自動テスト通過

## リスクと対策

| リスク | 影響 | 対策 |
|---|---|---|
| 採譜精度（複雑な和音で誤検出） | 高 | ピアノソロ曲に絞る、後処理で音楽理論的整合性チェック |
| 処理時間（CPU環境で30-90秒） | 高 | SSEで進捗表示、GPU環境なら10-20秒に短縮 |
| メモリ使用量（モデルで~500MB-1GB） | 中 | ワーカー数制限、モデルのシングルトン管理、同時採譜1件制限（Semaphore） |
| 簡略化の音楽的品質 | 中 | 和声進行の維持・リズムパターン保持ルールを組み込む |
| OSMDの大規模楽譜表示性能 | 中 | ページネーションまたは遅延レンダリング |
| 権利関係（アップロード楽曲のサーバー保存） | 高 | 一時ファイルはリクエスト完了時に即削除、サーバーに残さない |
| 悪意あるファイルアップロード | 中 | MIMEタイプ検証 + マジックバイト確認 + ファイル名サニタイズ |
| DoS的な大量リクエスト | 中 | slowapi によるレート制限 |
| SSE切断・ネットワーク断 | 中 | フロントエンドで再接続ロジックを実装 |
| コールドスタート（モデル初回ロード遅延） | 低 | FastAPI lifespan でアプリ起動時にモデルプリロード |

## セキュリティ対策

| 対策 | 実装 |
|---|---|
| ファイルバリデーション | 拡張子チェック + MIMEタイプ検証 + ファイルヘッダー（マジックバイト）確認 |
| ファイル名サニタイズ | パストラバーサル防止のためアップロードファイル名を正規化 |
| レート制限 | slowapi で採譜APIに制限（例: 1分あたり3リクエスト） |
| 一時ファイル即削除 | リクエスト処理完了後にアップロード・生成ファイルを即時削除 |
| アップロードサイズ制限 | 50MB上限 |
| CORS設定 | フロントエンドオリジンのみ許可 |

## CI/CD

### GitHub Actions ワークフロー (.github/workflows/ci.yml)

**トリガー**: push / pull_request（main ブランチ）

**バックエンド ジョブ**:
1. `ruff check` — リント
2. `ruff format --check` — フォーマット確認
3. `pytest` — ユニットテスト + 統合テスト

**フロントエンド ジョブ**:
1. `npm ci` — 依存インストール
2. `eslint` — リント
3. `next build` — ビルド確認