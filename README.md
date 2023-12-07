# Catalyst Center Integration with GitHub


This repo is for two applications that will:
- update and maintain in sync Cisco DNA Center Projects and CLI templates with a GitHub Repo hosting the templates files.
- update a GitHub repo with device inventory, network settings and site hierarchy

GitHub Repos will be used as a single source of truth for all desired settings, templates and profiles, providing consistent configurations across multiple Cisco DNA Center Clusters, lab and production.
They will also provide network state and tracking of changed made to your Catalyst Center configurations.

**Cisco Products & Services:**

- Cisco DNA Center, devices managed by Cisco DNA Center
- Cisco DNA Center Python SDK

**Tools & Frameworks:**

- Python environment to run the application
- GitHub account, private token and repos
- Optional: CI/CD platform if desired to automate the process

**Usage**

"catalyst_center_github_sync.py"
This app will sync CLI templates from GitHub repos with Cisco DNA Center projects/templates:
 - identify if the specific repository exists in GitHub, pull or clone the repos.
 - will verify if the Cisco DNA Center template project exists and creates a new one
 - verify if Cisco DNA Center templates exist and are identical with the last version of the files from the GitHub repo
 - will create new templates or update existing ones with these details:
   - commit info: author, date, commit message and diff
   - CLI commands
 - it will commit the new or updated templates
 - no action will be taken if no templates changes
 - at the end of execution a report will be created

"catalyst_center_network_sync.py"
This app will sync Catalyst Center state documented as code to a GitHub repo:
 - collect the Catalyst Center device inventory
 - retrieve the Catalyst Center Site hierarchy for all sites
 - collect the network settings for all sites
 - identify if the specific repository exists in GitHub
 - it will commit the new or updated network state files
 - at the end of execution a report will be created
    

These apps may be part of your CI/CD pipelines, to run on-demand, scheduled or triggered by updates to the GitHub repo.

This app is using the Python SDK to make REST API calls to Cisco DNA Center.

Sample environment variables:

```shell
# Cisco DNA Center
DNAC_URL = 'https://dnacenter'
DNAC_USER = 'user'
DNAC_PASS = 'password'
DNAC_PROJECT = 'Cisco DNA Center Project'

# GitHub
GITHUB_TOKEN = 'token'   # GitHub access token
GITHUB_USERNAME = 'user'
GITHUB_REPO = 'repo'
```

Sample Output:

