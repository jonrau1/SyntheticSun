# SecurityDataSomething
Proof of concept for an AWS Security Data Lake. Ingest, normalize, analyze and visualize major sources of security telemetry.

*"...and then I told that CISO 'data lake, surely you jest, you mean a dAtA sWaMp' lol"*</br>
<sub>- **your CTO, probably**</sub>

## Description
SecurityDataSomething is an initiative to model a minimum viable product (MVP) for a seucirty data lake on AWS to ingest, normalize, analyze and visualize major sources of security telemetry such as AWS CloudTrail, WAF Logs, ALB Access Logs and other primary sources of information. SecurityDataSomething will utilize native tools such as Lake Formation, Elasticsearch Service, Sagemaker, Lambda, S3, Glue, Kinesis and various Event types (EventBridge, S3, etc.) to ingest, normalize, analyze and visualize the different log types. Some elements of SecurityDataSomething will build heavily on the detection, response and integration elements of [ElectricEye](https://github.com/jonrau1/ElectricEye). You should consider using that solution to familiarize yourself with service / infrastucture-level security best practices, automation and response on AWS.

SecurityDataSomething has two outcomes: the first (and obvious) outcome is to create a free, easy-to-use POC for a security data lake and the second is to help ease the burden of a security team operating on AWS that may be struggling with too many raw alerts or not being able to centralize and effecitely action on the telemetry (creating alerts, generating insights, hunting threats).

With those outcomes in mind, there are three goals SecurityDataSomething has:
1. Easily and quickly deployable across multiple AWS accounts / environments utilizing AWS services as much as possible
2. Data leaving the lake is well-structured and enriched with security-relevant data points
3. Utilize ML and big data analytics to infer insights quicker
4. Scenario-specific visualizations and investigation runbooks that a security operations team can quickly operationalize

## Solution Architecture