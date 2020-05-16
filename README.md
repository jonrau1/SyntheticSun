# SyntheticSun
SyntheticSun is a proof of concept (POC) defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats.

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

## Setting Up
Coming Soon.

## FAQ
#### 1. Why should I use this solution?
SyntheticSun is an easy way to start using cyber threat intelligence and machine learning for your edge protection security use cases on the AWS Cloud without having to invest in one or more commercial tools or a data scientist for your security team. This solution, after initial configuration, is fully automated allowing you to identify and respond to threats at machine speed. Finally, this solution provides basic visualizations for your incident response team to use for threat response, such as allowed inbound or outbound connections or DNS queries to / from IP addresses or domains deemed to be malicious. The core of the solution relies on very lightweight automation and data engineering pipelines, which theoretically, can be reused for other purposes where multi-stage normalization and enrichment or scheduled fast-paced batch jobs are needed.

#### 2. Who should use this solution?
Firstly, if you are making use or GuardDuty and/or AWS WAF it may make sense to evaluate this solution, but it is also a requirement. Obvious personas who can take advantage are product teams responsible for securing their full stack and lack the capital or expertise to model, train and deploy machine learning algorithms or operationalize cyber threat intelligence feeds in a meaningful way. Those aforementioned personas are likely security engineering, SecOps / SOC analysts & engineers or a DevSecOps engineer, but that list is not exhaustive, and they do not need to be product / application-aligned as central teams can use this as well. Another usage is those same personas (SecOps, security engineering) that work for a centralized team and want to create a dynamic block list for firewalls and intrusion prevention systems, the CodeBuild projects can be repurposed to drop CSV or flat files to almost any location (e.g. Palo Alto firewalls, Squid forward proxy URL filters, etc.)

#### 3. What are the non-negotiable dependencies for this solution?
You should be currently using AWS ELB (ALB) and logging to S3, AWS WAF and logging requests with Kinesis Data Firehose, CloudTrail and publishing the latest version (with all fields) of VPC Flow Logs to CloudWatch Logs. Additionally, you should also have GuardDuty and Security Hub enabled. If your account is a part of an Organization this solution should be deployed ***at a minimum*** where your GuardDuty Master is located as the Threat Lists cannot be updated by the members. Ideally, your Organizational Health API, Organizational CloudTrail, AWS Firewall Manager Administrator Account and Security Hub Master will be in the same place to make collection of security telemetry from those sources easier.

#### 4. Outside of the Masters for the AWS Security Services, what considerations are there for an Organizational deployment?
The easiest way to deploy this solution for an organization is to deploy it as suggested in FAQ #3 where all of your centralized security and management services are located. For the lower-level telemetry such as VPC Flow Logs and WAF Logs, you should split those elements out of the main CloudFormation template into their own and share them across your organization in AWS Service Catalog or in another centralized area. You will need to evaluate your shard consumption and index rotation of Elasticsearch Service, as well as the permissions, if you will be having cross-account Kinesis Data Firehose delivery streams publishing into a centralized location.

I built this solution in my personal sandbox account, hence why I did not bake any of the considerations from above into the solution, I will be happy to work on a PR with this in mind and may do it myself in the future.

#### 5. What is the IP Insights algorithm? Is your usage really what it was intended for?
**CAVEATS**: I am not a data scientist and this is going to be a long answer. Tl;dr: It's an anomaly finder and I think?

Given that I am not remotely close to a data scientist or have any training you are better served [reading the docs](https://docs.aws.amazon.com/sagemaker/latest/dg/ip-insights-howitworks.html) on this. That said, here is my layman's attempt at it, IP Insights is an unsupervised machine learning algorithm that learns the relationship between an IPv4 address and an entity (e.g. Account number, user name, user-agent) and tried to determine how likely it is that the entity would use that IPv4 address. Behind the curtains of IP Insights is a neural network that learns the latent vector representation of these entities and IPv4 addresses and the distance betweens these vectorized representation is emblematic for how anomalous (or not) it is for an entity to be associated with (e.g send a request from) an IPv4 address.

Neural networks are almost exactly like they sound, its a machine learning system that is supposed to behave similar to the human brain complete with computerized neurons and synapses. In unsupervised machine learning the algorithm can suss out what "good" (i.e. True Negative) looks like versus "bad" (i.e. True Positive) by looking at the association between all IPv4 Address and their paired entities and identify what vectors are similar to the others by their "distance". In IP Insights case, a prebuilt encoder is provided that looks for IPv4 addresses and then hashes out all entities into clusters and iterates over them using vectorization which is a way to perform computations as a matrix instead of looping over them (think of a "For" loop for a list containing tens of millions of values).

When you are training an IP Insights model it will actually create itself false positives by pairing IPv4 addresses with entities that have a far distance (i.e. highly anomalous) and are less likely to actually occur in reality, the model can now discriminate between True Positives, False Positives and True Negatives. This is done to prevent another crazy ass term called "cross entropy" (AKA "log loss" as if that makes it better), and introduces another term, binary classification. IP Insights is essentially asking "what is the chance that this IP address paired with this entity is anomalous" which is what makes it binary, I think, so "yes it's bad" or "not it is not". The probability is represented as a value between 0 and 1, the goal of all machine learning models is to make this as close to 0 as possible, so predicting a value of 0.01 for something that is really 1 (known True Positive) would result in very high log loss. So, with all that said, by making purposely garbage data IP Insights helps to reduce that log loss (i.e. bad predictions) during training.

That brings us to the output from the endpoint. When you query it (either via batches or in near real-time using the `InvokeEndpoint` API) the response is an unbounded float that can be negative or positive and (from my tests) could have as much as 12 decimal points. The higher above 0 it is the more likely it is anomalous which is where your work begins. For this solution I chose anything above 0.03, which is largely notional, to get closer to the truth you should provide True Positives to the endpoint and see what your response is. Based on those findings, you could configure a tiered approach where you application may issue a 2nd factor challenge, raise an alert or block it outright depending on the score. The answer to the second part of the question is "Yes, I think so", training the model with user-agents paired with an IP is actually pretty sketchy. Now for other less volatile entities it feels like the intended usage.

#### 6. Are there any other considerations for training and using IP Insights?
Like anything else, a machine learning algorithm is a tool, and it should be used properly. The first thing you should do is train a model per use case and don't use it like I am in this solution (for WAF requests and for CloudTrail logs), you will likely get inaccurate results which either results in False Positives, or False Negatives which are much worse. The AWS provided notebook for this solution generates nearly 4 million records to train the model so I would use that as a benchmark for how much data you will need. Likely your web applications (and your CloudTrail) is generating over that in the matter of hours depending on your scale. Since WAF and CloudTrail are both in JSON format it is very simple to grab your IP address and entity pair and write them to a CSV. If you do decide to use user-agent, either remove (using Python's `replace()`) or escape special characters and periods, when I gave user-agent and IP pairs to the endpoint it would choke on periods since the encoder (probably) uses a regex the detect the IPv4 addresses.

