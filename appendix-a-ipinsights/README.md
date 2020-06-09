# SyntheticSun
SyntheticSun is a proof of concept (POC) defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats.

*"You sleep in fragmented glass"*</br>
*With reflections of you,"*</br>
*But are you feeling alive?"*</br>
*Yeah let me ask you,"*</br>
*Are you feeling alive?"*</br>
<sub>- **Norma Jean, 2016**</sub>

## Appendix A - IP Insights training grounds
This is an optional section of SyntheticSun which provides resources to prepare training sets for AWS telemetry and run them through an IP Insights training job before deploying the finished model to an endpoint. The basic implementation of SyntheticSun uses one generic IP Insights model for both WAF and CloudTrail logs, this will allow you to have a model trained on data that you source from within your own infrastructure which should increase the efficacy of the solution.

REFER HERE: https://github.com/awslabs/amazon-sagemaker-examples/blob/master/introduction_to_amazon_algorithms/ipinsights_login/ipinsights-tutorial.ipynb