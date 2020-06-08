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
-	IP Insights model from Amazon Sagemaker determines if IP address and entity pairs are anomalous
-	Dynamically update AWS WAF IP Sets and Amazon GuardDuty Threat Lists to bolster protection of your account and infrastructure from known threats

## Description
SyntheticSun is built around the usage of the Malware Information Sharing Platform (MISP) which is an open-source and community driven threat intelligence platform (TIP) and the IP Insights Amazon Sagemaker unsupervised machine learning algorithm to provide the core threat defense capabilities. MISP comes with dozens of out-of-the-box feeds that provide IP-address, URL, and domain/hostname-based indicators of compromise (IOC). MISP also has some compatibility with STIX/TAXII feeds from importing commercial and open-source feeds in those formats, such as Anamoli’s ThreatStream or STAXX platform, respectively.

AWS serverless technologies such as Lambda, DynamoDB, CodeBuild, EventBridge / CloudWatch Events and Kinesis are used for their ability to rapidly scale, their ease of use, and relatively cheap costs versus heavy MapReduce or Glue ETL-based data engineering jobs. All code is written in Python 3.8 and uses basic modules such as requests, json, ipaddress, socket and os to perform most of the extraction, transformation, and loading (ETL) into downstream services. All geolocation information is provided by ip-api.com, it does not require an account or paid tiers and has a great API which also includes throttling information in their response headers.

Outside of some basic configuration that needs to be done in MISP and artifacts being uploaded to an S3 bucket, this entire solution is automated and easily deployed (and sharable) via CloudFormation. Besides the usage of an EC2 instance for MISP and Elasticsearch Service it is 98% Serverless (since that matters to people). One thing I would not use in production is my pre-trained IP Insights model, I used traffic from my honeypots and AWS training data from the Jupyter notebook to train it and it’ll most likely not fit your use case. I am also 99% sure I am using it wrong, but whatever.

## Setting Up
SyntheticSun is spread across three Stages due to the size of solution and the required dependencies. All architecture and installation instructions (and perhaps FAQs where needed) will live within their own Stage.

### Before you start: Considerations for Production deployments
SyntheticSun, by virtue of being something you found on GitHub, is a proof-of-concept and therefore I did not go the extra mile for the first release to absolutely harden everything. Provided you are reading this at a point in time where I have not made the necessary changes, consider the following before you deploy this solution into a production-like environment. I will put these items on a roadmap and update them as appropiate.

1. Train your own IP Insights models. I used a mix of computer generated data and various other host-level and managed service logs. You should absolutely train a model per data set you are trying to detect anomalies in and use another entity other than the user agents from WAF and ALB logs.
2. Deploy your MISP server and Elasticsearch Service domain in a VPC to harden against internet-borne attacks. Consider using AWS' Client VPN, AWS Site-to-Site VPN, DirectConnect, Amazon Workspaces, AppStream 2.0 or (if you absolutely have to) a reverse-proxy to access the MISP console and Kibana within a VPC.
3. Consider using Cognito for AuthN into Kibana. Go a step further an federate your User Pool with your corporate IdP.
4. Consider baking your own AMI for MISP, or better yet, use Fargate or EKS to host it. I would also consider pre-baking Suricata and the Amazon CloudWatch Agent into future builds to help scale deployments of agents and HIDPS across your estate.
5. Modify your Suricata configuration to suit the needs of your SecOps teams looking at the logs, all this solution does is dump them in, also consider writing your own rules or importing other sources to harden your hosts against attacks.

### Prerequisites
- Admin access to an AWS Account (if using in a multi-account deployment you must be in the account where your Masters or Delegated Admin Masters are located)
- Application Load Balancer (ALB) with at least one target instance and access logs enabled
- CloudTrail logging enabled in your account
- One VPC with at least 1 private subnet (route to NATGW), 1 public subnet (route to IGW) and VPC Flow Logs enabled and published to CloudWatch Logs

