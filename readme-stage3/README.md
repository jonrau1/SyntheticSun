# SyntheticSun
SyntheticSun is a proof of concept (POC) defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats.

*"You sleep in fragmented glass"*</br>
*With reflections of you,"*</br>
*But are you feeling alive?"*</br>
*Yeah let me ask you,"*</br>
*Are you feeling alive?"*</br>
<sub>- **Norma Jean, 2016**</sub>

## Stage 3 - Core module deployment
In this Stage we will deploy the remainder of the infrastructure services that makes up the core of SyntheticSun and finally perform light configurations within Kibana (setting up indicies, importing visualizations). This is the last mandatory Stage of the solution, we'll go over the solutions architecture first, deployment instructions are below it.

### Solution Architecture
The solution architecture is split across two diagrams. The first diagram shows the basic data flows of how the telemetry sources are collected, normalized, and identifies basic enrichment. The second diagram details the threat defense automation framework and specialized enrichment steps based on the telemetry source.

The first diagram outlines the processing taken on the following security telemetry sources.
![SyntheticSun Telemetry Architecture](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-telemetry-diagram.jpg)

#### CloudTrail
1.	CloudTrail logs are published to an S3 bucket where a S3 Event will invoke a Lambda function
2.	Lambda will download, gunzip and parse out IP information from CloudTrail, if the action was taken from an IP address, Lambda will attempt to enrich the log with geolocation details
3.	Lambda prepares for additional conditional processing as shown in the next diagram
#### VPC Flow Logs
1.	Flow Logs are published to a CloudWatch Logs Group where a subscription will send them to Lambda to be converted from a space-separated log format to JSON
2.	Lambda will add additional EC2 instance information based on if the flow destination was to an instance, if not, the enrichment details from this step are marked as “Unidentified”
3.	Lambda will attempt to add geolocation data based on the source and destination. RFC1918 space will be marked as “Unidentified” as it is likely the private IP space for your resources on the AWS cloud
4.	Lambda will use the Python 3 Socket module to attempt to perform a reverse DNS lookup of the source or destination IP addresses. RFC1918 space will be marked as “Unidentified” as it is likely the private IP space for your resources on the AWS cloud
5.	Lambda prepares for additional conditional processing as shown in the next diagram
#### ALB Access Logs
1.	ALB Access logs are published to an S3 bucket where a S3 Event will invoke a Lambda function
2.	Lambda will download, gunzip and parse the log files and use regex and other methods to extract out connection and HTTP information from the log files
3.  Lambda will attempt to add geolocation data for the client IP
4.  Lambda will use the Python 3 Socket module to attempt to perform a reverse DNS lookup of the client IP
5.	Lambda prepares for additional conditional processing as shown in the next diagram
#### WAF Request Logs
1.	WAF Logs are published to Kinesis Data Firehose which are then sent to a bucket per Web ACL
2.	An S3 Event will invoke a Lambda function to download and perform restructuring of the WAF log
3.  Lambda will attempt to add geolocation data for the client IP
4.  Lambda will use the Python 3 Socket module to attempt to perform a reverse DNS lookup of the client IP
5.	Lambda prepares for additional conditional processing as shown in the next diagram
#### Suricta (HIDS/HIPS/NSM)
1.	Suricata publishes logs to the EVE.json file, a modified configuration file is used to reduce the relative noisyness of these logs.
2.	A CloudWatch Agent is configured to process this file and publish it to a CloudWatch Logs Group, each stream corresponds to an EC2 instance ID
3.	Lambda parses the logs from the CloudWatch Log streams and inserts them into ElasticSearch Service

The second diagram details automation and specialized enrichment activities before delivery to Elasticsearch Service
![SyntheticSun Automation Architecture](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-automation-diagram.jpg)

1.	MISP scheduled jobs on the host will refresh feeds and fetch events from feeds that are enabled and published via tags
2.	A cronjob-based Event will periodically invoke a CodeBuild project to pull all tagged feeds, perform light data formatting and write them to DynamoDB tables based on their IOC-type (IP or Domain/Hostname)
3.	Another cronjob-based Event will periodically invoke another CodeBuild project to write the entire content of the IP-IOC and Sagemaker DynamoDB tables into a text file which is parsed to update WAF IP Sets and dropped into a S3 bucket to be used by GuardDuty
4.	CodeBuild will use the UpdateThreatList API to instruct GuardDuty to use the latest text files that are generated
5.	AWS Security Hub and AWS Health (for Abuse findings) publish events to EventBridge which uses rules to match these events and publish them to Kinesis Data Firehose which in turn ships them to Elasticsearch Service
6.	All “ALLOWED” WAF requests and non-AWS service CloudTrail IP addresses are ran against the IP Insights Endpoint to detect anomalous activity. The WAF tuple is based on IP address and user-agent while the CloudTrail tuple is based on IP address and IAM principal name
7.	ALB, WAF, CloudTrail and VPC Flow Log IP addresses are ran against the IP-based IOC DynamoDB table to check for any matches
8.	WAF and ALB feeds are ran against the Domain-based IOC DynamoDB table to check for any matches from the hostnames
9.	A final JSON log format is generated by the respective data sources with results of the threat intelligence and Sagemaker enrichment and written into Elasticsearch Service by the respective Lambda function handling the feed

### Deployment instructions
1. Deploy a CloudFormation stack from `SyntheticSun_CORE_CFN.yaml`. This can take a few minutes due to the Sagemaker infrastructure services.