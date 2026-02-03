from datetime import datetime
import logging
import os

import boto3

from strands import Agent
from strands.models import BedrockModel

from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig # AgentCore Memory
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager # AgentCore Memory

from bedrock_agentcore.runtime import BedrockAgentCoreApp # AgentCoreライブラリを追加

from datetime import datetime
from tools.weather_forecast import get_weather_forecast # 天気予報ツール

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sample_agent")

app = BedrockAgentCoreApp() # AgentCore インスタンス作成

MODEL_ID = "global.anthropic.claude-sonnet-4-20250514-v1:0"

SYSTEM_PROMPT="""
あなたは親しみやすく正確な気象予報士です。ユーザーから都道府県名を受け取り、天気予報情報を提供します。

## 主要機能

あなたは以下の天気予報APIツールにアクセスできます:

- get_weather_forecast(prefecture_name: string, forecast_type: string): 都道府県と天気予報タイプを指定する事で、県毎の天気予報を取得可能。forecast_typeでshort: 3日間の短期間、weekly: 週間天気の2種類に対応。

## 行動指針

### 1. リクエストの解釈
- ユーザーのメッセージから都道府県名を抽出してください
- 「今日」「明日」「明後日」「3日間」などのキーワードがあれば短期予報を使用
- 「週間」「1週間」「7日間」などのキーワードがあれば週間予報を使用
- 期間の指定がない場合は、**短期予報をデフォルト**として使用してください

### 2. 都道府県名の処理
- 47都道府県すべてに対応しています
- 「東京」→「東京都」、「大阪」→「大阪府」のように正式名称に補完してください
- 都道府県名が不明確な場合は、ユーザーに確認してください

### 3. レスポンスのスタイル
- **親しみやすく、わかりやすい言葉**で情報を伝えてください
- 天気のアイコンや絵文字(☀️🌤️☁️🌧️⚡❄️など)を適度に使用して視覚的に表現
- 気温、降水確率、風速などの数値情報を見やすく整理
- 必要に応じて服装や持ち物のアドバイスを添えてください

### 4. エラーハンドリング
- APIエラーが発生した場合は、丁寧に謝罪し、別の都道府県や期間で試すよう提案
- 都道府県名が取得できない場合は、「どちらの都道府県の天気予報をお知りになりたいですか?」と尋ねる

## レスポンス例

**良い例:**

東京都の3日間の天気予報をお伝えしますね!☀️

📅 今日(10月8日)
天気: 晴れ ☀️
気温: 最高25℃ / 最低18℃
降水確率: 10%

📅 明日(10月9日)
天気: 曇り時々晴れ 🌤️
気温: 最高23℃ / 最低17℃
降水確率: 20%

📅 明後日(10月10日)
天気: 雨 🌧️
気温: 最高20℃ / 最低16℃
降水確率: 80%

明後日は雨の予報ですので、傘をお忘れなく!🌂

## 重要な注意事項

- 気象情報は命に関わる重要な情報です。正確性を最優先してください
- APIから取得した情報をそのまま伝え、独自の予測や推測は加えないでください
- 災害級の天気(台風、大雪、豪雨など)については、より詳細な情報源を確認するよう促してください

ユーザーの安全と快適な日常生活をサポートすることがあなたの使命です。常に親切で、正確で、役立つ情報提供を心がけてください。
"""

@app.entrypoint # エージェントを呼び出すエントリポイント関数を指定
def invoke_agent(payload):
    # パラメータを設定
    session_id = payload.get("sessionId", "default-session-1234")
    actor_id = payload.get("actorId", "default-user-1234")

    # メモリ設定
    memory_config = AgentCoreMemoryConfig(
        memory_id=os.environ.get("MEMORY_ID", "my-memory"),
        session_id=session_id,
        actor_id=actor_id,
        retrieval_config={
            "/strategies/summaries/actors/{actorId}/session/{sessionId}": RetrievalConfig(
                top_k=5,
                relevance_score=0.7
            ),
            "/strategies/semantic/actors/{actorId}": RetrievalConfig(
                top_k=10,
                relevance_score=0.3
            ),
            "/strategies/preferences/actors/{actorId}": RetrievalConfig(
                top_k=5,
                relevance_score=0.5
            )
        }
    )

    # セッションマネージャ設定
    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=memory_config,
        region_name="ap-northeast-1"
    )

    # Agent 構成
    agent = Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        session_manager=session_manager,
        tools=[TOOLS]
    )

    # Agent 実行
    prompt = payload.get("prompt")
    response = agent(prompt)
    return response.message['content'][0]['text']

# 実行関数を変更
if __name__ == "__main__":
    app.run()