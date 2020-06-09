# SyntheticSun
SyntheticSun is a proof of concept (POC) defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats.

*"You sleep in fragmented glass"*</br>
*With reflections of you,"*</br>
*But are you feeling alive?"*</br>
*Yeah let me ask you,"*</br>
*Are you feeling alive?"*</br>
<sub>- **Norma Jean, 2016**</sub>

## Appendix A - IP Insights training grounds
This is an optional section of SyntheticSun which provides resources to prepare training sets for AWS telemetry and run them through an IP Insights training job before deploying the finished model to an endpoint. The basic implementation of SyntheticSun uses one generic IP Insights model for both WAF and CloudTrail logs, this will allow you to have a model trained on data that you source from within your own infrastructure which should increase the efficacy of the solution. The original IP Insights Jupyter [notebook tutorial is here](https://github.com/awslabs/amazon-sagemaker-examples/blob/master/introduction_to_amazon_algorithms/ipinsights_login/ipinsights-tutorial.ipynb), note that there are some Python library implementation errors in this notebook and you should possess some moderate exposure to troubleshooting Python if the need arises.

Due to my lack of knowledge with writing Juypter notebooks I decided to go with the approach of using questionable Python magic and Fargate orchestrated Docker images. You can also run the provided scripts locally if you choose, however, if you are part of an organization or just have an abnormally high amount of traffic your CloudTrail and WAF logs can be in excess of 50GB in a 24-hour period.

This Appendix is split into two sections - one for WAF logs and one for CloudTrail. It is assumed that you will be preparing your WAF training dataset against the bucket deployed by SyntheticSun so the Python code will not prepare for any compression. It is also assumed that you will prepare your CloudTrail training dataset against standard S3 logs (Gunzipped JSON), any additional compression or processing done to either log will **FAIL** with the example scripts as is.

### Solutions architecture
Below is a basic representation of the data processing, model training and model endpoint hosting.

### Deployment guide
The steps below can be performed for both the CloudTrail or WAF training jobs interchangeably - this guide doesn't make an assumption which you choose. Ensure you navigate to the correct directory for your training job. All steps are performed on an Ubuntu 18.04LTS EC2 instance, modify the commands as needed, you should have power user rights on your instance profile / credentials profile to deploy the necessary solutions.

1. Install necessary dependencies if you do not have them installed.
```bash
sudo su
apt install -y docker python3-pip
pip3 install awscli
pip3 install boto3
git clone https://github.com/jonrau1/SyntheticSun
cd SyntheticSun/appendix-a-ipinsights
```

2. Create two ECR repositories, one for each training job.
`aws ecr create-repository --repository-name <value>`

3. Change directory to the example scripts and issue the following commands to authenticate to your repo, build, tag and push your images. Change the values for your AWS region and AWS Account Id as needed.
```bash
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com
docker build -t ct-ipinsights-trainer .
docker tag ct-ipinsights-trainer:latest <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/ct-ipinsights-trainer:latest
docker push <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/ct-ipinsights-trainer:latest
```

4. Deploy a CloudFormation stack from `SyntheticSun_TRAINING_GROUNDS_CFN.yaml`. Keep the default value of the ECS Cluster as the Python script in the next step has it hardcoded. You will need the URI of both Docker images created in Step 3. If you only want to use one of the training images then edit the CloudFormation to remove the redundant Container Definition.

5. After the CloudFormation stack has finished creating copy the security group ID from the **Resources** tab. Execute the `taskmaster.py` script in the Appendix A root directory and provide the value of a Public Subnet in the VPC you specified for creating the security group and the Security Group Id. `python3 taskmaster.py subnet-12345 sg-12345`

**Note**: Depending on the amount of logs you have in your buckets the tasks may take a substantial amount of time to complete. Refer to the ECS Logs of the running task to see what the status is, the majority of the operations are written to the logs via `print` statements.

