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
FROM python:3.8-slim

ENV PYTHONUNBUFFERED=1
ENV CLOUDTRAIL_LOGS_BUCKET=CLOUDTRAIL_LOGS_BUCKET

LABEL maintainer="https://github.com/jonrau1" \
    version="0.9" \
    license="GPL-3.0" \
    description="SyntheticSun is a defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats."

ADD requirements.txt /tmp/requirements.txt
ADD cloudtrail-ipinsights.py /root/cloudtrail-ipinsights.py

RUN pip3 install -r /tmp/requirements.txt

WORKDIR /root

CMD python3 cloudtrail-ipinsights.py