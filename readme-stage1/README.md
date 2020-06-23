# SyntheticSun
SyntheticSun is a proof of concept (POC) defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats.

*"You sleep in fragmented glass"*</br>
*With reflections of you,"*</br>
*But are you feeling alive?"*</br>
*Yeah let me ask you,"*</br>
*Are you feeling alive?"*</br>
<sub>- **Norma Jean, 2016**</sub>

## Stage 1 - Environment setup
In this Stage we will deploy the baseline services such as WAFv2, MISP and Elasticsearch and execute helper scripts to prepare the artifacts needed for the full solution. Before starting clone and navigate to this repository: `git clone https://github.com/jonrau1/SyntheticSun && cd SyntheticSun/readme-stage1` and then install required Python libraries `pip3 install -r requirements.txt`.

### Deployment instructions
All commands ran from a Cloud9 Ubuntu 18.04LTS instance using Python 3.6 and the latest version of `awscli`, `boto3` and with an IAM instance profile

1. <localInstance> Deploy a CloudFormation stack from `SyntheticSun_SETUP_CFN.yaml`. This can take a few minutes due to the Elasticsearch Service domain. Keep a tab open to refer to the resources as you will need various names and ARN values for the next steps.

2. <localInstance> After the CloudFormation stack has sucessfully deployed execute the following to upload the baseline artifacts to S3.
`cd artifacts && aws s3 sync . s3://<artifact-bucket-name-here>`

3. <localInstance> Execute the following command to create a Lambda layer for the `requests-aws4auth` Python library from the ZIP file.
```bash
cd -
cd lambda-layer
aws lambda publish-layer-version \
    --layer-name aws4auth \
    --description "Python 3 Lambda layer for AWS4Auth Requests library" \
    --license-info "MIT-0" \
    --zip-file fileb://aws4auth-layer.zip \
    --compatible-runtimes python3.7 python3.8
```

4. <localInstance>  Execute another helper script to create the rest of the necessary resources and conditions required for the remainder of this solution. This final script uses the `sys.argv` method to create variables from values provided to the command line. The below 7 values must be provided in the order they are given. **Note:** For the Elasticsearch endpoint URL do *not* use the Kibana one and remove any trailing slash.

**Important:** Replace the helper values (e.g. `my-aws-region`). If you are using an instance profile / don't use a credentials profile ensure you keep the default value (`default`)
```bash
cd -
python3 gewalthaufen.py \
    my-credential-profile (default ) \
    my-aws-region (us-east-1) \
    vpc-id (vpc-123456) \
    waf-arn (from CFN e.g. arn:aws:wafv2:us-east-1:12345678:regional/webacl/SyntheticSun-WACL/waf-id-goes-here) \
    firehose-arn (from CFN e.g. arn:aws:firehose:us-east-1:12345678:deliverystream/aws-waf-logs-syntheticsun) \
    elasticsearch-endpoint (e.g. https://my-domain-elasticsearch.com) \
    misp-instance-id (i-123456789012)
```

5. <localInstance> Connect to your MISP instance via SSH. You can also try to use AWS Systems Manager Session Manager (`aws ssm start-session --target <misp-ec2-instance-id>`), however, the IAM role may not register the instance in time.

**Note:** Refer [here](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) for information on installating the Session Manager Plugin for the AWS CLI if you go the Session Manager route.

6. <MISPInstance> Execute the following commands to install Suricata. Replace the value of the S3 bucket for the artifacts bucket that was deployed by CloudFormation.
```bash
cd ~
sudo su
add-apt-repository ppa:oisf/suricata-stable
apt update
apt upgrade -y
apt install -y suricata
apt install -y awscli
cd /etc/suricata
aws s3 cp s3://<artifact-bucket-name-here>/suricata.yaml .
```

7. <MISPInstance> Check the adapter name by using `ifconfig`. If this value is anything other than `ens5` replace the value in `suricata.yaml` before moving onto the next step. To quickly find the existing value search for `ens5`, it is around [Line 423](https://github.com/jonrau1/SyntheticSun/blob/master/readme-stage1/artifacts/suricata.yaml#L423)

8. <MISPInstance> Execute the following commands to finalize configuration of Suricata and installation of the CloudWatch Logs Agent. **Note** the 2 instances of `exit` are correct in the script, the first leaves sudo and the second will stop your Session.
```bash
suricata-update
cd ~
curl -o /root/amazon-cloudwatch-agent.deb https://s3.amazonaws.com/amazoncloudwatch-agent/debian/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E /root/amazon-cloudwatch-agent.deb
usermod -aG adm cwagent
service suricata restart
exit
exit
```

9. <localInstance> Execute the following command to run the `AmazonCloudWatch-ManageAgent` document to configure the Agent using the Parameter spec you deployed in Step 4 and start it. **Note** replace the Instance ID and the region as needed.
```bash
aws ssm send-command \
    --document-name "AmazonCloudWatch-ManageAgent" \
    --document-version "4" \
    --targets '[{"Key":"InstanceIds","Values":["<MISP_INSTANCE_ID_HERE"]}]' \
    --parameters '{"action":["configure"],"mode":["ec2"],"optionalConfigurationSource":["ssm"],"optionalConfigurationLocation":["AmazonCloudWatch-linux"],"optionalRestart":["yes"]}' \
    --timeout-seconds 600 \
    --max-concurrency "50" \
    --max-errors "0" \
    --cloud-watch-output-config '{"CloudWatchOutputEnabled":true}' \
    --region <AWS_REGION_HERE>
```

This is the end of Stage 1 for SyntheticSun. Before moving onto Stage 2 confirm that Suricata logs are being published to CloudWatch by navigating to the CloudWatch Logs console and looking at either `Suricata-DNS-Logs` or `Suricata-Not-DNS-Logs` log groups. 

If logs are not being published verify that the CloudWatch Agent is running by using the `AmazonCloudWatch-ManageAgent` Document in `status` mode and looking for Suricata publishing logs by navigating to `/var/logs/suricata` and verifying that both `eve-dns.json` and `eve-nsm.json` are created and streaming by using `tail -f`. If the `suricata-update` command was succesful you likely do not have the right network interface specified, repeat Step 7.

**[Stage 2 starts here](https://github.com/jonrau1/SyntheticSun/tree/master/readme-stage2)**
