# tests

AgentCore Runtime のテストスクリプト。

## test_invoke_agent.py

デプロイ済みの AgentCore Runtime にリクエストを送り、ストリーミングレスポンスを表示する。

### 前提条件

- `AgentStack` がデプロイ済みであること
- AWS 認証情報が設定されていること
- `boto3` がインストールされていること

### 引数

| 引数 | 必須 | 説明 |
|------|------|------|
| `--actor-id` | Yes | ユーザーを識別する Actor ID (payload の `actorId` に対応) |
| `--session-id` | Yes | セッション ID (payload の `sessionId` に対応) |
| `--prompt` | Yes | エージェントに送るプロンプト (payload の `prompt` に対応) |

### 実行例

```bash
uv run python tests/test_invoke_agent.py \
  --actor-id "user-001" \
  --session-id "52433935-c9fd-480c-e3d2-d8a91369b3db" \
  --prompt "今日の横浜の天気を教えて下さい。"
```
