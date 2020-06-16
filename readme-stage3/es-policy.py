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
import sys
import boto3
import json
from requests_aws4auth import AWS4Auth
import requests
# create boto3 clients
esearch = boto3.client('es')
sts = boto3.client('sts')
awsAccountId = sts.get_caller_identity()['Account']
# set command line arguments
awsRegion = sys.argv[1]
trustedCidr = sys.argv[2]

def elasticsearch_policy_attachment():
    rawPolicy = {
        'Version': '2012-10-17',
        'Statement': [
            {
            'Action': 'es:*',
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/CTLogParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': 'es:*',
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/ALBLogParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': 'es:*',
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/APIGWParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': 'es:*',
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/FlowLogParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': 'es:*',
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/WAFLogParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': 'es:*',
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/SuricataParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': 'es:*',
            'Effect': 'Allow',
            'Principal': {
                'AWS': '*'
            },
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            'Condition': {'IpAddress': {'aws:SourceIp': trustedCidr} }
            }
        ]
    }
    try:
        response = esearch.update_elasticsearch_domain_config(DomainName='syntheticsun-es', AccessPolicies=json.dumps(rawPolicy))
        print(response)
    except Exception as e:
        print(e)
        raise


def main():
    elasticsearch_policy_attachment()

main()