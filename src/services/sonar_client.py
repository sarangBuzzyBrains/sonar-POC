import requests
import json
import os
import yaml

PROPERTY_DATA = None

# Open the YAML file
with open("project-properties.yaml", "r") as file:
    # Load YAML data
    PROPERTY_DATA = yaml.safe_load(file)

# Access data from the YAML file
print(PROPERTY_DATA)

file_name_cnt = 1

class SonarClient:
    def __init__(self):
        # sonar_login_url = "http://localhost:9000/api/authentication/login"
        # payload = {'login': username, 'password': password}
        # # print('sonar_client_payload', payload)
        # response = requests.request('POST', sonar_login_url,  data=payload, verify=False)
        # self.username = username
        self.bearer_token = PROPERTY_DATA['USER_TOKEN']  # response.cookies.get('JWT-SESSION')
        self.headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            # 'Cookie': f'JWT-SESSION={self.bearer_token}'
        }
    
    def get_task(self, task_id):
        sonar_task_url = f'http://localhost:9000/api/ce/task?id={task_id}'
        # print(type(sonar_task_url), type(self.headers))
        response = requests.get(sonar_task_url, headers=self.headers)
        # print('task_method_url -->', response)
        self.current_task = response.json()
        return self.current_task

    def get_issues(self, prj_name, analysed_at):
        # sonar_task_url = f'http://localhost:9000/api/ce/task?id={task_id}'
        date_obj = str(analysed_at).split('+')[0]
        sonar_issue_url = f'http://localhost:9000/api/issues/search?components={prj_name}&createdAt={date_obj}%2B0000&ps=500&p=1'
        print('analysed_at ----> ', analysed_at, sonar_issue_url, self.headers)
        response = requests.get(sonar_issue_url, headers=self.headers)
        print('finnl_reponse', response)
        self.current_task = response.json()
        # print('issues___-->', response.json())
        save_to_file(response.json(), prj_name, analysed_at)
        # json_data = json.dumps(data, indent=4)
        # print('issues__---> ', json_data)
        return self.current_task
    
    def delete_project(self, project_key):
        sonar_prj_delete_url = 'http://localhost:9000/api/projects/delete'
        data = {
            "project": project_key
        }
        response = requests.post(sonar_prj_delete_url, data=data, headers=self.headers)

    
def save_to_file(data, prj_name, analysed_at):
    # print(data, type(data))
    print('Total Issues: ', data["total"])
    for i in range(0, min(10, len( data["issues"]))):
        print(i+1,  data["issues"][i]["message"])
    global file_name_cnt
    # Write dictionary to JSON file

    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the root folder (one level up)
    root_dir = os.path.dirname(script_dir)
    root_dir = os.path.dirname(root_dir)

    # Specify the directory name for the issue data
    issue_data_dir = os.path.join(root_dir, 'issue_data')

    # Create the directory if it doesn't exist
    os.makedirs(issue_data_dir, exist_ok=True)

    # Specify the file name in the current directory
    file_name = f"{prj_name}_{analysed_at}.json"

    # Write dictionary to JSON file in the current directory
    file_path = os.path.join(issue_data_dir, file_name)
    print('file_path_while_saving --> ', file_path)

    file_name_cnt += 1
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)
        