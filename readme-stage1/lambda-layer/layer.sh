aws lambda publish-layer-version \
    --layer-name aws4auth \
    --description "Python 3 Lambda layer for AWS4Auth Requests library" \
    --license-info "MIT" \
    --zip-file fileb://aws4auth-layer.zip \
    --compatible-runtimes python3.7 python3.8
