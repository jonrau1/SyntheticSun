import boto3
import os
import requests
import json
import datetime
# import codebuild env vars
mispParam = os.environ['MISP_AUTOMATION_KEY_PARAMETER']
awsRegion = os.environ['AWS_REGION']
mispIpIOCTable = os.environ['MISP_IP_IOC_DDB_TABLE']
mispDomainIOCTable = os.environ['MISP_DOMAIN_IOC_DDB_TABLE']
mispEc2Id = os.environ['MISP_EC2_ID']
# constant value, does not account of Epoch Leap Seconds
# so you can be +- 2 epoch seconds off (not that we care)
epochDay = int(86400)
# create boto3 clients
ssm = boto3.client('ssm')
ec2 = boto3.client('ec2')
dynamodb = boto3.resource('dynamodb', region_name=awsRegion)
# retrieve automation key from SSM
try:
    response = ssm.get_parameter(Name=mispParam,WithDecryption=True)
    authKey = str(response['Parameter']['Value'])
except Exception as e:
    print(e)
# retrieve private IP of the MISP server
try:
    response = ec2.describe_instances(InstanceIds=[mispEc2Id])
    mispIp = str(response['Reservations'][0]['Instances'][0]['PrivateIpAddress'])
except Exception as e:
    print(e)
# requests header
headers = { 'Authorization': authKey,'Accept': 'application/json','Content-type': 'application/json' }


def misp_ip_related_feeds_pull():
    #,"to_ids":"yes"
    data = '{"tags":"DDB_IP_FEED"}' 
    r = requests.post('https://' + mispIp + '/attributes/restSearch', headers=headers, data=data, verify=False) 
    c2Feed = r.json()
    for attribute in c2Feed['response']['Attribute']:
        value = str(attribute['value'])
        timestamp = int(attribute['timestamp'])
        # start time conversion
        isoTime = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
        isoString = str(isoTime)
        ttl = int(timestamp + 8*epochDay)
        feedName = str(attribute['Event']['info'])
        feedUuid = str(attribute['Event']['uuid'])
        # send info to dynamo
        try:
            table = dynamodb.Table(mispIpIOCTable)
            table.put_item(
                Item={
                    'IPV4_IOC': value,
                    'iso-time': isoString,
                    'ttl': ttl,
                    'feed-name': feedName,
                    'feed-uuid': feedUuid
                }
            )
        except Exception as e:
            print(e)
    print('All IP related feeds loaded to DynamoDB')

def misp_domain_related_feeds_pull():
    #,"to_ids":"yes"
    data = '{"tags":"DDB_URL_FEED"}' 
    r = requests.post('https://' + mispIp + '/attributes/restSearch', headers=headers, data=data, verify=False) 
    c2Feed = r.json()
    for attribute in c2Feed['response']['Attribute']:
        value = str(attribute['value'])
        timestamp = int(attribute['timestamp'])
        # start time conversion
        isoTime = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
        isoString = str(isoTime)
        ttl = int(timestamp + 8*epochDay)
        feedName = str(attribute['Event']['info'])
        feedUuid = str(attribute['Event']['uuid'])
        # send info to dynamo
        try:
            table = dynamodb.Table(mispDomainIOCTable)
            table.put_item(
                Item={
                    'DOMAIN_IOC': value,
                    'iso-time': isoString,
                    'ttl': ttl,
                    'feed-name': feedName,
                    'feed-uuid': feedUuid
                }
            )
        except Exception as e:
            print(e)
    print('All Domain and URL related feeds loaded to DynamoDB')

def exit_func():
    print('all feeds loaded, exiting')
    exit(0)

def misp_loader():
    misp_ip_related_feeds_pull()
    misp_domain_related_feeds_pull()
    exit_func()

misp_loader()