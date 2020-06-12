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

The second diagram details anomaly detection and threat intelligence enrichment activities before delivery to Elasticsearch Service
![SyntheticSun Automation Architecture](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-automation-diagram.jpg)

1. AWS Security Hub events with match EventBridge rules are sent to Kinesis Data Firehose which will batch and publish findings into Elasticsearch Service. Only certain findings will make it in such as [ElectricEye](https://github.com/jonrau1/ElectricEye), GuardDuty, Macie, IAM Access Analyzer and other security-related findings.
2. ALB, WAF, CloudTrail and VPC Flow Log IP addresses are ran against the IP-based IOC DynamoDB table to check for any matches.
3. WAF and ALB feeds are ran against the Domain-based IOC DynamoDB table to check for any matches from the hostnames.
4. All “ALLOWED” WAF requests and non-AWS service CloudTrail IP addresses are ran against the IP Insights Endpoint to detect anomalous activity. The WAF tuple is based on IP address and user-agent while the CloudTrail tuple is based on IP address and IAM principal name.
5. IP address and entity pairs that are deemed anomalous by IP Insights are written into the Anomaly DynamoDB table which is used by the GuardDuty automation job deployed in Phase 2. **Note** the WAF anomaly detection is appended to the log as a boolean.
6. A final JSON-formatted log is generated by the respective data sources, results of any threat intelligence matches are appended, logs are sent to Elasticsearch by the respective Lambda function handling the feed.

### Deployment instructions
1. Run the provided Python script to get the URI of the IP Insights image `cd SyntheticSun/readme-stage3 && python3 ipinsights-uri.py`.

2. Deploy a CloudFormation stack from `SyntheticSun_CORE_CFN.yaml`. This can take a few minutes due to the Sagemaker infrastructure services.

**Note:** If you trained new models in [Appendix A](https://github.com/jonrau1/SyntheticSun/tree/master/appendix-a-ipinsights) ensure that they are uploaded under the same names (e.g. `ct-model.tar.gz` or `waf-model.targ.gz`) they have in Stage 1. These values are hardcoded in the CFN template and will need to be manually changed if you named your model artifacts differently.

3. After the stack finishes creating execute another Python script to generate a resource-based IAM policy for the Elasticsearch Service domain. This script uses the `sys.argv` method to create variables from values provided to the command line. The below 3 values must be provided in the order they are given. **Note:** For the Elasticsearch endpoint URL do *not* use the Kibana one and remove any trailing slash.
```bash
python3 es-policy.py \
    my-aws-region (us-east-1) \
    trusted-cidr (e.g. 192.168.1.1/32) \
    elasticsearch-endpoint (e.g. https://my-domain-elasticsearch.com)
```

4. Log in and...