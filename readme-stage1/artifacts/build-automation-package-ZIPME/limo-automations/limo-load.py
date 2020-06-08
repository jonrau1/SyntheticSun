import os
from cabby import create_client
import datetime
import time
import pytz
import glob
from stix.core import STIXPackage, STIXHeader
import hashlib
import boto3

awsRegion = os.environ['AWS_REGION']
ipIOCTable = os.environ['IP_IOC_DDB_TABLE']

dynamodb = boto3.resource('dynamodb', region_name=awsRegion)
# constant value, does not account of Epoch Leap Seconds
# so you can be +- 2 epoch seconds off (not that we care)
epochDay = int(86400)
# Date magic
b = datetime.datetime.now() - datetime.timedelta(3)
timezone = pytz.timezone('US/Eastern')
beginDate = timezone.localize(b)
e = datetime.datetime.now()
timezone = pytz.timezone('US/Eastern')
endDate = timezone.localize(e)
# Create TAXII client
client = create_client('limo.anomali.com', use_https=True, discovery_path='/api/v1/taxii/taxii-discovery-service/')
client.set_auth(username='guest', password='guest')
services = client.discover_services()
# write DShield LIMO feed to XML file
content_blocks = client.poll(collection_name='DShield_Scanning_IPs_F150',begin_date=beginDate,end_date=endDate)
for block in content_blocks:
    with open('dshield.xml', 'wb') as file_handle:
		    file_handle.write(block.content)
# write ET D68 LIMO feed to XML file
content_blocks = client.poll(collection_name='Emerging_Threats___Compromised_F68',begin_date=beginDate,end_date=endDate)
for block in content_blocks:
    with open('etd68.xml', 'wb') as file_handle:
		    file_handle.write(block.content)
# create global variable for xml files
xmlFiles = glob.glob("*.xml")
# parse down XML files using the STIX spec
for xml in xmlFiles:
    pkg=STIXPackage.from_xml(xml)
    pkg_dict=pkg.to_dict()
    for v in pkg_dict.get('indicators'):
        description=v.get('description').split(';')
        timeString=v.get('producer').get('time').get('produced_time')
        source=description[5].split(':')
        iPAddress=v.get('observable').get('object').get('properties').get('address_value')
        Value=v.get('observable').get('object').get('properties').get('value')
        Confidence=v.get('confidence').get('value').get('value')
        # create TTL record by converting time string to Epoch seconds
        myDate = datetime.datetime.fromisoformat(timeString)
        myDateString = str(myDate)
        myDateEpoch = int(datetime.datetime.timestamp(myDate))
        ttl = int(myDateEpoch + 8*epochDay)
        # create hash of feed name to create UUID
        limoSource = str(source[1])
        feedBytes = bytes(limoSource, encoding='utf8')
        limoUuid = hashlib.sha224(feedBytes).hexdigest()
        try:
            table = dynamodb.Table(ipIOCTable)
            table.put_item(
                Item={
                    'IPV4_IOC': iPAddress,
                    'iso-time': myDateString,
                    'ttl': ttl,
                    'feed-name': limoSource,
                    'feed-uuid': limoUuid
                }
            )
        except Exception as e:
            print(e)
            raise

print('All LIMO feeds published to DynamoDB!')
exit(0)
