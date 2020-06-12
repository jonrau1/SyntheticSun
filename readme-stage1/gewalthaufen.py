import sys
import boto3
import json
from requests_aws4auth import AWS4Auth
import requests
import time
# create boto3 clients
ec2 = boto3.client('ec2')
sts = boto3.client('sts')
esearch = boto3.client('es')
wafv2 = boto3.client('wafv2')
ssm = boto3.client('ssm')
iam = boto3.client('iam')
awsAccountId = sts.get_caller_identity()['Account']
# set command line arguments
awsRegion = sys.argv[1]
vpcId = sys.argv[2]
trustedCidr = sys.argv[3]
wafArn = sys.argv[4]
firehoseArn = sys.argv[5]
esHostUrl = sys.argv[6]
mispInstanceId = sys.argv[7]

def endpoint_attachment():
    # get route tables
    try:
        response = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id','Values': [vpcId]}],DryRun=False)
        for tables in response['RouteTables']:
            tableId = str(tables['RouteTableId'])
            # create S3 endpoint
            try:
                response = ec2.create_vpc_endpoint(
                    DryRun=False,
                    VpcEndpointType='Gateway',
                    VpcId=vpcId,
                    ServiceName='com.amazonaws.' + awsRegion + '.s3',
                    RouteTableIds=[tableId]
                )
                print(response)
            except Exception as e:
                print(e)
                raise
            # create DynamoDB endpoint
            try:
                response = ec2.create_vpc_endpoint(
                    DryRun=False,
                    VpcEndpointType='Gateway',
                    VpcId=vpcId,
                    ServiceName='com.amazonaws.' + awsRegion + '.dynamodb',
                    RouteTableIds=[tableId]
                )
                print(response)
            except Exception as e:
                print(e)
                raise
    except Exception as e:
        print(e)
        raise

def elasticsearch_policy_attachment():
    rawPolicy = policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
            'Action': [
                'es:ESHttp*'
            ],
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/CTLogParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': [
                'es:ESHttp*'
            ],
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/ALBLogParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': [
                'es:ESHttp*'
            ],
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/FlowLogParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': [
                'es:ESHttp*'
            ],
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/WAFLogParserLambdaExecRolePolicy']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': [
                'es:ESHttp*'
            ],
            'Effect': 'Allow',
            'Principal': {'AWS': ['arn:aws:iam::' + awsAccountId + ':role/SuricataParserLambdaExecRole']},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            },
            {
            'Action': [
                'es:ESHttp*'
            ],
            'Effect': 'Allow',
            'Principal': {'AWS':'*'},
            'Resource':'arn:aws:es:' + awsRegion + ':' + awsAccountId + ':domain/syntheticsun-es/*',
            'Condition': {
                'IpAddress': {
                'aws:SourceIp': trustedCidr
                }
            }
            }
        ]
    }
    accessPolicy = json.dumps(rawPolicy)
    try:
        response = esearch.update_elasticsearch_domain_config(DomainName='syntheticsun-es',AccessPolicies=accessPolicy)
        print(response)
    except Exception as e:
        print(e)
        raise

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
    
def instance_profile():
    trustPolicy = {
        "Version": "2012-10-17",
        "Statement": [
            {
            "Effect": "Allow",
            "Principal": { "Service": "ec2.amazonaws.com" },
            "Action": "sts:AssumeRole"
            }
        ]
    }
    ec2Trust = json.dumps(trustPolicy)

    try:
        response = iam.create_role(
            RoleName='SyntheticSunMISPInstanceProfile',
            AssumeRolePolicyDocument=ec2Trust,
            Description='Role for SyntheticSun MISP instance - created by script',
            MaxSessionDuration=3600
        )
        print('Role created')
    except Exception as e:
        print(e)
        raise

    # wait for role to propgate
    time.sleep(5)
    try:
        response = iam.attach_role_policy(
            RoleName='SyntheticSunMISPInstanceProfile',
            PolicyArn='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore'
        )
    except Exception as e:
        print(e)
        raise
    try:
        response = iam.attach_role_policy(
            RoleName='SyntheticSunMISPInstanceProfile',
            PolicyArn='arn:aws:iam::aws:policy/CloudWatchAgentAdminPolicy'
        )
    except Exception as e:
        print(e)
        raise
    print('Policies attached')
    # wait for role to propgate
    time.sleep(5)

    try:
        response = iam.create_instance_profile(InstanceProfileName='SyntheticSunMISPInstanceProfile')
    except Exception as e:
        print(e)
        raise
    time.sleep(5)
    try:
        response = iam.add_role_to_instance_profile(
            InstanceProfileName='SyntheticSunMISPInstanceProfile',
            RoleName='SyntheticSunMISPInstanceProfile'
        )
    except Exception as e:
        print(e)
        raise
    print('instance profile created')
    time.sleep(6)

    try:
        response = ec2.associate_iam_instance_profile(
            IamInstanceProfile={'Name': 'SyntheticSunMISPInstanceProfile'},
            InstanceId=mispInstanceId
        )
        print(response)
    except Exception as e:
        print(e)
        raise

def im_helping():
    endpoint_attachment()
    elasticsearch_policy_attachment()
    waf_logging()
    cwa_ssm_parameter()
    es_alb_index_creation()
    es_vpc_index_creation()
    es_waf_index_creation()
    instance_profile()

im_helping()