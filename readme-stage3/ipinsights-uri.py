from sagemaker.amazon.amazon_estimator import get_image_uri
import boto3

image = get_image_uri(boto3.Session().region_name, 'ipinsights')
print(image)