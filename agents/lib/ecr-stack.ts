import * as cdk from 'aws-cdk-lib';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import { Construct } from 'constructs';

import { ContainerImageBuild } from 'deploy-time-build';
import * as path from 'path';

export class EcrStack extends cdk.Stack {
  public readonly repository: ecr.Repository;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ECRリポジトリを作成
    this.repository = new ecr.Repository(this, 'Repository', {
      repositoryName: "sample_agent",
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      emptyOnDelete: true,
    });

    // ARM64アーキテクチャでDockerイメージをビルドしてECRにプッシュ
    new ContainerImageBuild(this, 'AgentImage', {
      directory: path.join(__dirname, './app'),
      platform: Platform.LINUX_ARM64,
      zstdCompression: true,
      repository: this.repository,
      tag: 'latest',
      exclude: ['.venv', 'tests', 'README.md']
    });
  }
}
