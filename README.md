# SyntheticSun
SyntheticSun is a Proof of Concept (POC) defense-in-depth security automation framework which utilizes threat intelligence, machine learning, data engineering, managed AWS security services and serverless technologies to continuously adapt to, detect and neutralize new and existing threats at the edge.

*"You sleep in fragmented glass"*</br>
*With reflections of you,"*</br>
*But are you feeling alive?"*</br>
*Yeah let me ask you,"*</br>
*Are you feeling alive?"*</br>
<sub>- **Norma Jean, 2016**</sub>

## Synopsis
-	Uses event- and time-based serverless automation (e.g. AWS CodeBuild, AWS Lambda) to collect, normalize, enrich, and correlate security telemetry
-	Leverage threat intelligence, open-source intelligence, and AWS APIs to further enrich security telemetry and quickly respond to threats
-	IP Insights model from Amazon Sagemaker adds anomaly detection based on IP address and user-agent, username, or account number tuples
-	Dynamically update AWS WAF IP Sets and Amazon GuardDuty Threat Lists to bolter protection of your account and infrastructure from known threats

## Description
SyntheticSun is built around the usage of the Malware Information Sharing Platform (MISP) which is an open-source and community driven threat intelligence platform (TIP) and the IP Insights Amazon Sagemaker unsupervised machine learning algorithm to provide the core threat defense capabilities. MISP comes with dozens of out-of-the-box feeds that provide IP-address, URL, and domain/hostname-based indicators of compromise (IOC). MISP also has some compatibility with STIX/TAXII feeds from importing commercial and open-source feeds in those formats, such as Anamoli’s ThreatStream or STAXX platform, respectively.

AWS serverless technologies such as Lambda, DynamoDB, CodeBuild, EventBridge / CloudWatch Events and Kinesis are used for their ability to rapidly scale, their ease of use, and relatively cheap costs versus heavy MapReduce or Glue ETL-based data engineering jobs. All code is written in Python 3.8 and uses basic modules such as requests, json, ipaddress, socket and os to perform most of the extraction, transformation, and loading (ETL) into downstream services. All geolocation information is provided by ip-api.com, it does not require an account or paid tiers and has a great API which also includes throttling information in their response headers.

Outside of some basic configuration that needs to be done in MISP and artifacts being uploaded to an S3 bucket, this entire solution is automated and easily deployed (and sharable) via CloudFormation. Besides the usage of an EC2 instance for MISP and Elasticsearch Service it is 98% Serverless (since that matters to people). One thing I would not use in production is my pre-trained IP Insights model, I used traffic from my honeypots and AWS training data from the Jupyter notebook to train it and it’ll most likely not fit your use case. I am also 99% sure I am using it wrong, but whatever.

## Solution Architecture
The solution architecture is split across two diagrams. The first diagram shows the basic data flows of how the telemetry sources are collected, normalized, and identifies basic enrichment. The second diagram details the threat defense automation framework and specialized enrichment steps based on the telemetry source.

The first diagram outlines the processing taken on the following security telemetry sources.
![SyntheticSun Telemetry Architecture](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-telemetry-diagram.jpg)

#### CloudTrail
1.	CloudTrail logs are published to an S3 bucket where a S3 Event will invoke a Lambda function
2.	Lambda will gunzip and parse out IP information from CloudTrail, if the action was taken from an IP address, Lambda will attempt to enrich the log with geolocation details
3.	Lambda prepares for additional conditional processing as shown in the next diagram
#### VPC Flow Logs
1.	Flow Logs are published to a CloudWatch Logs Group where a subscription will send them to Lambda to be converted from a space-separated log format to JSON
2.	Lambda will add additional EC2 instance information based on if the flow destination was to an instance, if not, the enrichment details from this step are marked as “Unidentified”
3.	Lambda will attempt to add geolocation data based on the source and destination. RFC1918 space will be marked as “Unidentified” as it is likely the private IP space for your resources on the AWS cloud
4.	Lambda will use the Python 3 Socket module to attempt to perform a reverse DNS lookup of the source or destination IP addresses. RFC1918 space will be marked as “Unidentified” as it is likely the private IP space for your resources on the AWS cloud
5.	Lambda prepares for additional conditional processing as shown in the next diagram
#### Non-DNS Suricata EVE Logs (Alerts, Anomalies and TLS Traffic will be sent)
1.	Suricata is configured to publish Alerts (based on rules), Anomalies and Extended TLS based traffic to a separate EVE JSON log output
2.	Kinesis Data Agent is configured to process this file and publish it to a Kinesis Data Firehose delivery stream
3.	The delivery stream publishes all Non-DNS Suricata EVE Logs to Elasticsearch without further processing
#### DNS Suricata EVE Logs
1.	Suricata is configured to published Extended DNS logs to a separate EVE JSON log output. No other log formats are published (e.g. DHCP, TCP, HTTP)
2.	Kinesis Data Agent is configured to process this file and publish it to a Kinesis Data Stream that has a subscription to a Lambda function
3.	Lambda will use the Python 3 Socket module to attempt to lookup the IP address from any DNS host name or domain
4.	Lambda prepares for additional conditional processing as shown in the next diagram
#### WAF Request Logs
1.	WAF Logs are published to Kinesis Data Firehose which are then sent to a bucket per Web ACL
2.	An S3 Event will invoke a Lambda function to download and performs extremely basic data format normalization of the WAF logs. WAF publishes logs in JSON and already includes DNS, Geolocation and HTTP request header information in the logs
3.	Lambda prepares for additional conditional processing as shown in the next diagram

The second diagram details automation and specialized enrichment activities before delivery to Elasticsearch Service
![SyntheticSun Automation Architecture](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-automation-diagram.jpg)

1.	MISP scheduled jobs on the host will refresh feeds and fetch events from feeds that are enabled and published via tags
2.	A cronjob-based Event will periodically invoke a CodeBuild project to pull all tagged feeds, perform light data formatting and write them to DynamoDB tables based on their IOC-type (IP or Domain/Hostname)
3.	Another cronjob-based Event will periodically invoke another CodeBuild project to write the entire content of the IP-IOC and Sagemaker DynamoDB tables into a text file which is parsed to update WAF IP Sets and dropped into a S3 bucket to be used by GuardDuty
4.	CodeBuild will use the UpdateThreatList API to instruct GuardDuty to use the latest text files that are generated
5.	AWS Security Hub and AWS Health (for Abuse findings) publish events to EventBridge which uses rules to match these events and publish them to Kinesis Data Firehose which in turn ships them to Elasticsearch Service
6.	All “ALLOWED” WAF requests and non-AWS service CloudTrail IP addresses are ran against the IP Insights Endpoint to detect anomalous activity. The WAF tuple is based on IP address and user-agent while the CloudTrail tuple is based on IP address and IAM principal name
7.	WAF, CloudTrail and VPC Flow Log IP addresses are ran against the IP-based IOC DynamoDB table to check for any matches
8.	The Suricata DNS feed is ran against the Domain-based IOC DynamoDB table to check for any matches
9.	A final JSON log format is generated by the respective data sources with results of the threat intelligence and Sagemaker enrichment and written into matching Firehose delivery streams which are delivered to Elasticsearch service

## Setting Up
Coming Soon.

## FAQ
Coming Soon.

## Contributing
I am happy to accept PR's for items tagged as "Help Wanted" in Issues or the Project Board. I will review any other proposed PRs as well if it meets the spirit of the project.

## License
This library is licensed under the GNU General Public License v3.0 (GPL-3.0) License. See the LICENSE file.