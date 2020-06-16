# SyntheticSun
SyntheticSun is a defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats.

*You sleep in fragmented glass*</br>
*With reflections of you,*</br>
*But are you feeling alive?*</br>
*Yeah let me ask you,*</br>
*Are you feeling alive?*</br>
<sub>- **Norma Jean, 2016**</sub>

[![DepShield Badge](https://depshield.sonatype.org/badges/owner/repository/depshield.svg)](https://depshield.github.io)

## Synopsis
- Uses event- and time-based serverless automation (e.g. AWS CodeBuild, AWS Lambda) to collect, normalize, enrich, and correlate security telemetry in Kibana
- Leverages threat intelligence, geolocation data, open-source intelligence, machine learning (ML) backed anomaly detection and AWS APIs to further enrich security telemetry and identify potential threats
- Leverage Random Cut Forests (RCF) and IP Insights unsupervised ML algorithms to identify anomalies in timeseries and IP-entity pair data, respectively. Serverless, container-orchestrated resources are provided to train and deploy new IP Insights endpoints at will.
- Dynamically update AWS WAFv2 IP Sets and Amazon GuardDuty threat intel sets to bolster protection of your account and infrastructure against known threats 

## Description
SyntheticSun is built around the usage of the Malware Information Sharing Platform (MISP) and Anomali's LIMO which are community driven threat intelligence platforms (TIPs) that provide various types of indicators of compromise (IoC). Normalized and de-duplicated threat intel is looked up against in near-real time to quickly identify known threats in various types of network traffic. To add dynamism to the identification of potential threats IP Insights models are deployed to find anoamlies (and potential threats therein) between the pairing of IP addresses and entities (such as IAM principal ID's, user-agents, etc.), native RCF detectors are also used in Elasticsearch to find anomalies in near real-time security telemetry as it is streamed into Kibana. To democratize the usage and fine-tuning of ML models within security teams, utilities to train IP Insights models are provided as an add-on to the core solution.

To perform the both the orchestration and automation as well as extraction, transformation, and loading (ETL) of security telemetry into Kibana various AWS serverless technologies such as Lambda, DynamoDB, and CodeBuild are used. Serverless technologies such as these are used for their scalability, ease of use, relatively cheap costs versus heavy MapReduce or Glue ETL-based solutions. A majority of the solution is deployed via CloudFormation with helper scripts in Python and shell provided throughout the various Stages to promote adoption and the potential deployment in continuous integration pieplines.

To make the "guts" of the solution as lean as possible basic Python libraries such as `requests`, `json`, `ipaddress`, `socket` and `re` to perform most of the extraction, transformation, and loading (ETL) into downstream services. All geolocation information is provided by [ip-api.com](https://ip-api.com/docs), it does not require an account or paid tiers and has a great API which includes throttling information in their response headers. A majority of the Elasticsearch and Kibana dependencies are also provided in code (indicies, mappings, visualizations, etc) to avoid manual configuration of either.

## Setting Up
SyntheticSun is spread across three Stages due to the size of solution and the required dependencies. All architecture and installation instructions (and FAQs where appropriate) will live within their own Stage. Add-ons modules (called an Appendix) are also provided to extend the functionality, they too have their own architecture and installation instructions localizzed.

### Before you start: Considerations for Production deployments
SyntheticSun, by virtue of being something you found on GitHub, is a proof-of-concept and therefore I did not go the extra mile for the first release to absolutely harden everything. Provided you are reading this at a point in time where I have not made the necessary changes, consider the following before you deploy this solution into a production environment (or any environment with heightened security needs). I will put these items on a roadmap and update them as appropiate.

1. Train your own IP Insights models using the examples provided in [Appendix A](https://github.com/jonrau1/SyntheticSun/tree/master/appendix-a-ipinsights). Using your own data, and continually retraining the model, will help accurize findings.
2. Deploy your MISP server and Elasticsearch Service domain in a VPC to harden against internet-borne attacks. Consider using AWS' Client VPN, AWS Site-to-Site VPN, DirectConnect, Amazon Workspaces, AppStream 2.0 or (if you absolutely have to) a reverse-proxy to access the MISP console and Kibana within a VPC.
3. Consider using Cognito for AuthN into Kibana. Go a step further an federate your User Pool with your corporate IdP.
4. Consider baking your own AMI for MISP or use Fargate to host it. I would also consider pre-baking Suricata and the Amazon CloudWatch Agent into future builds to help scale deployments of agents and HIDPS across your estate.
5. Modify your Suricata configuration to suit the needs of your SecOps teams looking at the logs, all this solution does is dump them in, also consider writing your own rules or importing other sources to harden your hosts against attacks.

### Prerequisites
- Admin access to an AWS Account (if using in a multi-account deployment you must be in the account where your Masters or Delegated Admin Masters are located)
- Application Load Balancer (ALB) with at least one target instance and access logs enabled
- CloudTrail logging enabled in your account
- One VPC with at least 1 private subnet (route to NATGW), 1 public subnet (route to IGW) and VPC Flow Logs enabled and published to CloudWatch Logs

**[Stage 1 starts here](https://github.com/jonrau1/SyntheticSun/tree/master/readme-stage1)**

## FAQ

#### 1. Why should I use this solution?
SyntheticSun is an easy way to start using cyber threat intelligence and machine learning for your edge protection security use cases on the AWS Cloud without having to invest in one or more commercial tools or a data scientist for your security team (you should actually do the latter). This solution, after initial configuration, is fully automated allowing you to identify and respond to threats at machine speed. Finally, this solution provides basic visualizations for your incident response team to use for threat response, such as allowed inbound or outbound connections or DNS queries to / from IP addresses or domains deemed to be malicious. The core of the solution relies on very lightweight automation and data engineering pipelines, which theoretically, can be reused for other purposes where multi-stage normalization and enrichment or scheduled fast-paced batch jobs are needed.

#### 2. Who should use this solution?
Firstly, if you are making use or GuardDuty and/or AWS WAF it may make sense to evaluate this solution, but it is also a requirement. Obvious personas who can take advantage are product teams responsible for securing their full stack and lack the capital or expertise to model, train and deploy machine learning algorithms or operationalize cyber threat intelligence feeds in a meaningful way. Those aforementioned personas are likely security engineering, SecOps / SOC analysts & engineers or a DevSecOps engineer, but that list is not exhaustive, and they do not need to be product / application-aligned as central teams can use this as well. Another usage is those same personas (SecOps, security engineering) that work for a centralized team and want to create a dynamic block list for firewalls and intrusion prevention systems, the CodeBuild projects can be repurposed to drop CSV or flat files to almost any location (e.g. Palo Alto firewalls, Squid forward proxy URL filters, etc.)

#### 3. What are the gaps in this solution?
Lack of full coverage across all main log sources - namely S3 Access Logs and CloudFront Access Logs which are integral to the way a lot of folks deliver services (especially for SPAs on S3 buckets). The anomaly detection does not extend past WAF, API Gateway Access Logs or CloudTrail due to my obsession with IP Insights and complete lack of any data science training (seriously, I don't even know how to use pandas or numpy). There is not any in-depth analysis of raw threat intelligence IoCs other than attempting to match it in the logs.

#### 4. Outside of the Masters for the AWS Security Services, what considerations are there for an Organizational deployment?
The easiest way to deploy this solution for an organization is to deploy it in a centralized security services account. For the lower-level telemetry such as VPC Flow Logs and WAF Logs, you should consider providing helper scripts or CloudFormation templates via AWS Service Catalog to promote enablement in lower environments. You will need to evaluate your shard consumption and index rotation of Elasticsearch Service, as well as the permissions, if you will be having cross-account Kinesis Data Firehose delivery streams publishing into a centralized location. I built this solution in my personal sandbox account, hence why I did not bake any of the considerations from above into the solution, I will be happy to work on a PR with this in mind and may do it myself in the future.

#### 5. What is the IP Insights algorithm? Is your usage really what it was intended for?
**CAVEATS**: I am not a data scientist and this is going to be a long answer. Tl;dr: It's an anomaly finder and I think?

Given that I am not remotely close to a data scientist or have any training you are better served [reading the docs](https://docs.aws.amazon.com/sagemaker/latest/dg/ip-insights-howitworks.html) on this. That said, here is my layman's attempt at it, IP Insights is an unsupervised machine learning algorithm that learns the relationship between an IPv4 address and an entity (e.g. Account number, user name, user-agent) and tried to determine how likely it is that the entity would use that IPv4 address. Behind the curtains of IP Insights is a neural network that learns the latent vector representation of these entities and IPv4 addresses and the distance betweens these vectorized representation is emblematic for how anomalous (or not) it is for an entity to be associated with (e.g send a request from) an IPv4 address.

Neural networks are almost exactly like they sound, its a machine learning system that is supposed to behave similar to the human brain complete with computerized neurons and synapses. In unsupervised machine learning the algorithm can suss out what "good" (i.e. True Negative) looks like versus "bad" (i.e. True Positive) by looking at the association between all IPv4 Address and their paired entities and identify what vectors are similar to the others by their "distance". In IP Insights case, a prebuilt encoder is provided that looks for IPv4 addresses and then hashes out all entities into clusters and iterates over them using vectorization which is a way to perform computations as a matrix instead of looping over them (think of a "For" loop for a list containing tens of millions of values).

When you are training an IP Insights model it will actually create itself false positives by pairing IPv4 addresses with entities that have a far distance (i.e. highly anomalous) and are less likely to actually occur in reality, the model can now discriminate between True Positives, False Positives and True Negatives. This is done to prevent another crazy ass term called "cross entropy" (AKA "log loss" as if that makes it better), and introduces another term, binary classification. IP Insights is essentially asking "what is the chance that this IP address paired with this entity is anomalous" which is what makes it binary, I think, so "yes it's bad" or "not it is not". The probability is represented as a value between 0 and 1, the goal of all machine learning models is to make this as close to 0 as possible, so predicting a value of 0.01 for something that is really 1 (known True Positive) would result in very high log loss. So, with all that said, by making purposely garbage data IP Insights helps to reduce that log loss (i.e. bad predictions) during training.

That brings us to the output from the endpoint. When you query it (either via batches or in near real-time using the `InvokeEndpoint` API) the response is an unbounded float that can be negative or positive. The higher above 0 it is the more likely it is anomalous which is where your work begins. For this solution I chose anything above 0.03, which is largely notional, to get closer to the truth you should provide True Positives to the endpoint and see what your response is. Based on those findings, you could configure a tiered approach where you application may issue a 2nd factor challenge, raise an alert or block it outright depending on the score. The answer to the second part of the question is "Yes, I think so", training the model with user-agents paired with an IP is actually pretty sketchy. Now for other less volatile entities (account number, user name, IAM user) it feels like the intended usage.

#### 6. What threat intelligence feeds should I use? What happens if there are duplicates?
In the solution I provide some example feeds that you should use, some are pretty obvious like the cybercrime domain feed, Emerging Threats and CI-badguys. In my real job I work with one of the most talented cyber threat intelligence specialists in the entire world, no joke she is awesome, so she also had some secondary influence on the choices. Just like machine learning models and anything else you will build, you should try to tailor your threat intel feeds and aggregation to match what your current threat environment is. Duplicates are identified in MISP and only a hash key is specified in the DynamoDB tables to enforce uniqueness, so even if there are 5 feeds reporting on the same IPv4 address only one will make it to the table.

#### 7. I did a look up against the raw log sources in S3 and I am not seeing the entries in Elasticsearch, why is this?
Most log delivery from AWS is "best effort" there is not an official SLA published but I would assume it is around 99.5 - 99.9% where anything in that last 0.5 - 0.1% will not be delivered. "Production" traffic is also first class in AWS, if there are network bandwidth constraints it will default to delivering connectivity back to clients versus sending out logs. The more likely event is that the raw log file was too large for Lambda to process the entire thing in time, you see this a lot when you are being hosed by a DOS or crawler from the same client IP, WAF and ALB bundle log files by the caller from what I can tell and if you absorb 100s of requests the log file can be very large.

#### 8. I have an existing Elasticsearch Service domain in a VPC, will this solution work?
You will either need to place the Lambda functions into a VPC and attach VPC Endpoints for S3, DynamoDB, and CloudWatch Logs or modify the solution to publish the final formatted logs into Kinesis Data Firehose and point them to you ES Domain in a VPC. There are additional costs for this and Lambda in a VPC, especially for dozens of concurrent invocations, will likely lead to more problems from ENIs sticking around and eating your RFC1918 space. Unless you absolutely have to isolate all traffic within your VPC to meet compliance requirements I would not go down that road.

#### 9. Can I publish these log sources to Splunk instead?
You can if you modify the solution to publish the final formatted logs into Kinesis Data Firehose and point them to Splunk.

#### 10. Will you support any other logging sources 
I hope to have support for Route 53 DNS Logs, S3 Access Logs, CloudFront Access Logs ~~and API Gateway Access Logs~~ and maybe some other host-based logs in the future.

#### 11. Why did you use the CloudWatch Agent instead of the Kinesis Data Agent?
I would have preferred to use to Kinesis Data Agent honestly but I found a lot of issues with it, it is not included by default in Amazon Linux 2 and now that Ubuntu 18.04LTS AMI's come with Java 11 pre-installed I was running into backwards compatability issues with the Agent as it fails the build unless you have OpenJDK 8 or 9. It was much easier to install the CloudWatch Agent as it is frequently updated with new features and there is Systems Manager Document support for configuration and it even has a wizard for installation. If AWS ever takes the Kinesis Data Agent support as serious as CloudWatch Agent I may switch to it as I'd much rather publish to Kinesis Data Firehose directly for certain host-based logs (Suricata, Squid, Nginx, Apache) versus using CloudWatch Logs as an intermediary.

#### 12. My DynamoDB table for IPv4-based IOCs from MISP has tens of thousands of entries but my WAF IP Set has just a little under 10,000! What gives?!
WAF IP Sets only accepted 10,000 addresses as a hard limit per IP Set, super annoying but there is nothing I can do about that. I used some hacky Python magic to take the last 10,000 values from the list I generate by parsing through the text files I write out from the DynamoDB tables, it is the only way to ensure that your IP set will get updated.

## Contributing
I am happy to accept PR's for items tagged as "Help Wanted" in Issues or the Project Board. I will review any other proposed PRs as well if it meets the spirit of the project.

## License
This library is licensed under the GNU General Public License v3.0 (GPL-3.0) License. See the LICENSE file.