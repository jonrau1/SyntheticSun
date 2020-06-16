# This file is part of SyntheticSun.

# SyntheticSun is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# SyntheticSun is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with SyntheticSun.  
# If not, see https://github.com/jonrau1/SyntheticSun/blob/master/LICENSE.
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