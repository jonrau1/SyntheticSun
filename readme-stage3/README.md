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

**Note 1:** If you trained new models in [Appendix A](https://github.com/jonrau1/SyntheticSun/tree/master/appendix-a-ipinsights) ensure that they are uploaded under the same names (e.g. `ct-model.tar.gz` or `waf-model.targ.gz`) they have in Stage 1. These values are hardcoded in the CFN template and will need to be manually changed if you named your model artifacts differently.

**Note 2:** You will likely need to manually add the respective Lambda function roles to the S3 bucket policies for your CloudTrail, WAF and/or ALB.

**Note 3:** Manually download the `kibana-objects.ndjson` file in this directory to your workstation. You will need to manually upload it to Kibana that way.

3. After the stack finishes creating execute another Python script to generate a resource-based IAM policy for the Elasticsearch Service domain. This script uses the `sys.argv` method to create variables from values provided to the command line. The below 2 values must be provided in the order they are given.
```bash
python3 es-policy.py \
    my-aws-region (us-east-1) \
    trusted-cidr (e.g. 192.168.1.1/32) 
```

**Note:** If you are unable to apply the policy due to being blocked set the Access Policy in the console to allow everyone to access and try again.

4. After the Elasticsearch Service domain is back in an available state after applying the policy login to Kibana by selecting the **Kibana** endpoint URL in the Elasticsearch console.

5. In Kibana select the **Management** menu, select **Saved Objects** and choose **Import** in the top-right. When prompted select the `kibana-objects.ndjson` you saved to your desktop. You may need to refresh and/or closer all browser sessions if you encounter redirect attempts to create any indicies.
![Kibana Import Objects](https://github.com/jonrau1/SyntheticSun/blob/master/img/kibana-importobjects.JPG)

6. Navigate to **Dashboard**, select the **SyntheticSun Fusion Center** and change the time filter at the top right to **1 Year**. This will allow you to see all data for your indicies. If there is missing data check the logs of all Lambda functions and for the Security Hub Kinesis Firehose. All Lambda functions will publish immediately, but they may have some other transient errors. Security Hub will only send new events published after Step 2, check the Firehose logs and the S3 error file bucket if you suspect an issue.
![Kibana Dashboard](https://github.com/jonrau1/SyntheticSun/blob/master/img/kibana-dashboard.JPG)

To add additional ML-based anomaly detection we will use [Random Cut Forest](https://docs.aws.amazon.com/sagemaker/latest/dg/randomcutforest.html) (RCF) detectors that are now included with Elasticsearch Service after being forked from the [Open Distro for Elasticsearch](https://opendistro.github.io/for-elasticsearch/blog/odfe-updates/2019/11/random-cut-forests/). RCF will allow us to identify anomalies in time-series data, which is a perfect fit for Elasticsearch, we will create two different detectors - one for ALB and one for VPC flow logs to detect possible Distribute Denial of Service (DDOS) threat vectors coming from anomalies in the amount of packets / bytes that are received. Finally, we will use another Open Distro feature called [Monitors](https://aws.amazon.com/blogs/big-data/setting-alerts-in-amazon-elasticsearch-service/) to receive alerts about this anomalous activity.

7. Navigate to the **Open Distro for Elasticsearch Anomaly Detection Kibana plugin** (yes, they actually named it that) and choose **Create detector**. Enter a **Name**,  **Description** and choose the `vpc-flows` index as shown below.
![Kibana Create Detector](https://github.com/jonrau1/SyntheticSun/blob/master/img/kibana-createdetector.JPG)

8. Select a value for **Timestamp field**, scroll to the bottom and enter `3` for **Detector interval** and `1` for **Window delay** and choose **Create**
![Kibana Create Detector](https://github.com/jonrau1/SyntheticSun/blob/master/img/kibana-intervaldetector.JPG)

9. On the next screen select **Add feature**. Enter a **Name** (i.e. `FlowLog-Pckts`) and select **Custom expression** from the **Find anomalies based on** dropdown menu. Enter in the below JSON blob, scroll to the bottom, select **Save and start detector** and select **Confirm** at the next pop up.
```json
{
    "aggregation_name": {
        "sum": {
            "field": "packets"
        }
    }
}
```

**Important note:** If you do not have at least 500 data points you will generate warning message when selecting **Preview anomalies**. Even with 500 data points, the RCF plugin will take a 50:1 sampling which can lead to a skewed visual. Finally, it can take a signifigant amount of time for the detector to initialize and begin to deliver anomaly and confidence scores depending on the existing data points in your index and how many events per second (EPS) is generated.

10. Repeat Stpes 7 - 9 for ALB. When adding **Features** choose the `receivedBytes` value if available. If not, select **Custom expression** and enter in the below.
```json
{
    "aggregation_name": {
        "sum": {
            "field": "receivedBytes"
        }
    }
}
```

11. (**Note:** skip this step if you'll use Slack, Chime or a custom webhook which are native to Elasticsearch Monitors). Execute the following script to create two SNS topics and an IAM role to allow Elasticsearch to alert your topic for VPC and ALB anomaly detections: `python3 monitors.py`.

**Note:** Repeat Steps 12 - 15 for each detector you create

12. Navigate to **Alerting**, select the **Destinations** tab and choose **Add destination**. Enter a **Name**, choose **Amazon SNS** and enter in the ARN for the IAM Role and the SNS topic for that particular destination as shown below. You can reuse the same IAM Role for subsequent SNS destinations.
![Kibana Create Monitor Destination](https://github.com/jonrau1/SyntheticSun/blob/master/img/kibana-monitordest.JPG)

13. Select the **Monitor** tab and choose **Create monitor**. Enter a **Name**, under **Method of definition** choose **Define using anomaly detector** and select one of your detectors. Optionally customize the **Monitor schedule** and select **Create** as shown below.
![Kibana Configure Monitor](https://github.com/jonrau1/SyntheticSun/blob/master/img/kibana-configuremonitor.JPG)

14. On the next screen enter a **Trigger name** (e.g. `VPC-RCF-Alerts`) and optionally change the values for **Severity level**, **Anomaly grade threshold** and/or **Anomaly confidence threshold**. By default these values are set to `1`, `0.7` and `0.7`, respectively. Scroll to the bottom and enter another **Name**, choose your SNS topic for **Destination** and customize your **Message subject** and **Message**. You can enter in the below `Mustache` example to add result information to the message.
```yaml
Monitor {{ctx.monitor.name}} just entered alert status. Please investigate the issue.
- Trigger: {{ctx.trigger.name}}
- Severity: {{ctx.trigger.severity}}
- Period start: {{ctx.periodStart}}
- Period end: {{ctx.periodEnd}}
- Results: {{ctx.results.0}}
```

**Note:** For more information on the `Mustache` specification for Monitors refer [here](https://opendistro.github.io/for-elasticsearch-docs/docs/alerting/monitors/#available-variables).

15. For information about using Lambda with SNS refer [here](https://docs.aws.amazon.com/sns/latest/dg/sns-lambda-as-subscriber.html). You can publish to further downstream tools such as Jira, PagerDuty, ServiceNow, Azure DevOps Boards or Microsoft Teams. For examples on the aforementioned destinations refer to the [add-on modules](https://github.com/jonrau1/ElectricEye#add-on-modules) of ElectricEye.

## FAQ

### 1. Why am I seeing so many anomalies identified by IP Insights?
The most likely reason is you have not used Appendix A to train your own IP Insights models, or, those are all true positives and you're in the midst of an attack. What are you still doing here? Go verify!