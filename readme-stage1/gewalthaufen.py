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
import time
# set the profile for boto3 to use
profileName = sys.argv[1]
session = boto3.Session(profile_name=profileName)
# create boto3 clients
sts = boto3.client('sts')
esearch = session.client('es')
wafv2 = session.client('wafv2')
ssm = session.client('ssm')
awsAccountId = sts.get_caller_identity()['Account']
# set command line arguments
awsRegion = sys.argv[2]
wafArn = sys.argv[3]
firehoseArn = sys.argv[4]
esHostUrl = sys.argv[5]

def waf_logging():
    try:
        response = wafv2.put_logging_configuration(LoggingConfiguration={'ResourceArn': wafArn,'LogDestinationConfigs': [firehoseArn]})
        print(response)
    except Exception as e:
        print(e)
        raise

def cwa_ssm_parameter():
    rawParameter = {
        'agent': {
            'run_as_user': 'cwagent'
        },
        'logs': {
            'logs_collected': {
                'files': {
                    'collect_list': [
                        {
                            'file_path': '/var/log/suricata/eve-dns.json',
                            'log_group_name': 'Suricata-DNS-Logs',
                            'log_stream_name': '{instance_id}'
                        },
                        {
                            'file_path': '/var/log/suricata/eve-ids.json',
                            'log_group_name': 'Suricata-Not-DNS-Logs',
                            'log_stream_name': '{instance_id}'
                        }
                    ]
                }
            }
        }
    }
    paramVal = json.dumps(rawParameter)
    try:
        response = ssm.put_parameter(
            Name='AmazonCloudWatch-linux',
            Description='SyntheticSun cloudwatch agent spec for Linux',
            Value=paramVal,
            Type='String',
            Overwrite=True,
            Tier='Standard'
        )
    except Exception as e:
        print(e)
        raise

def es_apigw_index_creation():
    region = awsRegion
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)
    host = esHostUrl
    index = 'apigw-accesslogs'
    url = host + '/' + index + '/'
    headers = { "Content-Type": "application/json" }
    pload = {
        "mappings": {
            "properties": {
                'clientIp': { "type": "ip"  },
                'date': { "type": "date"  },
                'requestTimeEpoch': { "type": "integer"  },
                'httpMethod': { "type": "text"  },
                'protocol': { "type": "text"  },
                'userAgent': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'domainName': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'routeKey': { "type": "text"  },
                'status': { "type": "integer"  },
                'responseLength': { "type": "integer"  },
                'requestId': { "type": "text"  },
                'location': { "type": "geo_point" },
                'clientCountryCode': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'clientIsp': { "type": "text"  },
                'clientOrg': { "type": "text"  },
                'clientPort': { "type": "text"  },
                'clientAs': { "type": "text"  },
                'clientAsname': { "type": "text"  },
                'clientHost': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'clientFqdn': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'clientIpThreatMatch': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'clientHostnameThreatMatch': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'isAnomaly': { "type": "text", "fields": {"keyword": { "type": "keyword"}}}
            }
        }
    }
    r = requests.put(url, auth=awsauth, json=pload, headers=headers)
    print(r.json())

def es_alb_index_creation():
    region = awsRegion
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)
    host = esHostUrl
    index = 'app-load-balancer'
    url = host + '/' + index + '/'
    headers = { "Content-Type": "application/json" }
    pload = {
        "mappings": {
            "properties": {
                'trafficType': { "type": "text"  },
                'timestamp': { "type": "date"  },
                'elbTimestamp': { "type": "text"  },
                'elbName': { "type": "text"  },
                'elbVpcId': { "type": "text"  },
                'clientIp': { "type": "ip"  },
                'clientIpThreatMatch': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'clientReverseDomain': { "type": "text"  },
                'clientHostnameThreatMatch': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'location': { "type": "geo_point" },
                'clientCountryCode': { "type": "text"  },
                'clientIsp': { "type": "text"  },
                'clientOrg': { "type": "text"  },
                'clientPort': { "type": "text"  },
                'clientAs': { "type": "text"  },
                'clientAsname': { "type": "text"  },
                'receivedBytes': { "type": "integer"  },
                'sentBytes': { "type": "integer"  },
                'httpMethod': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'uri':  { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'httpVersion': { "type": "text"  },
                'userAgent':  { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'statusCode': { "type": "text", "fields": {"keyword": { "type": "keyword"}}}
            }
        }
    }
    r = requests.put(url, auth=awsauth, json=pload, headers=headers)
    print(r.json())

def es_vpc_index_creation():
    region = awsRegion
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)
    host = esHostUrl
    index = 'vpc-flows'
    url = host + '/' + index + '/'
    headers = { "Content-Type": "application/json" }
    pload = {
        "mappings": {
            "properties": {
                'accountId': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'interfaceId': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'interfaceArn': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'packets': { "type": "integer"  },
                'bytes': { "type": "integer"  },
                'sourceInstanceId': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'sourceInstanceArn': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'sourceIp': { "type": "ip"  },
                'sourceIpIsThreat': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'sourceReverseDomain': { "type": "text"  },
                'sourceLocation': { "type": "geo_point" },
                'sourceIpCountry': { "type": "text"  },
                'sourceIsp': { "type": "text"  },
                'sourceOrg': { "type": "text"  },
                'sourceAs': { "type": "text"  },
                'sourceAsname': { "type": "text"  },
                'destInstanceId': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'destInstanceArn': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'destIp': { "type": "ip"  },
                'destIpIsThreat': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'destReverseDomain': { "type": "text"  },
                'destinationLocation': { "type": "geo_point" },
                'destIpCountry': { "type": "text"  },
                'destIsp': { "type": "text"  },
                'destOrg': { "type": "text"  },
                'destAs': { "type": "text"  },
                'destAsname': { "type": "text"  },
                'sourcePort': { "type": "text"  },
                'destPort': { "type": "text"  },
                'protocol': { "type": "text"  },
                'date': { "type": "date"  },
                'action': { "type": "text", "fields": {"keyword": { "type": "keyword"}}} 
            }
        }
    }
    r = requests.put(url, auth=awsauth, json=pload, headers=headers)
    print(r.json())

def es_waf_index_creation():
    region = awsRegion
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)
    host = esHostUrl
    index = 'waf-logs'
    url = host + '/' + index + '/'
    headers = { "Content-Type": "application/json" }
    pload = {
        "mappings": {
            "properties": {
                'date': { "type": "date"  },
                'isAnomaly': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'webAclArn': { "type": "text"  },
                'terminatingRuleId': { "type": "text"  },
                'action': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'httpSourceName': { "type": "text"  },
                'httpSourceId': { "type": "text"  },
                'uri': { "type": "text"  },
                'httpMethod': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'userAgent': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'clientIp': { "type": "ip"  },
                'location': { "type": "geo_point" },
                'clientIsp': { "type": "text"  },
                'clientOrg': { "type": "text"  },
                'clientAs': { "type": "text"  },
                'clientAsName': { "type": "text"  },
                'clientHostname': { "type": "text"  },
                'clientHostnameThreatMatch': { "type": "text", "fields": {"keyword": { "type": "keyword"}}},
                'clientIpThreatMatch': { "type": "text", "fields": {"keyword": { "type": "keyword"}}}
            }
        }
    }
    r = requests.put(url, auth=awsauth, json=pload, headers=headers)
    print(r.json())

def im_helping():
    endpoint_attachment()
    waf_logging()
    cwa_ssm_parameter()
    es_apigw_index_creation()
    es_alb_index_creation()
    es_vpc_index_creation()
    es_waf_index_creation()

im_helping()