```shell
python catalyst_center_github_sync.py

INFO:root: App "catalyst_center_github_sync.py" Start, 2023-12-06 16:22:11
INFO:root: Repo "dnacenter_github_templates" found!
INFO:root: Repo "dnacenter_github_templates" files:
INFO:root: File: aaa_config.txt
INFO:root: File: csr_logging.txt
INFO:root: File: snmp_ntp.txt
INFO:root: Collected all commit comments for "dnacenter_github_templates" repo
INFO:root: Project "GitHub_Project" id: 4f7d1420-b86c-4b8b-b2a2-3c3e03f667f3
INFO:root: Template name: aaa_config
INFO:root: Template content:
{#
This template has been pulled from GitHub.
Uploaded to Catalyst Center by GitHub_Sync App
Author: gzapodea@cisco.com
Date: 2023-03-24T21:19:42Z
Commit message: updated templates, new template
Commit URL: https://github.com/zapodeanu/dnacenter_github_templates/commit/50724c24f7f7ebe435bafbdb41419adf660cc41f
Commit Diff: @@ -0,0 +1,5 @@
+!
+aaa new-model
+aaa authentication login default local
+aaa authorization exec default local
+!
\ No newline at end of file
#}
!
!
aaa new-model
aaa authentication login default local
aaa authorization exec default local
!
INFO:root: Template "aaa_config" has not changed, identical template on Catalyst Center
INFO:root: Template name: csr_logging
INFO:root: Template content:
{#
This template has been pulled from GitHub.
Uploaded to Catalyst Center by GitHub_Sync App
Author: gzapodea@cisco.com
Date: 2023-12-06T22:43:13Z
Commit message: updated logging buffer
Commit URL: https://github.com/zapodeanu/dnacenter_github_templates/commit/960dc36b6130c46c679fea0a9cfa9f7590e97e69
Commit Diff: @@ -1,5 +1,5 @@
 !
-logging buffered 81920
+logging buffered 4096
 logging host 10.93.141.37 transport udp port 8514
 logging source-interface Loopback100
 no logging host 10.93.141.1 transport udp port 8514
#}
!
!
logging buffered 4096
logging host 10.93.141.37 transport udp port 8514
logging source-interface Loopback100
no logging host 10.93.141.1 transport udp port 8514
!
service timestamps debug datetime localtime
service timestamps log datetime localtime
!
INFO:root: Template "csr_logging" has not changed, identical template on Catalyst Center
INFO:root: Template name: snmp_ntp
INFO:root: Template content:
{#
This template has been pulled from GitHub.
Uploaded to Catalyst Center by GitHub_Sync App
Author: gzapodea@cisco.com
Date: 2023-04-19T22:28:26Z
Commit message: updated ntp source
Commit URL: https://github.com/zapodeanu/dnacenter_github_templates/commit/82ed7d6f6235d46daaceeeb6cad5c05214250611
Commit Diff: @@ -5,5 +5,6 @@ snmp-server host 10.93.130.50 version 2c RW
 ntp server 171.68.48.78
 ntp server 171.68.38.53
 no ntp server 171.68.48.80
-ntp source Loopback1
+no ntp source Loopback1
+ntp source Loopback0
 !
\ No newline at end of file
#}
!
!
snmp-server host 10.93.135.30 version 2c RO
snmp-server host 10.93.130.50 version 2c RW
!
ntp server 171.68.48.78
ntp server 171.68.38.53
no ntp server 171.68.48.80
no ntp source Loopback1
ntp source Loopback0
!
INFO:root: Template "snmp_ntp" has not changed, identical template on Catalyst Center
INFO:root:
GitHub Sync Report:
Template "aaa_config" has not changed, identical template on Catalyst Center
Template "csr_logging" has not changed, identical template on Catalyst Center
Template "snmp_ntp" has not changed, identical template on Catalyst Center

INFO:root: End of Application "catalyst_center_github_sync.py" Run: 2023-12-06 16:22:37
```

```shell
python catalyst_center_network_state_sync.py

INFO:root: Application "catalyst_center_network_state_sync.py" Start, 2023-12-06 16:24:31
INFO:root: Number of devices managed by Cisco DNA Center: 12
INFO:root: Collected the device list from Cisco DNA Center
INFO:root: Collected the device inventory from Cisco DNA Center
INFO:root: Saved the device inventory to file "device_inventory.json"
INFO:root: Saved the AP inventory to file "ap_inventory.json"
INFO:root: Number of sites in Catalyst Center: 17
INFO:root: Global site id: 15ab86e1-706e-41df-8400-ee1a974bc1f3
INFO:root: Saved the site hierarchy to file "site_hierarchy.json"
INFO:root: Saved the site hierarchy to file "network_settings.json"
INFO:root: Repo "catalyst_center_network_state" found!
INFO:root: Catalyst Center Network State Sync Report:
INFO:root:    GitHub push for file: ap_inventory.json, file existing: True
INFO:root:    GitHub push for file: device_inventory.json, file existing: True
INFO:root:    GitHub push for file: network_settings.json, file existing: True
INFO:root:    GitHub push for file: site_hierarchy.json, file existing: True
INFO:root: Saved the report to file "report.json"
INFO:root: End of Application "catalyst_center_network_state_sync.py" Run: 2023-12-06 16:25:10

```

**License**

This project is licensed to you under the terms of the [Cisco Sample Code License](./LICENSE).


