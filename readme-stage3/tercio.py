import boto3
import sys
import os
# create boto3 clients
sts = boto3.client('sts')
s3 = boto3.client('s3')
apigwv2 = boto3.client('apigatewayv2')
# create variables
awsAccountId = sts.get_caller_identity()['Account']
# input vars
awsRegion = sys.argv[1]
ctBucket = sys.argv[2]
albBucket = sys.argv[3]
wafBucket = sys.argv[4]
apiId = sys.argv[5]
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