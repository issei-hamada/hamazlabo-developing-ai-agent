import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as agentcore from '@aws-cdk/aws-bedrock-agentcore-alpha';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';

export class AgentStack extends cdk.Stack {
  public readonly agent: agentcore.Runtime;
  public readonly memory: agentcore.Memory;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const account = cdk.Stack.of(this).account;
    const region = cdk.Stack.of(this).region;

    /**
     * AgentCore Memory
     */
    this.memory = new agentcore.Memory(this, "Memory", {
      memoryName: "sample_memory",
      memoryStrategies: [
        agentcore.MemoryStrategy.usingSummarization({
          name: "SummarizationStorategy",
          description: "Summarization memory strategy",
          namespaces: ["/strategies/summaries/actors/{actorId}/session/{sessionId}"],
        }),
        agentcore.MemoryStrategy.usingSemantic({
          name: "SemanticStorategy",
          description: "Semantic memory strategy",
          namespaces: ["/strategies/semantic/actors/{actorId}"],
        }),
        agentcore.MemoryStrategy.usingUserPreference({
          name: "UserPreferenceStorategy",
          description: "UserPreference memory strategy",
          namespaces: ["/strategies/preferences/actors/{actorId}"],
        }),
      ],
      expirationDuration: cdk.Duration.days(90),
    });

    /**
     * IAM Role
     */
    const runtimeRole = new iam.Role(this, 'RuntimeRole', {
      assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com'),
      ),
      description: 'IAM role for AgentCore',
    });

    // ECRイメージアクセス権限
    runtimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['ecr:BatchGetImage', 'ecr:GetDownloadUrlForLayer'],
        resources: [`arn:aws:ecr:${region}:${account}:repository/*`],
      })
    );

    // ECRトークンアクセス権限
    runtimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['ecr:GetAuthorizationToken'],
        resources: ['*'],
      })
    );

    // CloudWatch Logs権限
    runtimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['logs:DescribeLogGroups'],
        resources: [`arn:aws:logs:${region}:${account}:log-group:*`],
      })
    );

    runtimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
        resources: [
          `arn:aws:logs:${region}:${account}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*`,
        ]
      })
    );

    // X-Ray権限
    runtimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'xray:GetSamplingRules',
          'xray:GetSamplingTargets',
          'xray:PutTelemetryRecords',
          'xray:PutTraceSegments',
        ],
        resources: ['*'],
      })
    );

    // CloudWatch メトリクス権限
    runtimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['cloudwatch:PutMetricData'],
        resources: ['*'],
        conditions: {
          StringEquals: {
            'cloudwatch:namespace': 'bedrock-agentcore',
          },
        },
      })
    );

    // AgentCore Memory 権限
    runtimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'bedrock-agentcore:CreateEvent',
          'bedrock-agentcore:ListEvents',
          'bedrock-agentcore:ListSessions',
        ],
        resources: [
          this.memory.memoryArn
        ],
      })
    );

    // Bedrockモデル呼び出し権限
    runtimeRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
        resources: ['*'],
      })
    );

    // CloudWatch Logs ロググループ (AgentCore Runtime 用)
    new logs.LogGroup(this, 'RuntimeLogGroup', {
      logGroupName: `/aws/bedrock-agentcore/runtimes/sample_agent`,
      retention: logs.RetentionDays.THREE_MONTHS,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // リポジトリ取得
    const repository = ecr.Repository.fromRepositoryName(this, 'Repository', "sample_agent");

    // AgentCore Runtime の作成
    this.agent = new agentcore.Runtime(this, "Runtime", {
      runtimeName: "sample_agent",
      executionRole: runtimeRole,
      agentRuntimeArtifact: agentcore.AgentRuntimeArtifact.fromEcrRepository(repository), // ECR のリポジトリを指定
      environmentVariables: {
        MEMORY_ID: this.memory.memoryId,
      },
    });
  }
}
