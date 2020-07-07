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
# set your profile
profileName = sys.argv[1]
session = boto3.Session(profile_name=profileName)
# create boto3 clients
sts = boto3.client('sts')
s3 = session.client('s3')
apigwv2 = session.client('apigatewayv2')
# create variables
awsAccountId = sts.get_caller_identity()['Account']
# input vars
awsRegion = sys.argv[2]
ctBucket = sys.argv[3]
albBucket = sys.argv[4]
wafBucket = sys.argv[5]
apiId = sys.argv[6]
# dynamic vars
ctFunctionArn = 'arn:aws:lambda:' + awsRegion + ':' + awsAccountId + ':function:SyntheticSun-CTLogParserLambda'
albFunctionArn = 'arn:aws:lambda:' + awsRegion + ':' + awsAccountId + ':function:SyntheticSun-ALBLogParserLambda'
wafFunctionArn = 'arn:aws:lambda:' + awsRegion + ':' + awsAccountId + ':function:SyntheticSun-WAFLogParserLambda'
apiLogsArn = 'arn:aws:logs:' + awsRegion + ':' + awsAccountId + ':log-group:APIGWLogGrp:*'
# JSON APIGW access logs
logCsv = '{ "requestId":"$context.requestId", "ip": "$context.identity.sourceIp", "requestTimeEpoch":"$context.requestTimeEpoch", "httpMethod":"$context.httpMethod","routeKey":"$context.routeKey", "status":"$context.status","protocol":"$context.protocol", "responseLength":"$context.responseLength", "domainName":"$context.domainName", "userAgent": "$context.identity.userAgent" }'

def cloudtrail_event_attachment():
    try:
        response = s3.put_bucket_notification_configuration(
            Bucket=ctBucket,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': ctFunctionArn,
                        'Events': ['s3:ObjectCreated:*']
                    }
                ]
            }
        )
        print('S3 Event attached to CloudTrail bucket')
    except Exception as e:
        print(e)
        raise

def alb_event_attachment():
    try:
        response = s3.put_bucket_notification_configuration(
            Bucket=albBucket,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': albFunctionArn,
                        'Events': ['s3:ObjectCreated:*']
                    }
                ]
            }
        )
        print('S3 Event attached to ALB bucket')
    except Exception as e:
        print(e)
        raise

def waf_event_attachment():
    try:
        response = s3.put_bucket_notification_configuration(
            Bucket=wafBucket,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': wafFunctionArn,
                        'Events': ['s3:ObjectCreated:*']
                    }
                ]
            }
        )
        print('S3 Event attached to WAF bucket')
    except Exception as e:
        print(e)
        raise

def apigw_logs():
    try:
        response = apigwv2.update_stage(
            AccessLogSettings={
                'DestinationArn': apiLogsArn,
                'Format': str(logCsv)
            },
            ApiId=apiId,
            AutoDeploy=True,
            StageName='$default'
        )
        print('APIGW Logging has been updated')
    except Exception as e:
        print(e)
        raise

def pike_n_shot():
    cloudtrail_event_attachment()
    alb_event_attachment()
    waf_event_attachment()
    apigw_logs()

pike_n_shot()