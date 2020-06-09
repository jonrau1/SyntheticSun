import boto3
import sys

publicSubnet = sys.argv[1]
sgId = sys.argv[2]

ecs = boto3.client('ecs')

try:
    response = ecs.run_task(
        count = 1,
        platformVersion = 'LATEST',
        launchType = 'FARGATE',
        cluster = 'SyntheticSun-Cluster',
        networkConfiguration = {
            'awsvpcConfiguration': {
                'subnets': [publicSubnet],
                'securityGroups': [sgId],
                'assignPublicIp': 'ENABLED'
            }
        },
        taskDefinition='SyntheticSun-IPInsights-Trainer'
    )
    print(response)
except Exception as e:
    print(e)
    raise