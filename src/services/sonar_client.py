import requests
import json
import os
import yaml

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
        sonar_task_url = f'http://localhost:9000/api/ce/task?id={task_id}'
        response = requests.get(sonar_task_url, headers=self.headers)
        self.current_task = response.json()
        return self.current_task

    def get_issues(self, prj_name, analysed_at):
        date_obj = str(analysed_at).split('+')[0]
        sonar_issue_url = f'http://localhost:9000/api/issues/search?components={prj_name}&createdAt={date_obj}%2B0000&ps=500&p=1'
        response = requests.get(sonar_issue_url, headers=self.headers)
        self.current_task = response.json()
        save_to_file(response.json(), prj_name, analysed_at)
        return self.current_task
    
    def delete_project(self, project_key):
        sonar_prj_delete_url = 'http://localhost:9000/api/projects/delete'
        data = {
            "project": project_key
        }
        response = requests.post(sonar_prj_delete_url, data=data, headers=self.headers)

    
def save_to_file(data, prj_name, analysed_at):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    root_dir = os.path.dirname(root_dir)

    issue_data_dir = os.path.join(root_dir, 'issue_data')
    os.makedirs(issue_data_dir, exist_ok=True)
    file_name = f"{prj_name}_{analysed_at}.json"
    file_path = os.path.join(issue_data_dir, file_name)

    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)

    print('Saving issues to file: ', file_path)
        