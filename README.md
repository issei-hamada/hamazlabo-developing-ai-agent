# hamazlabo-developing-ai-agent

## 概要

本ワークショップは、Strands Agents で AI エージェントを実装し、Amazon Bedrock AgentCore Runtime でのデプロイを体験します。
Strands Agents の基本的な使い方、AgentCore との連携、AWS CDK でデプロイする時のポイントを学ぶことが出来ます。

## 学べる事

- Python を使った基本的な開発環境の設定
- Strands Agents の基本
- Amazon Bedrock AgentCore Runtime/Memory の基本
- AWS CDK の初歩

## 前提条件

- Administrator 権限で操作できる AWS アカウント
  - AWS CDK を利用する為、Admin に近い権限が必要

- クライアント側に AWS CLI を利用する為の認証情報を設定済みである事
  - 例: AK/SK、AWS SSO 他

### codespace を使う場合

GitHub Codespace を使う場合、AWS CLI のインストールが必要です。

**AWS CLI のインストール手順**:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**認証情報の取得**:

GitHub Codespace から aws login コマンドを利用して AWS SDK を実行する際、boto3 に追加ライブラリが必要です。

```bash
uv add botocore[crt]
```

**AWS 認証情報を取得**:

以下コマンドを入力し、表示された URL をブラウザに入力する。

```bash
aws login --remote
```