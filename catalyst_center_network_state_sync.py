#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2023 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__author__ = "Gabriel Zapodeanu TME, ENB"
__email__ = "gzapodea@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2023 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

import json
import logging
import os
import time
from datetime import datetime

from dnacentersdk import DNACenterAPI
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth  # for Basic Auth

import github_apis

load_dotenv('environment.env')

CATALYST_CENTER_URL = os.getenv('CATALYST_CENTER_URL')
CATALYST_CENTER_USER = os.getenv('CATALYST_CENTER_USER')
CATALYST_CENTER_PASS = os.getenv('CATALYST_CENTER_PASS')

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_NETWORK_STATE_REPO')

NETWORK_STATE_PATH = 'network_state/'

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/


# noinspection PyBroadException
def main():
    """
    This app will sync Catalyst Center state documented as code to a GitHub repo:
     - collect the Catalyst Center device inventory
     - retrieve the Catalyst Center Site hierarchy for all sites
     - collect the network settings for all sites
     - identify if the specific repository exists in GitHub
     - it will commit the new or updated network state files
     - at the end of execution a report will be created
    This app may be part of a CI/CD pipeline to run on-demand or scheduled.

    This app is using the Python SDK to make REST API calls to Cisco Catalyst Center.

    """

    # logging, debug level, to file {application_run.log}
    logging.basicConfig(level=logging.INFO)

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logging.info(' Application "catalyst_center_network_state_sync.py" Start, ' + current_time)

    # verify if folder for state files exist

    if not os.path.exists(NETWORK_STATE_PATH):
        # Create a new directory because it does not exist
        os.makedirs(NETWORK_STATE_PATH)

    # create a report with each Catalyst Center state file
    report = []

    # delete existing report if any
    if os.path.exists(NETWORK_STATE_PATH + 'report.json'):
        os.remove(NETWORK_STATE_PATH + 'report.json')

    # create a DNACenterAPI "Connection Object" to use the Python SDK
    catalyst_center_api = DNACenterAPI(username=CATALYST_CENTER_USER, password=CATALYST_CENTER_PASS,
                                       base_url=CATALYST_CENTER_URL, version='2.3.5.3', verify=False)

    # collect device inventory
    # get the device count
    response = catalyst_center_api.devices.get_device_count()
    device_count = response['response']
    logging.info(' Number of devices managed by Cisco Catalyst Center: ' + str(device_count))

    # get the device info list
    offset = 1
    limit = 500
    device_list = []
    while offset <= device_count:
        response = catalyst_center_api.devices.get_device_list(offset=offset)
        offset += limit
        device_list.extend(response['response'])
    logging.info(' Collected the device list from Cisco Catalyst Center')

    # create device and AP inventory, it will include all Catalyst Center device details

    device_inventory = []
    ap_inventory = []

    for device in device_list:
        # select which inventory to add the device to
        if device.family != "Unified AP":
            device_id = device['id']
            device_management_ip_address = device['managementIpAddress']
            device_details = {'hostname': device['hostname']}
            device_details.update({'device_ip': device['managementIpAddress']})
            device_details.update({'device_id': device['id']})
            device_details.update({'version': device['softwareVersion']})
            device_details.update({'device_family': device['type']})
            device_details.update({'role': device['role']})

            # get the device site hierarchy
            response = catalyst_center_api.devices.get_device_detail(identifier='uuid', search_by=device_id)
            site = response['response']['location']
            device_details.update({'site': site})

            # get the device fabric role
            device_sda_roles = []

            try:
                response = catalyst_center_api.sda.get_device_role_in_sda_fabric(
                    device_management_ip_address=device_management_ip_address)
                device_sda_roles = response['roles']
            except:
                pass
            device_details.update({'sda_roles': device_sda_roles})

            device_inventory.append(device_details)
        else:
            device_id = device['id']
            device_details = {'hostname': device['hostname']}
            device_details.update({'device_ip': device['managementIpAddress']})
            device_details.update({'device_id': device['id']})
            device_details.update({'version': device['softwareVersion']})
            device_details.update({'device_family': device['type']})
            device_details.update({'role': device['role']})

            # get the device site hierarchy
            response = catalyst_center_api.devices.get_device_detail(identifier='uuid', search_by=device_id)
            site = response['response']['location']
            device_details.update({'site': site})
            ap_inventory.append(device_details)

            # get the device fabric role
            device_sda_roles = []

            try:
                response = catalyst_center_api.sda.get_device_role_in_sda_fabric(
                    device_management_ip_address=device_management_ip_address)
                device_sda_roles = response['roles']
            except:
                pass
            device_details.update({'sda_roles': device_sda_roles})

    logging.info(' Collected the device inventory from Cisco Catalyst Center')

    # save device inventory to JSON formatted file
    with open(NETWORK_STATE_PATH + 'device_inventory.json', 'w') as f:
        f.write(json.dumps(device_inventory, indent=4))
    logging.info(' Saved the device inventory to file "device_inventory.json"')

    # save ap inventory to JSON formatted file
    with open(NETWORK_STATE_PATH + 'ap_inventory.json', 'w') as f:
        f.write(json.dumps(ap_inventory, indent=4))
    logging.info(' Saved the AP inventory to file "ap_inventory.json"')

    # collect site hierarchy
    # get number of sites
    response = catalyst_center_api.sites.get_site_count()
    sites_number = response['response']
    logging.info(' Number of sites in Catalyst Center: ' + str(sites_number))

    # get the Global site id
    response = catalyst_center_api.sites.get_site(name='Global')
    global_site_id = response['response'][0]['id']
    logging.info(' Global site id: ' + global_site_id)

    # get all the sites
    response = catalyst_center_api.sites.get_site()
    site_hierarchy = response['response']

    site_list = []
    for site in site_hierarchy:
        site_details = {'site_name_hierarchy': site['siteNameHierarchy'], 'site_id': site['id']}
        site_list.append(site_details)

    # sort the list of sites details
    site_list_sorted = sorted(site_list, key=lambda x: x['site_name_hierarchy'])

    # save site_hierarchy to JSON formatted file
    with open(NETWORK_STATE_PATH + 'site_hierarchy.json', 'w') as f:
        f.write(json.dumps(site_list_sorted, indent=4))
    logging.info(' Saved the site hierarchy to file "site_hierarchy.json"')

    # collect network settings
    network_settings = []
    for site in site_list_sorted:
        site_id = site['site_id']
        site_name_hierarchy = site['site_name_hierarchy']
        response = catalyst_center_api.network_settings.get_network_v2(site_id=site_id)
        site_settings = {'site_name_hierarchy': site_name_hierarchy}
        site_settings.update({'network_settings': response['response']})
        network_settings.append(site_settings)

    # save network settings to JSON formatted file
    with open(NETWORK_STATE_PATH + 'network_settings.json', 'w') as f:
        f.write(json.dumps(network_settings, indent=4))
    logging.info(' Saved the site hierarchy to file "network_settings.json"')

    # get the repos for user
    repos = github_apis.get_private_repos(username=GITHUB_USERNAME, github_token=GITHUB_TOKEN)

    # verify if repo exists
    if GITHUB_REPO not in repos:
        logging.info(' Repo "' + GITHUB_REPO + '" not found!')
        return
    logging.info(' Repo "' + GITHUB_REPO + '" found!')

    # push all files to GitHub repo
    os.chdir(NETWORK_STATE_PATH)
    files_list = os.listdir()

    # Git push network state files

    for filename in files_list:
        try:
            contents = github_apis.get_repo_file_content(username=GITHUB_USERNAME, repo_name=GITHUB_REPO, file_name=filename)
            update = True
        except:
            update = False  # file does not exist

        with open(filename) as f:
            file_content = f.read()

        # create or push the file
        github_apis.github_push(github_repo=GITHUB_REPO, filename=filename,
                                message="committed by Jenkins - Network State Sync", content=file_content,
                                update=update)
        report.append('    GitHub push for file: ' + filename + ', file existing: ' + str(update))

    logging.info(' Catalyst Center Network State Sync Report:')
    for item in report:
        logging.info(item)

    # save report to JSON formatted file
    with open('report.json', 'w') as f:
        f.write(json.dumps(report, indent=4))
    logging.info(' Saved the report to file "report.json"')

    date_time = str(datetime.now().replace(microsecond=0))
    logging.info(' End of Application "catalyst_center_network_state_sync.py" Run: ' + date_time)

    return


if __name__ == '__main__':
    main()
