# This file is part of SyntheticSun.

# SyntheticSun is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# SyntheticSun is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with SyntheticSun.  
# If not, see https://github.com/jonrau1/SyntheticSun/blob/master/LICENSE.
import json
import datetime
import gzip
import boto3
import re
import botocore
import os
import csv
import sagemaker
import pandas
from sagemaker.amazon.amazon_estimator import get_image_uri
from sagemaker.predictor import csv_serializer, json_deserializer

# create boto3 clients
s3resc = boto3.resource('s3')
s3 = boto3.client('s3')
paginator = s3.get_paginator('list_objects_v2')
# var for CT logs bucket
wafBucket = os.environ['WAF_LOGS_BUCKET']
# create a YYYY/MM/DD 1 day in the past. This will grab a small swath of WAF data
# if you are part of a larger organization, depending on your CT configuration (Data Events, Insights, KMS) 
# it is not unheard of to have 70+ GB of data
# you may need to change that strftime to a timestamp to pull by the hour
now = datetime.datetime.now()
pastTime = now - datetime.timedelta(days=1)
wafTimestamp = pastTime.strftime('%Y/%m/%d')
# create multiple regex to perform hacky filtering
ipv4Regex = re.compile('^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
wafTimestampFilter = re.compile(wafTimestamp)
wafList = []
print('Preparing to download S3 objects')
# iterate over all objects in the bucket
iterator = paginator.paginate(Bucket=wafBucket)
for page in iterator:
    for item in page['Contents']:
        s3Obj = str(item['Key'])
        timeDropper = wafTimestampFilter.search(s3Obj)
        if timeDropper:
            # drop any keys that no not match the timestamp
            localFilePath = s3Obj.split('/')[-1]
            s3.download_file(wafBucket, s3Obj, localFilePath)
            try:
                with open(localFilePath,'r') as content:
                    for line in content:
                        wafLogs = json.loads(line)
                        clientIp = str(wafLogs['httpRequest']['clientIp'])
                        ipv4Match = ipv4Regex.match(clientIp)
                        if ipv4Match:
                            for headers in wafLogs['httpRequest']['headers']:
                                if str(headers['name']) == 'User-Agent':
                                    try:
                                        userAgent = str(headers['value'])
                                        newUserAgent = userAgent.replace('.','')
                                        noCommaUserAgent = newUserAgent.replace(',','')
                                        wafDict = {
                                            'userAgent': noCommaUserAgent,
                                            'ipaddress': clientIp
                                        }
                                        wafList.append(wafDict)
                                    except:
                                        pass   
                                else:
                                    pass
                        else:
                            pass
            except Exception as e:
                print(e)
                raise
        else:
            pass

keys = wafList[0].keys()
with open('ct-training-data.csv', 'w') as outf:
    dw = csv.DictWriter(outf, keys)
    dw.writerows(wafList)

outf.close()
print('WAF data training is complete, starting sagemaker job')
trainingBucket = sagemaker.Session().default_bucket()
ctTrainingOutputPath = 'waf-ipinsights'
trainingData = 'ct-training-data.csv'
trainingInstanceSize = 'ml.m5.large'
print('Uploading training data to Sagemaker default bucket')
s3resc.meta.client.upload_file('./' + trainingData, trainingBucket, ctTrainingOutputPath + '/' + trainingData)
print('CT training data uploaded to S3')
trainingDataS3 = 's3://' + trainingBucket + '/' + ctTrainingOutputPath + '/' + trainingData
print('Declaring sagemaker IAM role for current session. Ensure your trust policy allows sagemaker.amazonaws.com to perform sts:AssumeRole')
execution_role = sagemaker.get_execution_role()
print('Preparing S3 training data')
input_data = { 'train': sagemaker.session.s3_input(trainingDataS3, distribution='FullyReplicated', content_type='text/csv') }
image = get_image_uri(boto3.Session().region_name, 'ipinsights')
print('IP Insights image URI retrieved for region')
# Set up the estimator with training job configuration
print('Creating IP Insights Sagemaker estimator')
ip_insights = sagemaker.estimator.Estimator(
    image, 
    execution_role, 
    train_instance_count=1, 
    train_instance_type=trainingInstanceSize,
    output_path='s3://' + trainingBucket + '/' + ctTrainingOutputPath + '/output',
    sagemaker_session=sagemaker.Session())
# Configure algorithm-specific hyperparameters
# num_entity_vectors should ideally be 2x the total number of unique entites (i.e. user names) in your dataset
print('Setting hyperparameters')
ip_insights.set_hyperparameters(
    num_entity_vectors='20000',
    random_negative_sampling_rate='2',
    vector_dim='128', 
    mini_batch_size='1000',
    epochs='5',
    learning_rate='0.01',
)
print('Starting training job')
# Start the training job (should take about ~1.5 minute / epoch to complete)  
ip_insights.fit(input_data)
print('Training job name: {}'.format(ip_insights.latest_training_job.job_name))
## INFERENCE TIME
predictor = ip_insights.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.xlarge'
)
print('Endpoint name: {}'.format(predictor.endpoint))
print('Providing endpoint sample data')
predictor.content_type = 'text/csv'
predictor.serializer = csv_serializer
predictor.accept = 'application/json'
predictor.deserializer = json_deserializer
# read 5 entries into a Pandas dataframe
sample = pandas.read_csv('ct-training-data.csv', nrows=5)
inference_data = [(data[0], data[1]) for data in sample[:5].values]
predictor.predict(inference_data)
predictor.accept = 'application/json; verbose=True'
predictor.predict(inference_data)
print('training has completed and the endpoint is deployed')

sagemaker.Session().delete_endpoint(predictor.endpoint)