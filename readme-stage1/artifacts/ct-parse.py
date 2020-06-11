import requests
from requests_aws4auth import AWS4Auth
import time
import os
import json
import boto3
import socket
import datetime
import gzip
import re

def lambda_handler(event, context):
    # create boto3 clients
    s3 = boto3.client('s3')
    dynamodb = boto3.client('dynamodb')
    runtime = boto3.client('sagemaker-runtime')
    # set the ipv4 regex pattern
    ipv4Regex = re.compile('^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    digestRegex = re.compile('CloudTrail-Digest')
    # loop through list of s3 events
    for r in event['Records']:
        # abort if the file is larger than 512MB
        objectSize = int(r['s3']['object']['size'])
        if objectSize >= 536870911:
            pass
        else:
            bucketName = str(r['s3']['bucket']['name'])
            keyName = str(r['s3']['object']['key'])
            digestCheck = digestRegex.search(keyName)
            if digestCheck:
                pass
            else:
                # create local file path in Lambda
                localFilePath = '/tmp/' + keyName.split('/')[-1]
                # download waf log to Lambda /tmp
                s3.download_file(bucketName, keyName, localFilePath)
                try:
                    # gunzip the cloudtrail log
                    with gzip.open(localFilePath,'r') as content:
                        for line in content:
                            # turn the decompressed logs into a dict
                            cloudTrailLogs = json.loads(line)
                            for r in cloudTrailLogs['Records']:
                                ctLogDict = json.dumps(r)
                                x = json.loads(ctLogDict)
                                # x.update
                                # drop logs that are invoked by AWS services directly
                                userIdType = str(r['userIdentity']['type'])
                                if userIdType == 'AWSService':
                                    pass
                                else:
                                    ipAddress = str(r['sourceIPAddress'])
                                    principalId = str(r['userIdentity']['principalId'])
                                    # drop source IP address that is not an IP, this is likely an AWS SPN and should be dropped anyway
                                    ipv4Match = ipv4Regex.match(ipAddress)
                                    if ipv4Match:
                                        pair = principalId + ',' + ipAddress
                                    else:
                                        pass
                except Exception as e:
                    print(e)
                    raise

                def anomaly_check():
                    # create sagemaker and ddb vars
                    smEndpoint = os.environ['SAGEMAKER_ENDPOINT']
                    anomalyDdbTable = os.environ['ANOMALY_DYNAMODB_TABLE']
                    # check if the principal ID and IP address pair is anomalous
                    response = runtime.invoke_endpoint(EndpointName=smEndpoint,ContentType='text/csv',Body=pair)
                    result = json.loads(response['Body'].read().decode())
                    prediction = float(result['predictions'][0]['dot_product'])
                    if prediction <= 0.03:
                        iso8601 = datetime.datetime.now().isoformat()
                        ts = int(time.time())
                        ttl = int(ts + 8*86000)
                        try:
                            table = dynamodb.Table(anomalyDdbTable)
                            table.put_item(
                                Item={
                                    'ANOMALY_IPV4': ipAddress,
                                    'entity': principalId,
                                    'iso-time': iso8601,
                                    'ttl': ttl
                                }
                            )
                        except Exception as e:
                            print(e)
                        anomalyDict = { 'isAnomaly': 'True' }
                        anomalyData = json.dumps(anomalyDict)
                        return anomalyData
                    else:
                        anomalyDict = { 'isAnomaly': 'False' }
                        anomalyData = json.dumps(anomalyDict)
                        return anomalyData

                def cloudtrail_publisher():
                    print('good')
                    """
                    awsRegion = os.environ['AWS_REGION']
                    accessKey = os.environ['AWS_ACCESS_KEY_ID']
                    secretAccessKey = os.environ['AWS_SECRET_ACCESS_KEY']
                    seshToken = os.environ['AWS_SESSION_TOKEN']
                    # create auth token
                    awsAuthToken = AWS4Auth(accessKey, secretAccessKey, awsRegion, 'es', session_token=seshToken)
                    host = os.environ['ELASTICSEARCH_URL']
                    index = 'waf-logs'
                    # create requests items
                    url = host + '/' + index + '/' + '_doc/'
                    headers = { "Content-Type": "application/json" }
                    r = requests.post(url, auth=awsAuthToken, data=newWafLog, headers=headers)
                    print(r.json())
                    """

                def main():
                    anomaly_check()
                    cloudtrail_publisher()

                main()