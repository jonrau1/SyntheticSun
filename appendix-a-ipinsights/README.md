# SyntheticSun
SyntheticSun is a proof of concept (POC) defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats.

*"You sleep in fragmented glass"*</br>
*With reflections of you,"*</br>
*But are you feeling alive?"*</br>
*Yeah let me ask you,"*</br>
*Are you feeling alive?"*</br>
<sub>- **Norma Jean, 2016**</sub>

## Appendix A - IP Insights training grounds
This is an optional section of SyntheticSun which provides resources to prepare training sets for AWS telemetry and run them through an [IP Insights](https://docs.aws.amazon.com/sagemaker/latest/dg/ip-insights-howitworks.html) training job before deploying the finished model to an endpoint. The basic implementation of SyntheticSun uses one generic IP Insights model for both WAF and CloudTrail logs, this will allow you to have a model trained on data that you source from within your own infrastructure which should increase the efficacy of the solution. The original IP Insights Jupyter [notebook tutorial is here](https://github.com/awslabs/amazon-sagemaker-examples/blob/master/introduction_to_amazon_algorithms/ipinsights_login/ipinsights-tutorial.ipynb), note that there are some Python library implementation errors in this notebook and you should possess some moderate exposure to troubleshooting Python if the need arises.

Due to my lack of knowledge with writing Juypter notebooks I decided to go with the approach of using questionable Python magic and Fargate orchestrated Docker images. You can also run the provided scripts locally if you choose, however, if you are part of an organization or just have an abnormally high amount of traffic your CloudTrail and WAF logs can be in excess of 50GB in a 24-hour period.

This Appendix is split into two sections - one for WAF logs and one for CloudTrail. It is assumed that you will be preparing your WAF training dataset against the bucket deployed by SyntheticSun so the Python code will not prepare for any compression. It is also assumed that you will prepare your CloudTrail training dataset against standard S3 logs (Gunzipped JSON), any additional compression or processing done to either log will **FAIL** with the example scripts as is.

### Solutions architecture
Below is a basic representation of the data processing, model training and model endpoint hosting that happens between Fargate, SageMaker and S3.
![SyntheticSun IP Insights Training Ground Architecture](https://github.com/jonrau1/SyntheticSun/blob/master/img/ipinsights-training-architecture.jpg)
1. Docker images for each IP Insights training task are pulled from Amazon [Elastic Container Registry](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html) (ECR).
2. Each container will download and parse the trail day's logs from their respective bucket. Basic Python libraries such as `json`, `csv` and `re` are used to process the logs into a [headerless CSV file](https://docs.aws.amazon.com/sagemaker/latest/dg/ip-insights-training-data-formats.html) used for the SageMaker training jobs.
3. The `sagemaker` [library](https://pypi.org/project/sagemaker/1.0.0/) is used to persist the training data into SageMaker's default S3 bucket and create various utilities to start the training jobs such as temporary credentials from the ECS Task IAM Role.
4. The SageMaker training jobs for each data type is scheduled to begin, it will pull an IP Insights container from the AWS service account in the region and download the CSV file from S3. [Hyperparameters](https://docs.aws.amazon.com/sagemaker/latest/dg/ip-insights-hyperparameters.html) are specified in the respective job's Python script in the Docker image.
5. If the training job was successful a GZIP'ed tarball of the model is uploaded into another output prefix path in the same S3 bucket. These are timestamped and can be referred back to for other usage such as [tuning jobs](https://docs.aws.amazon.com/sagemaker/latest/dg/ip-insights-tuning.html) or swapping them out from endpoints.
6. Finally, a SageMaker [Endpoint](https://docs.aws.amazon.com/sagemaker/latest/dg/deploy-model.html) is deployed using the trained model and is ready for real-time and/or batch inference of entity and IPv4 address pairs.

### Deployment guide
The steps below can be performed for both the CloudTrail or WAF training jobs interchangeably - this guide assumes you will do both as that is what is the CloudFormation template is expecting. Ensure you navigate to the correct directory for your training job. All steps are performed on an Ubuntu 18.04LTS EC2 instance, modify the commands as needed, you should have power user rights on your instance profile / credentials profile to deploy the services.

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

**Note**: The end of both Python scripts for the image builds contains a command (`sagemaker.Session().delete_endpoint(predictor.endpoint)`) that deletes the endpoint deployed at the end of the inference portion of training. Uncomment this line to delete the endpoint if you just wanted to have a newly trained model uploaded to S3 for future use.

4. Deploy a CloudFormation stack from `SyntheticSun_TRAINING_GROUNDS_CFN.yaml`. Keep the default value of the ECS Cluster as the Python script in the next step has it hardcoded. You will need the URI of both Docker images created in Step 3. If you only want to use one of the training images then edit the CloudFormation to remove the redundant Container Definition.

5. After the CloudFormation stack has finished creating copy the security group ID from the **Resources** tab. Execute the `taskmaster.py` script in the Appendix A root directory and provide the value of a Public Subnet in the VPC you specified for creating the security group and the Security Group Id. `python3 taskmaster.py subnet-12345 sg-12345`

**Note**: Depending on the amount of logs you have in your buckets the tasks may take a substantial amount of time to complete. Refer to the ECS Logs of the running task to see what the status is, the majority of the operations are written to the logs via `print` statements.

6. After the Endpoints have deployed copy the name from either the ECS logs or SageMaker console and overwrite the Lambda enviornment variables for the WAF and/or VPC Flow Log functions deployed in the Core module.

## FAQ

### 1. How long do the Fargate tasks take to complete? What about the IP Insights training job?
Both are directly dependent on the size of your data (in GB) from your log sources as large datasets will take longer to write to CSV and for the SageMaker IP Insights training jobs to complete. The training job time is also influenced in how you setup your hyperparameters, namely `num_entity_vectors`, this hyperparameter should be greater than or equal to twice the number of your total entities in your training data. CloudTrail logs will take (very) slightly longer due to the extra step of needing the gunzip the log files and having to parse over Digest files. Individual benchmarking should be performed by observing the time between the first log and the last log being published to CloudWatch Logs by ECS this, however, will not take into account the total time it takes to start the Fargate job during the provisioning stage.

For anecdotal reference the total time it took a Fargate task with 2vCPU, 4GB RAM and only running the CloudTrail container to process 2.5GB of data (resulting in ~9000 useable entities) was 17 minutes with 67 seconds devoted to the Sagemaker training job itself (not counting the provisioning).

### 2. Why did you use Fargate instead of CodeBuild?
Due to the likliehood of very long running jobs Fargate was chosen as it would be more cost effective factoring in both vCPU and RAM costs per hour of cost per build minute in CodeBuild. Additionally, Fargate is more flexible for running tasks - with CodeBuild you cannot move the project in and out of a VPC but Fargate allows you to specify different Clusters, VPCs, Subnets and have the ability to customize the security group and public IP flags. (That is not saying that it is hard to recreate a CodeBuild project on the fly to meet network security requirements)

### 3. Why did you use Fargate instead of SageMaker Notebooks?
Primarily because I have only used a Jupyter notebook less than half a dozen times and do not know how to effectively write Jupyter notebooks. There are also possible risks for data leakage due to publicly accessible Jupyter notebooks and the VPC architecture needed to airgap and harden a notebook can be prohibitive to some organizations. Jupyter notebooks also imply human intervention where the Fargate tasks can be fully automated and orchestrated and Fargate offers greater deployment flexibility and I do not have to rely on a specific kernel from the notebook. Lastly, it is still more cost effective to use Fargate and you can directly control what libraries go into the image when using something small like an Alpine-based image.

### 4. Why didn't you use (insert cool and complicated technology here)?
If you haven't picked up on this already I am **not** the sharpest spoon in the gun cabinet. I have no idea how to use `pandas` or `numpy` nor can I write a Jupyter notebook. I have no idea how to use Spark, EMR, Glue ETL jobs, Spark automation jobs on Glue, AWS Batch or any other cool toy. While I am sure there are much more highly efficient methods to accomplish what I am doing I am holding out hope you will open a PR and give me all your knowledge...please?
![fuggg xD](https://github.com/jonrau1/SyntheticSun/blob/master/img/fuggg.jpeg)

### 5. I already have WAF logs configured outside of ElectricEye and they are compressed, will your example work?
No (that is explained above). If they are GZIP'ed then you can reuse some of the code from the CloudTrail training grounds but other compression types you are shit out of luck and will need to do it yourself.

### 6. Will you support other log types for training jobs?
Eventually. Since the training grounds are an appendix (add-on) to the core SyntheticSun offering I will not treat it as a first-class citizen. I will accept PRs that are in the same style (Dockerfile + Python script + CFN) as the CloudTrail and WAF logs training grounds examples.

### 7. Will you support other machine learning algorithms, such as Random Cut Forest (RCF)?
I hope to. The downstream solution uses the RCF detectors built into Kibana (for ES domains on version `7.4`+) with other Open Distro for Elasticsearch features such as Monitors and the SNS integration to take advantage of the functionality. I cannot stress it enough that I have zero formal learning (or even informal) and am quite out of my comfort zone.

### 8. My CloudTrail has all features enabled and I am part of a massive Organization, we generate 10GB of data in an hour, please help?
To perform filtering of listed S3 objects there is a reliance on regex using the Python `re` library to both ignore digest files and (for all training grounds jobs) filter the listed keys. I do not know of a solution to perform time-based filtering as an arguement when listing objects, due to that, every single object in the bucket will be looped over and downloaded. The time-based filtering is using `strftime` from the `datetime` library to create a `YYYY/MM/DD` timestamp. You can specify `HH` or `HH/MM` to further scope down the data processing. I do not see another way around doing what I am doing in whole or in part, the previous mentioned steps should at least slightly speed up the job.

Another option would likely be performing a pre-pre-processing step of using a shell script and the S3 CLI (and other *nix tools) to pre-stage a subet of keys in the S3 bucket in another bucket and do away with the pre-processing that is done in the Python scripts (namely the listing and regex matching of objects).