#### 7. What threat intelligence feeds should I use? What happens if there are duplicates?
In the solution I provide some example feeds that you should use, some are pretty obvious like the cybercrime domain feed, Emerging Threats and CI-badguys. In my real job I work with one of the most talented cyber threat intelligence specialists in the entire world, no joke she is awesome, so she also had some secondary influence on the choices. Just like machine learning models and anything else you will build, you should try to tailor your threat intel feeds and aggregation to match what your current threat environment is. I cannot tell you which is the best suited so I give popular ones, but ideally you should try to rely on sources and do your own analysis and correlation based on threats facing your organizations, whether those threats manifest in targeted malware campaigns in your vertical or you know certain state-sponsored groups want to target you.

As far as duplicates MISP will call that out within the console, to combat that I only specify a hash key in the DynamoDB tables to enforce uniqueness, so even if there are 5 feeds reporting on the same IPv4 address only one will make it to the table. 

#### 8. I did a look up against the raw log sources in S3 and I am not seeing the entries in Elasticsearch, why is this?
Most log delivery from AWS is "best effort" there is not an official SLA published but I would assume it is around 99.5 - 99.9% where anything in that last 0.5 - 0.1% will not be delivered. "Production" traffic is also first class in AWS, if there are network bandwidth constraints it will default to delivering connectivity back to clients versus sending out logs. The more likely event is that the raw log file was too large for Lambda to process the entire thing in time, you see this a lot when you are being hosed by a DOS or crawler from the same client IP, WAF and ALB bundle log files by the caller from what I can tell and if you absorb 100s of requests the log file can be very large.

#### 9. I have an existing Elasticsearch Service domain in a VPC, will this solution work?
You will either need to place the Lambda functions into a VPC and attach VPC Endpoints for S3, DynamoDB, and CloudWatch Logs or modify the solution to publish the final formatted logs into Kinesis Data Firehose and point them to you ES Domain in a VPC. There are additional costs for this and Lambda in a VPC, especially for dozens of concurrent invocations, will likely lead to more problems. Unless you absolutely have to isolate all traffic within your VPC to meet compliance requirements I would not go down that road.

#### 10. Can I publish these log sources to Splunk instead?
You can if you modify the solution to publish the final formatted logs into Kinesis Data Firehose and point them to Splunk. I was going to do that, but, Firehose is an expensive addition (especially if in a VPC) so it was easier to just use the Requests-AWS4Auth library to publish directly into a non-VPC ES domain.

#### 11. Will you support any other logging sources 
I hope to have support for Route 53 DNS Logs, S3 Access Logs, CloudFront Access Logs and API Gateway Access Logs and maybe some other host-based logs in the future.

#### 12. Why did you use the CloudWatch Agent instead of the Kinesis Data Agent?
I would have preferred to use to Kinesis Data Agent honestly but I found a lot of issues with it, it is not included by default in Amazon Linux 2 and now that Ubuntu 18.04LTS AMI's come with Java 11 pre-installed I was running into backwards compatability issues with the Agent as it fails the build unless you have OpenJDK 8 or 9. It was much easier to install the CloudWatch Agent as it is frequently updated with new features and there is Systems Manager Document support for configuration and it even has a wizard for installation. If AWS ever takes the Kinesis Data Agent support as serious as CloudWatch Agent I may switch to it as I'd much rather publish to Kinesis Data Firehose directly for certain host-based logs (Suricata, Squid, Nginx, Apache) versus using CloudWatch Logs as an intermediary.

#### 13. My DynamoDB table for IPv4-based IOCs from MISP has tens of thousands of entries but my WAF IP Set has just a little under 10,000! What gives?!
WAF IP Sets only accepted 10,000 addresses as a hard limit per IP Set, super annoying but there is nothing I can do about that. I used some hacky Python magic to take the last 10,000 values from the list I generate by parsing through the text files I write out from the DynamoDB tables, it is the only way to ensure that your IP set will get updated.

## Contributing
I am happy to accept PR's for items tagged as "Help Wanted" in Issues or the Project Board. I will review any other proposed PRs as well if it meets the spirit of the project.

## License
This library is licensed under the GNU General Public License v3.0 (GPL-3.0) License. See the LICENSE file.