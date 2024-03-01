import requests
import json
import os
import yaml
from .logger_config import logger, custom_write_file

PROPERTY_DATA = None

with open("project-properties.yaml", "r") as file:
    PROPERTY_DATA = yaml.safe_load(file)

class SonarClient:
    def __init__(self):
        self.bearer_token = PROPERTY_DATA['USER_TOKEN']  # response.cookies.get('JWT-SESSION')
        self.headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }
    
    def get_task(self, task_id):
        sonar_task_url = f'{PROPERTY_DATA["HOST_URL"]}/api/ce/task?id={task_id}'
        response = requests.get(sonar_task_url, headers=self.headers)
        self.current_task = response.json()
        return self.current_task

    def get_new_issues(self, prj_name, analysed_at):
        date_obj = str(analysed_at).split('+')
        sonar_issue_url = f'{PROPERTY_DATA["HOST_URL"]}/api/issues/search?components={prj_name}&facets=types,severities,cleanCodeAttributeCategories,impactSoftwareQualities&createdAt={date_obj[0]}%2B{date_obj[1]}&ps=500&p=1'
        
        response = requests.get(sonar_issue_url, headers=self.headers)
        self.new_issues = response.json()
        sonar_measure_url = f'{PROPERTY_DATA["HOST_URL"]}/api/measures/search_history?component={prj_name}&metrics=ncloc,coverage,new_violations&ps=1000'
        response = requests.get(sonar_measure_url, headers=self.headers)
        self.new_issues["measures_history"] = response.json()

        save_to_file(self.new_issues, prj_name)
        
        return self.new_issues
    
    def get_all_issues(self, prj_name, analysed_at):
        sonar_issue_url = f'{PROPERTY_DATA["HOST_URL"]}/api/issues/search?components={prj_name}&facets=types,severities,cleanCodeAttributeCategories,impactSoftwareQualities&ps=500&p=1'
        
        response = requests.get(sonar_issue_url, headers=self.headers)
        self.all_issues = response.json()

        sonar_measure_url = f'{PROPERTY_DATA["HOST_URL"]}/api/measures/search_history?component={prj_name}&metrics=bugs,code_smells,vulnerabilities,reliability_rating,security_rating,sqale_rating&ps=1000'
        response = requests.get(sonar_measure_url, headers=self.headers)
        self.all_issues["measures_history"] = response.json()

        save_to_file(self.all_issues, prj_name)
        
        return self.all_issues
    
    def delete_project(self, project_key):
        sonar_prj_delete_url = f'{PROPERTY_DATA["HOST_URL"]}/api/projects/delete'
        data = {
            "project": project_key
        }
        requests.post(sonar_prj_delete_url, data=data, headers=self.headers)
        custom_write_file(project_key, f'Deleted sonarqube project {project_key}')
        logger.info(f'Deleted sonarqube project {project_key}')

    
def save_to_file(data, prj_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    root_dir = os.path.dirname(root_dir)

    issue_data_dir = os.path.join(root_dir, 'issue_data')
    os.makedirs(issue_data_dir, exist_ok=True)

    file_name = f"{prj_name}.json"
    file_path = os.path.join(issue_data_dir, file_name)

    try:
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        custom_write_file(prj_name, f'********** Process completed. Saved issues to file: {file_path} ***************')
        logger.info(f'********** Process completed. Saved issues to file: {file_path} ***************')
    except Exception as e:
        custom_write_file(prj_name, f'Failed to save issues to file: {e}')
        logger.error(f'Failed to save issues to file: {e}')
                