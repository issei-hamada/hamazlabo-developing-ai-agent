import argparse
import json

import boto3


def get_agent_runtime_arn() -> str:
    """AgentStack の CfnOutput から AgentRuntimeArn を取得する"""
    cfn = boto3.client("cloudformation")
    resp = cfn.describe_stacks(StackName="AgentStack")
    for output in resp["Stacks"][0]["Outputs"]:
        if output["OutputKey"] == "AgentRuntimeArn":
            return output["OutputValue"]
    raise RuntimeError("AgentRuntimeArn not found in AgentStack outputs")


def invoke_agent(actor_id: str, session_id: str, prompt: str) -> None:
    agent_runtime_arn = get_agent_runtime_arn()

    payload = {
        "prompt": prompt,
        "sessionId": session_id,
        "actorId": actor_id,
    }

    client = boto3.client("bedrock-agentcore")
    response = client.invoke_agent_runtime(
        agentRuntimeArn=agent_runtime_arn,
        contentType="application/json",
        payload=json.dumps(payload),
    )

    # Process and print the response
    if "text/event-stream" in response.get("contentType", ""):
    
        # Handle streaming response
        content = []
        for line in response["response"].iter_lines(chunk_size=10):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    print(line)
                    content.append(line)
        print("\nComplete response:", "\n".join(content))

    elif response.get("contentType") == "application/json":
        # Handle standard JSON response
        body = response["response"].read().decode("utf-8")
        print(json.loads(body))
    
    else:
        # Print raw response for other content types
        print(response)

def main():
    parser = argparse.ArgumentParser(description="Invoke AgentCore Runtime")
    parser.add_argument("--actor-id", required=True, help="Actor ID (ACTOR_ID)")
    parser.add_argument("--session-id", required=True, help="Session ID (SESSION_ID)")
    parser.add_argument("--prompt", required=True, help="エージェントに送るプロンプト")
    args = parser.parse_args()

    invoke_agent(args.actor_id, args.session_id, args.prompt)


if __name__ == "__main__":
    main()
