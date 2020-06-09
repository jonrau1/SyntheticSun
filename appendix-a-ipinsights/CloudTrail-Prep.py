import boto3
import json
import os
import gzip
import re
import csv
# create boto3 clients
s3 = boto3.client('s3')
paginator = s3.get_paginator('list_objects_v2')
# var for CT logs bucket
ctBucket = ''
#ctBucket = os.environ['CLOUDTRAIL_LOGS_BUCKET']

# create an IPv4 regex
ipv4Regex = re.compile('^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')

# create an empty list to append converted CT logs into
ctList = []

# iterate over all objects in the bucket
iterator = paginator.paginate(Bucket=ctBucket)
for page in iterator:
    for item in page['Contents']:
        s3Obj = str(item['Key'])
        with open('file' + s3Obj, 'wb') as data:
            s3.download_fileobj(ctBucket, s3Obj, data)
            with gzip.open('file' + s3Obj,'r') as content:
                for line in content:
                    # turn the decompressed logs into a dict
                    cloudTrailLogs = json.loads(line)
                    for r in cloudTrailLogs['Records']:
                        # drop logs that are invoked by AWS services directly
                        userIdType = str(r['userIdentity']['type'])
                        if userIdType == 'AWSService':
                            os.remove('file' + s3Obj)
                            continue
                        else:
                            clientIp = str(r['sourceIPAddress'])
                            # drop source IP address that is not an IP, this is likely an AWS SPN and should be dropped anyway
                            ipv4Match = ipv4Regex.match(clientIp)
                            if ipv4Match:
                                iamPrincipalId = str(r['userIdentity']['principalId'])
                                ctDict = {
                                    'ipaddress': clientIp,
                                    'principalId': iamPrincipalId
                                }
                                formJson = json.dumps(ctDict)
                                ctList.append(formJson)
                                os.remove('file' + s3Obj)
                            else:
                                os.remove('file' + s3Obj)
                                continue

data = json.loads(ctList)

with open('cloudtrail-training-data.csv', 'w') as outf:
    dw = csv.DictWriter(outf, data[0].keys())
    dw.writeheader()
    for row in data:
        dw.writerow(row)