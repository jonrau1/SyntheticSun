import boto3

lambdas = boto3.client('lambda')

try:
    response = lambdas.publish_layer_version(
        LayerName='aws4auth',
        Description='Python 3 Lambda layer for AWS4Auth Requests library',
        Content={'ZipFile': b'./aws4auth-layer.zip'},
        CompatibleRuntimes=['python3.7','python3.8'],
        LicenseInfo='MIT-0'
    )
    print('Success. Layer ARN is: ' + response['LayerArn'])
except Exception as e:
    print(e)
    raise