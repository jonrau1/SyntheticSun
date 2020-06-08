import os
import boto3
import datetime
import ipaddress
# create boto3 clients and ddb paginator
wafv2 = boto3.client('wafv2')
dynamodb = boto3.client('dynamodb')
scanPaginator = dynamodb.get_paginator('scan')
# variables for CTI
ctiDdbTable = os.environ['MISP_IP_IOC_DDB_TABLE']
ctiIpSetId = os.environ['WAF_CTI_IP_SET_ID']
ctiIpSetName = os.environ['WAF_CTI_IP_SET_NAME']
# variables for anomalies
anomalyDdbTable = os.environ['IP_INSIGHTS_DDB_TABLE']
anomalyIpSetId = os.environ['IP_INSIGHTS_IP_SET_ID']
anomalyIpSetName = os.environ['IP_INSIGHTS_IP_SET_NAME']

def cti_ip_set_update():
    # create writer object
    f = open('./blocklist.txt','w')
    # perform a paginated scan on ddb table
    # parse our IP-based IOCs and write them to the file with a new line
    iterator = scanPaginator.paginate(TableName=ctiDdbTable)
    for page in iterator:
        for item in page['Items']:
            ipAddress = str(item['IPV4_IOC']['S'])
            try:
                ipv4Check = ipaddress.IPv4Address(ipAddress)
                f.write(ipAddress + '/32' + '\n')
            except:
                pass
    # close out the file
    f.close()
    # get lock token to update waf ip set
    try:
        response = wafv2.get_ip_set(Name=ctiIpSetName,Scope='REGIONAL',Id=ctiIpSetId)
        lockToken = str(response['LockToken'])
    except Exception as e:
        print(e)
    # parse down file, remove last trailing new line and convert to a list
    lineList = [line.rstrip('\n') for line in open('./blocklist.txt')]
    ipSetList = lineList[:10000]
    # create timestamp for ip set update description
    x = datetime.datetime.now().isoformat()
    strX = str(x)
    # update the Ip set
    try:
        response = wafv2.update_ip_set(
            Name=ctiIpSetName,
            Scope='REGIONAL',
            Id=ctiIpSetId,
            Description='MISP IP Set updated by automation on ' + strX,
            Addresses=ipSetList,
            LockToken=lockToken
        )
        print(response)
    except Exception as e:
        print(e)
    print('IP Set updated!')

def ipinsights_ip_set_update():
    # create writer object
    f = open('./anomalies.txt','w')
    # perform a paginated scan on ddb table
    # parse our IP-based IOCs and write them to the file with a new line
    iterator = scanPaginator.paginate(TableName=anomalyDdbTable)
    for page in iterator:
        for item in page['Items']:
            ipAddress = str(item['ANOMALY_IPV4']['S'])
            try:
                ipv4Check = ipaddress.IPv4Address(ipAddress)
                f.write(ipAddress + '/32' + '\n')
            except:
                pass
    # close out the file
    f.close()
    # get lock token to update waf ip set
    try:
        response = wafv2.get_ip_set(Name=ctiIpSetName,Scope='REGIONAL',Id=anomalyIpSetId)
        lockToken = str(response['LockToken'])
    except Exception as e:
        print(e)
    # parse down file, remove last trailing new line and convert to a list
    lineList = [line.rstrip('\n') for line in open('./anomalies.txt')]
    ipSetList = lineList[:10000]
    # create timestamp for ip set update description
    x = datetime.datetime.now().isoformat()
    strX = str(x)
    # update the Ip set
    try:
        response = wafv2.update_ip_set(
            Name=anomalyIpSetName,
            Scope='REGIONAL',
            Id=anomalyIpSetId,
            Description='MISP IP Set updated by automation on ' + strX,
            Addresses=ipSetList,
            LockToken=lockToken
        )
        print(response)
    except Exception as e:
        print(e)
    print('IP Set updated!')

def pizza_delivery():
    cti_ip_set_update()
    ipinsights_ip_set_update()

pizza_delivery()