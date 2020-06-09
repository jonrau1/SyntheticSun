FROM python:3.8-slim

ENV PYTHONUNBUFFERED=1
ENV CLOUDTRAIL_LOGS_BUCKET=CLOUDTRAIL_LOGS_BUCKET

LABEL maintainer="https://github.com/jonrau1" \
    version="0.9" \
    license="GPL-3.0" \
    description="SyntheticSun is a proof of concept (POC) defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats."

ADD requirements.txt /tmp/requirements.txt
ADD cloudtrail-ipinsights.py /root/cloudtrail-ipinsights.py

RUN pip3 install -r /tmp/requirements.txt

WORKDIR /root

CMD python3 cloudtrail-ipinsights.py