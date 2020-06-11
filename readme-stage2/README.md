# SyntheticSun
SyntheticSun is a proof of concept (POC) defense-in-depth security automation and monitoring framework which utilizes threat intelligence, machine learning, and serverless technologies to continuously prevent, detect and respond to new and emerging threats.

*"You sleep in fragmented glass"*</br>
*With reflections of you,"*</br>
*But are you feeling alive?"*</br>
*Yeah let me ask you,"*</br>
*Are you feeling alive?"*</br>
<sub>- **Norma Jean, 2016**</sub>

## Stage 2 - Automation configuration
In this Stage we will configure the MISP platform to bring in cyber threat intelligence and prepare it for export. We will also deploy all necessary services for the automation of edge protection and processing of cyber threat intelligence (CTI) indicators of compromise (IoCs). We'll go over the solutions architecture first, deployment instructions are below it.

### Solution Architecture
Below is the high level view of the four different build automation jobs that run. While no direct links are shown all four CodeBuild projects get their artifacts from a single CodeCommit repository. All builds are scheduled using time-based EventBridge events and all build logs are published to CloudWatch Logs.

![SyntheticSun Build Automation Architecture](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-buildautomation-diagram.jpg)
##### LIMO Automations
1. CodeBuild uses various Python libaries to parse IoC's from [Anomali's LIMO feed](https://www.anomali.com/community/limo)by collections. IoCs are returned in [STIX](https://stixproject.github.io/about/) XML.
2. STIX XML is converted to JSON, parsed and normalized before being written into DynamoDB. This project runs every 4 hours.
##### MISP Automations
1. [MISP](https://www.misp-project.org/) continually pulls and publishes events from a variety of public CTI feeds. Native jobs are used to schedule the pull and refresh of feeds and corresponding events.
2. CodeBuild retrieves the MISP automation API key from Systems Manager [Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-about-examples.html#parameter-types) (SecureString).
3. CodeBuild uses [MISP's built-in API](https://www.circl.lu/doc/misp/automation/) to perform tag-based pulls on the feeds, the response is in JSON which is simply looped through to normalize the IoCs.
4. The parsed and normalized CTI is written into a corresponding DynamoDB table. This project runs every 4 hours.
##### WAF Automations
1. CodeBuild runs a `Scan` against the IP-based DynamoDB table, grabs the latest 10,000 IP IoC's and writes them into their respective WAF [IP Sets](https://docs.aws.amazon.com/waf/latest/APIReference/API_IPSet.html), overwriting all older values. This project runs every 6 days.
2. (**Optional**) Firewall Manager can be used to mandate a desired state for a WAFv2 Web ACL using [AMRs](https://aws.amazon.com/blogs/aws/announcing-aws-managed-rules-for-aws-waf/) and this automated IP Set based on CTI.
##### GuardDuty Automations
1. CodeBuild runs a `Scan` against the IP and Anomaly (feed in another workflow) DynamoDB tables. The latest IP addresses are written in text files and uploaded to S3. Threat intel sets for GuardDuty support up to 6 sets with 250,000 IP's each.
2. CodeBuild calls the `UpdateThreatIntelSet` API which instructs GuardDuty to retrieve and activate the latest text files. This project runs every 6 days.

**Important note:** This solution architecture is assuming you will run it in the account where your [GuardDuty Delegated Admin](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_organizations.html) and [AWS Firewall Manager Administrator Account](https://docs.aws.amazon.com/waf/latest/developerguide/enable-integration.html) are designated if you are part of an AWS Organization.

### Deployment instructions
1. Log in to the MISP server deployed in Phase 1. Refer to the public IP address in the EC2 console, you will likely get an untrusted X.509 cert warning in your browser, the default login credentials are `admin@admin.test` and the password is `admin`. Refer to the [MISP-Cloud project](https://github.com/MISP/misp-cloud#credentials--access) in case this value or the AMI changes. **Note** if you have trouble reaching the sign-in page attempt to add `/users/login` to the end of the IP address / hostname.

2. Change the password and optionally create a new admin user in MISP. If you are not prompted navigate to **Administration >> List Users** and edit the user by selecting the notebook icon as shown in the figure below.
![MISP Edit User](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-misp-edituser.JPG)

3. Navigate to **Event Actions >> Automation** and `reset` the Automation key as shown below. This will be the value we will provide to our CodeBuild projects to perform tag-based queries against the MISP API.
![MISP Automation Key](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-misp-automationkey.JPG)

4. Copy this new Automation key and create a Systems Manager Parameter for it: `aws ssm put-parameter --name MISP-Automation-Key --description 'Contains the MISP Automation key for SyntheticSun Stage 2 Build automations' --value <AUTOMATION_KEY> --type SecureString`. The name of this parameter will be entered into the CloudFormation stack, take note of it if you change the name from what is provided by default.

5. Navigate to **Event Actions >> Add Tag** and create tags for `DDB_IP_FEED` and `DDB_URL_FEED` as shown below. Ensure that the checkbox for **Exportable** is selected, you can optionally select your organization (if you configured it) under **Restrict tagging to org**, it will default to `ORGNAME`.
![MISP Add Tags](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-misp-addtag.JPG)

**IMPORTANT NOTE:** The next steps should be repeated as many times as you want to add new threat intel feeds into MISP, at the minimum you will need one IP-based IOC feed and one URL/hostname-based IOC feed. Refer to the list below for recommended lists across URL/Domain and IP types.
##### IP-based IOC Feeds
- blockrules of rules.emergingthreats.net
- IPs from High-Confidence DGA-Based C&Cs Actively Resolving feed
- mirai.security.gives feed
- ci-badguys.txt feed (**Note:** This list can easily get close to over 1M+ records)
- CyberCure - IP Feed feed
##### URL/hostname-based IOC Feeds
- OpenPhish url list feed
- Phishtank online valid phishing feed
- CyberCure - Blocked URL Feed feed

6. Navigate to **Sync Actions >> List Feeds**. Go through the list of default feeds in MISP, check the box at the far left of the list and at the top of the console select **Enable selected** as shown below.
![MISP Enable Feeds](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-misp-enablefeeds.JPG)

7. After you are done enabling all of your desired feeds filter onto the enabled feeds by selecting **Enabled feeds** at the top of the console. For each enabled feed select **Fetch all events** at the far right which is presented as a downward pointing arrow within a dark circle as shown below. **Note:** if you picked an instance that is not memory-optimized this may take a while or crash your instance. You should delay the time between fetching events as this schedules a job onto MISP to do a pull into the backend DB.
![MISP Fetch Events](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-misp-fetchevents.JPG)

8. Navigate **Home** where the published events from your selected feeds will appear. For each feed select the **Id** (represented numerically). Select the globe icon within the Event to add the tags created in Step 5. Ensure you select the tag that corresponds to the feed type (i.e `DDB_IP_FEED` for the `mirai.security.gives feed`) as shown below. After you have tagged your feed select **Publish Event** (in the below screenshot it says **Unpublish** which is where **Publish Event** typically appears)
![MISP Publish Events](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-misp-publishevents.JPG)

9. Finally, navigate to **Administration >> Scheduled Tasks**. Select the **Frequency (h)** row by double-clicking and enter a `4` for **fetch_feeds** and **pull_all** as shown below. This will allow MISP to continuously update the feeds to pull the latest events which will be published and available to DynamoDB.
![MISP Scheduled Tasks](https://github.com/jonrau1/SyntheticSun/blob/master/img/syntheticsun-misp-scheduledtasks.JPG)

10. Deploy a CloudFormation stack from `SyntheticSun_BUILD_AUTOMATION_CFN.yaml`. This should not take too long, ensure that you are running this in your GuardDuty Master account if you are part of an AWS Organization. Ensure you run at least the MISP project after deployment before moving onto Stage 3.

**[Stage 3 starts here](https://github.com/jonrau1/SyntheticSun/tree/master/readme-stage3)**

## FAQ

### 1. How are CTI IoCs normalized for loading into DynamoDB?
Normalization is done using a wide variety of Python libraries such as `stix`, `cabby`, `json`, `datetime`, and `requests`. Not all libaries are used for all types of feeds (LIMO or MISP) and any advanced functionality for either is likely ignored. The primary information that is pulled is the primary IoC itself (e.g. IPv4 address, domain name, URL or hostname) as well as the name of the feed, a unique identifier and timestamps in both ISO8601 and Unix time are processed.

In the case of MISP the built-in `/attributes/restSearch` API is used to pull published events by Tag and the JSON reponse from the `requests` libary is looped over and a new JSON object is formed per event into a new `item` before calling `PutItem`. MISP provides the feed name and a UUID for the feed by default and also provides a timestamp for when the event was entered into the feed in Unix time. `datetime` is used to convert the Unix timestamp into a UTC ISO8601 timestamp for sorting the DynamodB table by time. The Unix timestamp is used as the Time-to-live (TTL) attribute in DynamoDB.

For LIMO the `cabby` libary is used to create an authenticated TAXII client using the default basic auth (guest/guest) provided by Anomali and polling Collections (synonymous to MISP's feeds) for IoCs within the last 3 days. SyntheticSun's implementation hard-codes the collections (`DShield` and `EmergingThreats_D68`) but you could optionally loop through all collections and write them to a table, however, some provide Domain or Hostname-based IoCs (which were not evaluated) and the Anomali Weekly Threat Brief Collection seems to have been deprecated. Both Collections are written to XML files which are provided to an XML iterator using `glob` and parsed into strings using the `stix` libary spec. LIMO provides timestamps as a string which are converted to ISO8601 and Unix time by the `datetime` library before the calling `PutItem`. The last unique piece about the LIMO implementation is that the feed name is hardcoded and the feed unique identifier is created by creating a SHA-224 hash of the feed name using `hashlib`. This just helps ensure consistency of the data model in DynamoDB and is unused at this time.

### 2. How are CTI IoCs de-duplicated across threat feeds?
De-duplication takes advantage of the mutability of hash keys in [DynamoDB tables](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html). In DynamoDB, and similar NoSQL databases, the hash key (or primary key) is (shocker) the primary key that records (called `items`) are organized against. The hash key is mutable which has the secondary affect of de-duplication when multiple records containing the same hash key are entered into a table, if you wanted to avoid this mutability you would need to specify a secondary range key (aka `sort key`) and optionally Local or Global Secondary Indicies (`LSI` and `GSI`) into your table, only if all keys and indicies were the same would the item be updated upon `PutItem` calls. For SyntheticSun all DynamoDB tables deployed in Stage 2 only use a hash key, so when multiple feeds from both MISP and Anomali's LIMO are reporting the same IPv4 or Domain/URL-based IoC only one unqiue instance of that IoC will ever appear. Your table will still consume [write consumption units](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/switching.capacitymode.html) (WCU), this was the simplest way to enforce uniqueness without having to invest heavily into data pre-processing during CodeBuild builds.

### 3. How are CTI IoCs kept up to date?
The DynamoDB tables, as shown in the solution architecture, are loaded using time-based Event-triggered CodeBuild projects to run every 4 hours. As described in FAQ#1 Unix timestamps are used as the TTL entry in DynamoDB, they are created by multiplying the IoC timestamp by `7` and by `86400` which is roughly 7 weeks in Unix time which in practice will purge these entries from DynamoDB weekly unless they are encountered by a feed again. New entries will have new TTLs so you may run into cases where an IoC's `item` is continually updated but the `feed-name` may change as different feeds encounter the IoC. Threat actors are becoming increasingly sophisticated and relying on domain generation algorithms (DGA), self-hosted / cloud-hosted VPNs and IoT Botnets to further obfuscate the sources of their attacks and you'll quickly encounter that outside of TOR nodes most IoCs change rapidly depending on the threat type and involved actors.

### 4. Will adding IoCs to the GuardDuty Threat Intel Set block these attempts?
No, GuardDuty will generate a different finding type when traffic is seen going to or coming from a malicious IP in the threat intel set. These findings include `UnauthorizedAccess:EC2/MaliciousIPCaller.Custom`, `UnauthorizedAccess:IAMUser/MaliciousIPCaller.Custom` and `Recon:IAMUser/MaliciousIPCaller.Custom` and special attention should be paid to them. Anecdotally, due to current work-from-home situations, you may see a spike of these originating from TOR IP addresses due to workforce members using TOR itself or VPN services that over VPN-over-TOR such as NordVPN. More information on GuardDuty finding types can be [found here](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-active.html).