**[Phase 1 starts here](https://github.com/jonrau1/SyntheticSun/readme-stage1)**


## FAQ
#### 1. Why should I use this solution?
SyntheticSun is an easy way to start using cyber threat intelligence and machine learning for your edge protection security use cases on the AWS Cloud without having to invest in one or more commercial tools or a data scientist for your security team. This solution, after initial configuration, is fully automated allowing you to identify and respond to threats at machine speed. Finally, this solution provides basic visualizations for your incident response team to use for threat response, such as allowed inbound or outbound connections or DNS queries to / from IP addresses or domains deemed to be malicious. The core of the solution relies on very lightweight automation and data engineering pipelines, which theoretically, can be reused for other purposes where multi-stage normalization and enrichment or scheduled fast-paced batch jobs are needed.

#### 2. Who should use this solution?
Firstly, if you are making use or GuardDuty and/or AWS WAF it may make sense to evaluate this solution, but it is also a requirement. Obvious personas who can take advantage are product teams responsible for securing their full stack and lack the capital or expertise to model, train and deploy machine learning algorithms or operationalize cyber threat intelligence feeds in a meaningful way. Those aforementioned personas are likely security engineering, SecOps / SOC analysts & engineers or a DevSecOps engineer, but that list is not exhaustive, and they do not need to be product / application-aligned as central teams can use this as well. Another usage is those same personas (SecOps, security engineering) that work for a centralized team and want to create a dynamic block list for firewalls and intrusion prevention systems, the CodeBuild projects can be repurposed to drop CSV or flat files to almost any location (e.g. Palo Alto firewalls, Squid forward proxy URL filters, etc.)

#### 3. What are the gaps in this solution?


#### 4. Outside of the Masters for the AWS Security Services, what considerations are there for an Organizational deployment?
The easiest way to deploy this solution for an organization is to deploy it as suggested in FAQ #3 where all of your centralized security and management services are located. For the lower-level telemetry such as VPC Flow Logs and WAF Logs, you should split those elements out of the main CloudFormation template into their own and share them across your organization in AWS Service Catalog or in another centralized area. You will need to evaluate your shard consumption and index rotation of Elasticsearch Service, as well as the permissions, if you will be having cross-account Kinesis Data Firehose delivery streams publishing into a centralized location.

I built this solution in my personal sandbox account, hence why I did not bake any of the considerations from above into the solution, I will be happy to work on a PR with this in mind and may do it myself in the future.

#### 5. What is the IP Insights algorithm? Is your usage really what it was intended for?
**CAVEATS**: I am not a data scientist and this is going to be a long answer. Tl;dr: It's an anomaly finder and I think?

Given that I am not remotely close to a data scientist or have any training you are better served [reading the docs](https://docs.aws.amazon.com/sagemaker/latest/dg/ip-insights-howitworks.html) on this. That said, here is my layman's attempt at it, IP Insights is an unsupervised machine learning algorithm that learns the relationship between an IPv4 address and an entity (e.g. Account number, user name, user-agent) and tried to determine how likely it is that the entity would use that IPv4 address. Behind the curtains of IP Insights is a neural network that learns the latent vector representation of these entities and IPv4 addresses and the distance betweens these vectorized representation is emblematic for how anomalous (or not) it is for an entity to be associated with (e.g send a request from) an IPv4 address.

Neural networks are almost exactly like they sound, its a machine learning system that is supposed to behave similar to the human brain complete with computerized neurons and synapses. In unsupervised machine learning the algorithm can suss out what "good" (i.e. True Negative) looks like versus "bad" (i.e. True Positive) by looking at the association between all IPv4 Address and their paired entities and identify what vectors are similar to the others by their "distance". In IP Insights case, a prebuilt encoder is provided that looks for IPv4 addresses and then hashes out all entities into clusters and iterates over them using vectorization which is a way to perform computations as a matrix instead of looping over them (think of a "For" loop for a list containing tens of millions of values).

When you are training an IP Insights model it will actually create itself false positives by pairing IPv4 addresses with entities that have a far distance (i.e. highly anomalous) and are less likely to actually occur in reality, the model can now discriminate between True Positives, False Positives and True Negatives. This is done to prevent another crazy ass term called "cross entropy" (AKA "log loss" as if that makes it better), and introduces another term, binary classification. IP Insights is essentially asking "what is the chance that this IP address paired with this entity is anomalous" which is what makes it binary, I think, so "yes it's bad" or "not it is not". The probability is represented as a value between 0 and 1, the goal of all machine learning models is to make this as close to 0 as possible, so predicting a value of 0.01 for something that is really 1 (known True Positive) would result in very high log loss. So, with all that said, by making purposely garbage data IP Insights helps to reduce that log loss (i.e. bad predictions) during training.

That brings us to the output from the endpoint. When you query it (either via batches or in near real-time using the `InvokeEndpoint` API) the response is an unbounded float that can be negative or positive. The higher above 0 it is the more likely it is anomalous which is where your work begins. For this solution I chose anything above 0.03, which is largely notional, to get closer to the truth you should provide True Positives to the endpoint and see what your response is. Based on those findings, you could configure a tiered approach where you application may issue a 2nd factor challenge, raise an alert or block it outright depending on the score. The answer to the second part of the question is "Yes, I think so", training the model with user-agents paired with an IP is actually pretty sketchy. Now for other less volatile entities (account number, user name, IAM user) it feels like the intended usage.

#### 6. Are there any other considerations for training and using IP Insights?
Like anything else, a machine learning algorithm is a tool, and it should be used properly. The first thing you should do is train a model per use case and don't use it like I am in this solution (for WAF requests and for CloudTrail logs), you will likely get inaccurate results which either results in False Positives, or False Negatives which are much worse. The AWS provided notebook for this solution generates nearly 4 million records to train the model so I would use that as a benchmark for how much data you will need. Likely your web applications (and your CloudTrail) is generating that in a matter of hours depending on your scale. Since WAF and CloudTrail are both in JSON format it is very simple to grab your IP address and entity pair and write them to a CSV. If you do decide to use user-agent, either remove (using Python's `replace()`) or escape special characters and periods, when I gave user-agent and IP pairs to the endpoint it would choke on periods since the encoder (probably) uses a regex the detect the IPv4 addresses.

#### 7. What threat intelligence feeds should I use? What happens if there are duplicates?
In the solution I provide some example feeds that you should use, some are pretty obvious like the cybercrime domain feed, Emerging Threats and CI-badguys. In my real job I work with one of the most talented cyber threat intelligence specialists in the entire world, no joke she is awesome, so she also had some secondary influence on the choices. Just like machine learning models and anything else you will build, you should try to tailor your threat intel feeds and aggregation to match what your current threat environment is. I cannot tell you which is the best suited so I give popular ones but ideally you should try to rely on sources and do your own analysis and correlation based on threats facing your organizations, whether those threats manifest in targeted malware campaigns in your vertical or you know certain state-sponsored groups want to target you.

As far as duplicates MISP will call that out within the console, to combat that I only specify a hash key in the DynamoDB tables to enforce uniqueness, so even if there are 5 feeds reporting on the same IPv4 address only one will make it to the table. 

#### 8. I did a look up against the raw log sources in S3 and I am not seeing the entries in Elasticsearch, why is this?
Most log delivery from AWS is "best effort" there is not an official SLA published but I would assume it is around 99.5 - 99.9% where anything in that last 0.5 - 0.1% will not be delivered. "Production" traffic is also first class in AWS, if there are network bandwidth constraints it will default to delivering connectivity back to clients versus sending out logs. The more likely event is that the raw log file was too large for Lambda to process the entire thing in time, you see this a lot when you are being hosed by a DOS or crawler from the same client IP, WAF and ALB bundle log files by the caller from what I can tell and if you absorb 100s of requests the log file can be very large.

#### 9. I have an existing Elasticsearch Service domain in a VPC, will this solution work?
You will either need to place the Lambda functions into a VPC and attach VPC Endpoints for S3, DynamoDB, and CloudWatch Logs or modify the solution to publish the final formatted logs into Kinesis Data Firehose and point them to you ES Domain in a VPC. There are additional costs for this and Lambda in a VPC, especially for dozens of concurrent invocations, will likely lead to more problems from ENIs sticking around and eating your RFC1918 space. Unless you absolutely have to isolate all traffic within your VPC to meet compliance requirements I would not go down that road.

#### 10. Can I publish these log sources to Splunk instead?
You can if you modify the solution to publish the final formatted logs into Kinesis Data Firehose and point them to Splunk.

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