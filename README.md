# SentBot

Discordの文章から感情分析を行い、必要な時に低速モードへ移行するBotです。

## 機能
- Discordの文章を監視し、文脈に基づいた感情分析（Groq API / Llama 3.1）を実行
- 荒れの予兆を検知した場合、チャンネルを自動で低速モードに設定
- スラッシュコマンドによる設定変更・状態表示
- 監視状態の永続化（再起動時も引き継ぎ）

## 開発環境
- Python 3.12
- uv
- Docker

## セットアップ

### local
1. `.env.example` を `.env` にコピーし、必要事項を記入してください。
2. `uv sync` で依存関係をインストールします。
3. `uv run sentbot` で起動します。

### docker
`docker compose up`で起動します。

## スラッシュコマンド
- `/toggle <channel_id/all> <enable/disable>`
    - 特定のチャンネルまたはBot全体（`all`）の監視を有効/無効にします。
- `/status`
    - 現在の監視状況（全体設定および個別設定チャンネル数）を表示します。
- `/set_slowmode <seconds>`
    - 低速モードの秒数を設定します。
