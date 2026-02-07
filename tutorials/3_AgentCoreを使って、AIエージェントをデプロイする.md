# 3_AgentCoreを使って、AIエージェントをデプロイする

## このセクションの概要

本セクションでは、前手順で作成した AI エージェントを AWS にデプロイし、テスト実行する。
基盤には Amazon Bedrock AgentCore Runtime を採用し、AWS CDK を使ってデプロイする。

## 3.1. デプロイ用ツールのインストール

### node のインストール

**PC に node が入っていない方のみ、本手順を実施して下さい**

今回は AWS CDK を使う為、node.js が必要。
uv で python のバージョンを管理するように、node.js でもバージョン管理は重要。

今回は、nvm を使って node をインストールしていく。

- nvm: <https://github.com/nvm-sh/nvm>

**windows の場合**:

1. [リリースノート](https://github.com/coreybutler/nvm-windows/releases)から最新のインストーラをダウンロード
2. インストーラを実行

- 参考手順: <https://zenn.dev/keison8864/articles/nvm-windows-nodejs-install>

**Linux/macOS の場合**:

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
```

- 参考手順: <https://github.com/nvm-sh/nvm>

**共通手順**:

インストール出来たか確認

```bash
nvm --version
```

最新の node をインストール

```bash
nvm install node
```

node のインストール確認

```
node --version
```

バージョンが表示されれば、node のインストールは完了

### ライブラリをインストール

AgentCore を使う為のライブラリを追加する。

```bash
# 現在のディレクトリを確認
pwd
# hamazlabo-developing-ai-agent/agents/lib/app

uv add bedrock-agentcore bedrock-agentcore-starter-toolkit
```

## 3.2. デプロイ準備

### Strands Agents のコードを AgentCore 用に修正

Fast API で動作する Strands Agents のコードを、AgentCore 対応に修正する。
以下を全てコピーし、sample_agent.py の中に貼り付ける。

```py
import argparse
import json

from strands import Agent
from strands.models import BedrockModel

from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

from datetime import datetime
from tools.weather_forecast import get_weather_forecast

from bedrock_agentcore.runtime import BedrockAgentCoreApp # AgentCoreライブラリを追加

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
    now = datetime.now()
    system_prompt = SYSTEM_PROMPT + f"""
    現在の時刻: {now}
    """

    bedrock_model = BedrockModel(
        model_id=MODEL_ID,
        region_name="us-west-2"
    )

    # AgentCore Memory を設定
    agentcore_memory_config = AgentCoreMemoryConfig(
        memory_id=MEM_ID,
        session_id=SESSION_ID,
        actor_id=ACTOR_ID,
        retrieval_config={
            "/preferences/{actorId}": RetrievalConfig(
                top_k=5,
                relevance_score=0.7
            ),
            "/facts/{actorId}": RetrievalConfig(
                top_k=10,
                relevance_score=0.3
            ),
            "/summaries/{actorId}/{sessionId}": RetrievalConfig(
                top_k=5,
                relevance_score=0.5
            )
        }
    )

    # セッションマネージャを定義
    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=agentcore_memory_config,
        region_name="us-west-2"
    )

    agent = Agent(
        model=bedrock_model,
        system_prompt=system_prompt,
        session_manager=session_manager,
        tools=[get_weather_forecast]
    )

    prompt = payload.get("prompt")
    response = agent(prompt)
    return response.message['content'][0]['text']

# 実行関数を変更
if __name__ == "__main__":
    app.run()
```

### Dockerfile を追加

hamazlabo-developing-ai-agent/agents/lib/app 直下に Dockerfile を作成し、以下の内容をそのままコピーペースト。

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# All environment variables in one layer
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=us-west-2 \
    AWS_DEFAULT_REGION=us-west-2

COPY . .
# Install from pyproject.toml directory
RUN cd . && uv pip install .

RUN uv pip install aws-opentelemetry-distro==0.12.2

# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

# Copy entire project (respecting .dockerignore)
COPY . .

# Use the full module path

CMD ["opentelemetry-instrument", "python", "-m", "sample_agent"]
```

AgentCore Runtime を AWS CDK でデプロイする為に必要になる。

## 3.3. エージェントをデプロイ

AWS CDK を使って、AgentCore 一式をデプロイする。
AI エージェントを AgentCore Runtime にデプロイする為には、ざっくり3通りの手順がある。

1. スターターツールキットを利用する
2. ECR リポジトリからデプロイする
3. ソースコードを zip 化してデプロイする

1は簡単だが、本番に組み込むには不向き。
2は CI/CD と組み合わせて本番にも使えるが、準備が煩雑。
3は手軽で本番にも使えるが、ソースコードを zip 化する時、ARM でビルドされたライブラリを使う必要がある。

そこで今回は、**deploy-time-build** というサードパーティツールを利用して、2の「ECR リポジトリからデプロイ」する。

### deploy-time-build のアーキテクチャ

deploy-time-build (ContainerImageBuild) は、以下の流れで Docker イメージをビルド・デプロイする。

![deploy-time-build アーキテクチャ](./images/03_deploy_time_build_architecture.svg)

| ステップ | 処理内容 |
|---------|---------|
| 1. Upload assets | `cdk deploy` 実行時、Dockerfile とソースコードを zip 化して S3 にアップロード |
| 2. Fetch | AWS CodeBuild が S3 からアセットを取得 |
| 3. Push image | CodeBuild が ARM64 アーキテクチャで Docker イメージをビルドし、ECR にプッシュ |
| 4. Pull & Deploy | AgentCore Runtime が ECR からイメージを取得してデプロイ |

この仕組みにより、ローカル環境に Docker がインストールされていなくても、AWS 上でコンテナイメージをビルドできる。
また、ARM64 (Graviton) 向けのイメージを x86 環境からでもビルド可能になる。

> **参考**: [deploy-time-build (GitHub)](https://github.com/tmokmss/deploy-time-build)

### AWS CDK のルートディレクトリへ移動

agents ディレクトリ直下にいる事を確認。

```bash
pwd

# hamazlabo-developing-ai-agent/agents
```

もしいなければ、cd コマンドを使って /agents 配下へ移動。

### ライブラリをインストール

```bash
npm install
```

### (初めて AWS CDK を実行する場合)AWS CDK をセットアップ

AWS CDK を利用する際、事前に CDK が使う IAM ロールや環境変数(のようなもの)を AWS 上に作成しておく必要がある。

以下コマンドは、それらを AWS アカウントに作成する。

```bash
npx cdk bootstrap
```

各 AWS 環境で一度だけ実行しておけばよい。

### CFn テンプレート生成

typescript で書かれたテンプレートを、CFn に変換する。

```bash
npx cdk synth
```

実行後、cdk.out フォルダを確認すると CFn テンプレートが生成されているのを確認出来る。

### ECR リポジトリ作成

EcrStack をデプロイ。

```bash
npx cdk deploy EcrStack
```

### AgentCore Runtime デプロイ

AgentStack をデプロイ。

```bash
npx cdk deploy AgentStack
```

## 3.4. AgentCore をテスト実行

### デプロイした AgentCore Runtime を実行

```sh
agentcore invoke '{"sessionId": "52433935-c9fd-480c-e3d2-d8a91369b3db", "prompt": "今日の横浜の天気を教えて下さい。"}'
```
