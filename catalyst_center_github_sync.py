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

import logging
import os
import time
from datetime import datetime

from dnacentersdk import DNACenterAPI
from dotenv import load_dotenv

import github_apis

load_dotenv('environment.env')

CATALYST_CENTER_URL = os.getenv('CATALYST_CENTER_URL')
CATALYST_CENTER_USER = os.getenv('CATALYST_CENTER_USER')
CATALYST_CENTER_PASS = os.getenv('CATALYST_CENTER_PASS')
CATALYST_CENTER_PROJECT = os.getenv('CATALYST_CENTER_PROJECT')

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/


def main():
    """
    This app will sync CLI templates from GitHub repos with Catalyst Center projects/templates:
     - identify if the specific repository exists in GitHub, pull or clone the repos
     - will verify if the Catalyst Center project exists and creates a new one
     - verify if Catalyst Center templates exist and are identical with the last version of the GitHub repo files
     - will create new templates or update existing ones, with these details:
       - commit info: author, date, commit message and diff
       - CLI commands
     - it will commit the new or updated templates
     - no action will be taken if no templates changes
     - at the end of execution a report will be created
    This app may be part of a CI/CD pipeline to run on-demand, scheduled or triggered by updates to the GitHub repo.

    This app is using the Python SDK to make REST API calls to Catalyst Center.

    """

    # logging, debug level, to file {application_run.log}
    logging.basicConfig(level=logging.INFO)

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logging.info(' App "catalyst_center_github_sync.py" Start, ' + current_time)

    # create a report with each template operation - create, update or no change
    report = ''

    # create a DNACenterAPI "Connection Object" to use the Python SDK
    catalyst_center_api = DNACenterAPI(username=CATALYST_CENTER_USER, password=CATALYST_CENTER_PASS,
                                       base_url=CATALYST_CENTER_URL, version='2.3.5.3',
                                       verify=False)

    # get the repos for user
    repos = github_apis.get_repos(GITHUB_USERNAME)

    # verify if repo exists
    if GITHUB_REPO not in repos:
        logging.info(' Repo "' + GITHUB_REPO + '" not found!')
        return
    logging.info(' Repo "' + GITHUB_REPO + '" found!')

    # get the repo details
    files_list = github_apis.get_repo_content(GITHUB_USERNAME, GITHUB_REPO)
    if not files_list:
        logging.info(' Repo "' + GITHUB_REPO + '" is empty')
        return
    logging.info(' Repo "' + GITHUB_REPO + '" files:')
    for file in files_list:
        logging.info(' File: ' + file)

    # get the sha list for repo
    sha_list = github_apis.get_repo_commits(username=GITHUB_USERNAME, repo_name=GITHUB_REPO)
    comments_list = []

    # get the comments for each sha from the list
    for sha in sha_list:
        comment = github_apis.get_repo_commit_sha(username=GITHUB_USERNAME, repo_name=GITHUB_REPO, sha=sha)
        comments_list.append(comment)
    logging.info(' Collected all commit comments for "' + GITHUB_REPO + '" repo')

    # check if existing Catalyst Center project, if not create a new project
    projects_list = catalyst_center_api.configuration_templates.get_projects(name=CATALYST_CENTER_PROJECT)
    if not projects_list:
        # unable to find the project, create new project
        logging.info(' Project "' + CATALYST_CENTER_PROJECT + '" not found, will create project')
        report += 'Project "' + CATALYST_CENTER_PROJECT + '" not found, created\n'
        # create new project
        response = catalyst_center_api.configuration_templates.create_project(name=CATALYST_CENTER_PROJECT)
        time.sleep(10)

    # retrieve the project id for the project
    project_info = catalyst_center_api.configuration_templates.get_projects(name=CATALYST_CENTER_PROJECT)
    project_id = project_info[0]['id']
    logging.info(' Project "' + CATALYST_CENTER_PROJECT + '" id: ' + project_id)

    # get the files content, loop to pull each file, upload to Catalyst Center, commit

    for file in files_list:
        new_template = '{#\nThis template has been pulled from GitHub.\nUploaded to Catalyst Center by GitHub_Sync App\n'

        # get the last commit message for file, add to template
        for comment in comments_list:
            if file == comment['filename']:
                new_template += 'Author: ' + comment['author'] + '\n'
                new_template += 'Date: ' + comment['date'] + '\n'
                new_template += 'Commit message: ' + comment['message'] + '\n'
                new_template += 'Commit URL: ' + comment['url'] + '\n'
                new_template += 'Commit Diff: ' + comment['diff'] + '\n'
                break
        new_template += '#}\n!\n'
        # append the CLI commands from GitHub file
        new_template += github_apis.get_repo_file_content(username=GITHUB_USERNAME, repo_name=GITHUB_REPO,
                                                          file_name=file)

        # upload the templates to Catalyst Center - create or update template
        template_name = file.split('.')[0]
        logging.info(' Template name: ' + template_name)
        logging.info(' Template content:\n' + new_template)

        # identify if template exists
        template_id = None
        templates_list = project_info[0]['templates']
        for template in templates_list:
            if template_name == template['name']:
                template_id = template['id']

        device_types = [
            {
                'productFamily': 'Routers'
            },
            {
                'productFamily': 'Switches and Hubs'
            }
        ]
        if template_id is None:

            # create new template
            response = catalyst_center_api.configuration_templates.create_template(project_id=project_id,
                                                                                   templateContent=new_template,
                                                                                   language='JINJA',
                                                                                   name=template_name,
                                                                                   deviceTypes=device_types,
                                                                                   softwareType='IOS-XE',
                                                                                   author='Jenkins automation',
                                                                                   description='Created by Python automation')
            logging.info(' New template "' + template_name + '" created')
            task_id = response['response']['taskId']
            logging.info(' Task id: ' + task_id)
            time.sleep(10)

            # get the template id
            project_info = catalyst_center_api.configuration_templates.get_projects(name=CATALYST_CENTER_PROJECT)
            templates_list = project_info[0]['templates']
            for template in templates_list:
                if template_name == template['name']:
                    template_id = template['id']

            # commit the template
            commit_payload = {
                'comments': 'Jenkins automation committed',
                'templateId': template_id
            }
            response = catalyst_center_api.configuration_templates.version_template(payload=commit_payload)
            logging.info(' Template "' + template_name + '" committed\n')
            report += 'New template "' + template_name + '" created and committed\n'

        else:
            # update the existing template if different

            # retrieve the existing template
            response = catalyst_center_api.configuration_templates.get_templates_details(name=template_name,
                                                                                         project_id=project_id)

            if response['response']:

                catalyst_center_existing_template = response['response'][0]['templateContent']
                # verify if matches the GitHub template
                if catalyst_center_existing_template == new_template:
                    logging.info(
                        ' Template "' + template_name + '" has not changed, identical template on Catalyst Center')
                    report += (
                            'Template "' + template_name + '" has not changed, identical template on Catalyst Center\n')
                else:
                    response = catalyst_center_api.configuration_templates.update_template(project_id=project_id,
                                                                                           templateContent=new_template,
                                                                                           language='JINJA',
                                                                                           name=template_name,
                                                                                           deviceTypes=device_types,
                                                                                           softwareType='IOS-XE',
                                                                                           author='Jenkins automation',
                                                                                           description='Updated by Python automation',
                                                                                           id=template_id)
                    logging.info(' Template "' + template_name + '" has changed, different template on Catalyst Center')
                    logging.info(' Updating existing template "' + template_name + '" id: ' + template_id)

                    time.sleep(10)

                    # commit the template
                    commit_payload = {
                        'comments': 'Jenkins automation committed',
                        'templateId': template_id
                    }
                    response = catalyst_center_api.configuration_templates.version_template(payload=commit_payload)
                    logging.info(' Template "' + template_name + '" committed\n')
                    report += (
                            'Template "' + template_name + '" has changed, updated and committed on Catalyst Center\n')

        # save template in local folder
        with open(('templates/' + file), 'w', encoding='utf-8') as f:
            f.write(new_template)

    logging.info('\nGitHub Sync Report:\n' + report)

    date_time = str(datetime.now().replace(microsecond=0))
    logging.info(' End of Application "catalyst_center_github_sync.py" Run: ' + date_time)

    return


if __name__ == '__main__':
    main()
