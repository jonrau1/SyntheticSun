import boto3
import sys

publicSubnet = sys.argv[1]
sgId = sys.argv[2]

ecs = boto3.client('ecs')

def waf_training_grounds():
    try:
        response = ecs.run_task(
            count = 1,
            platformVersion = '1.4.0',
            launchType = 'FARGATE',
            cluster = 'SyntheticSun-Cluster',
            networkConfiguration = {
                'awsvpcConfiguration': {
                    'subnets': [publicSubnet],
                    'securityGroups': [sgId],
                    'assignPublicIp': 'ENABLED'
                }
            },
            taskDefinition='SyntheticSun-IPInsights-WAF-Trainer'
        )
        print(response)
    except Exception as e:
        print(e)
        raise

def ct_training_grounds():
    try:
        response = ecs.run_task(
            count = 1,
            platformVersion = '1.4.0',
            launchType = 'FARGATE',
            cluster = 'SyntheticSun-Cluster',
            networkConfiguration = {
                'awsvpcConfiguration': {
                    'subnets': [publicSubnet],
                    'securityGroups': [sgId],
                    'assignPublicIp': 'ENABLED'
                }
            },
            taskDefinition='SyntheticSun-IPInsights-CT-Trainer'
        )
        print(response)
    except Exception as e:
        print(e)
        raise

def taskmaster():
    waf_training_grounds()
    ct_training_grounds()

taskmaster()