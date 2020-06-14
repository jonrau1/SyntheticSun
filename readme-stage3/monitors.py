import boto3
import json
import time
# create boto3 clients
sts = boto3.client('sts')
sns = boto3.client('sns')
iam = boto3.client('iam')
# create variables
awsRegion = boto3.Session().region_name
awsAccountId = sts.get_caller_identity()['Account']

try:
    response = sns.create_topic(
        Name='es-monitor-vpc-rcf',
        Attributes={
            'KmsMasterKeyId': 'alias/aws/sns',
            'DisplayName': 'es-monitor-vpc-rcf'
        }
    )
    print('Created VPC Flow log SNS topic')
except Exception as e:
    print(e)
    raise

try:
    response = sns.create_topic(
        Name='es-monitor-alb-rcf',
        Attributes={
            'KmsMasterKeyId': 'alias/aws/sns',
            'DisplayName': 'es-monitor-alb-rcf'
        }
    )
    print('Created ALB SNS topic')
except Exception as e:
    print(e)
    raise

trustPolicy = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "es.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}

vpcSnsArn = 'arn:aws:sns:' + awsRegion + ':' + awsAccountId + ':es-monitor-vpc-rcf'
print('Your VPC RCF SNS Topic is ' + vpcSnsArn)
albSnsArn = 'arn:aws:sns:' + awsRegion + ':' + awsAccountId + ':es-monitor-alb-rcf'
print('Your ALB RCF SNS Topic is ' + albSnsArn)

snsPolicy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "sns:Publish"
            ],
            "Effect": "Allow",
            "Resource": [
                vpcSnsArn,
                albSnsArn
            ]
        }
    ]
}

try:
    response = iam.create_role(
        RoleName='ES-Monitor-SNS',
        AssumeRolePolicyDocument=json.dumps(trustPolicy),
        Description='Allows Elasticsearch Service monitors to send messages to SNS'
    )
    print('ES IAM Role created')
except Exception as e:
    print(e)
    raise

time.sleep(7)

try:
    response = iam.put_role_policy(
        RoleName='ES-Monitor-SNS',
        PolicyName='ES-Monitor-SNS-Policy',
        PolicyDocument=json.dumps(snsPolicy)
    )
    print('Policy attached to role')
except Exception as e:
    print(e)
    raise

iamArn = 'arn:aws:iam::' + awsAccountId + ':role/ES-Monitor-SNS'

time.sleep(2)

print('Your IAM Role for ES Monitors is ' + iamArn)