import os
import tempfile
import requests
import git
import subprocess
import threading
import shutil
from faker import Faker
import random

from ..services import sonar_client
from .sonar_client import PROPERTY_DATA

fake = Faker()
base_branch = None
new_branch = None
repo_url = None
usr_repo = None
usr_proj_dir = None

def get_pr_details(pr_url):
    pr_parts = pr_url.split('/')
    owner = pr_parts[3]
    repo = pr_parts[4]
    pr_number = pr_parts[6]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    response = requests.get(api_url)
    if response.status_code == 200:
        pr_details = response.json()
        return pr_details
    else:
        print(f"Failed to fetch PR details. Status code: {response.status_code}")
        return None

def clone_project(usr_proj_dir, repo_url):
    repo = git.Repo.clone_from(repo_url, usr_proj_dir)
    return repo

def run_sonar_scanner_and_delete_dir(project_key, buildnum, usr_proj_dir, logger):
    run_sonar_scanner(project_key, buildnum)
    try:
        shutil.rmtree(usr_proj_dir)
        logger.info(f"Directory '{usr_proj_dir}' successfully deleted.")
    except Exception as e:
        logger.info(f"Error deleting directory '{usr_proj_dir}': {e}")

def run_sonar_scanner(project_key, buildnum = 1):
    try:
        print('Sonarscan running...............')
        maven_command = []
        if os.path.exists("pom.xml"):
            maven_command.append("mvn clean verify sonar:sonar")
        print('pom_xmls_existing-----> ', maven_command)
        
        run_commands = [
                "sonar-scanner",
                "-Dsonar.projectKey=" + f"{project_key}",
                "-Dsonar.sources=.",
                "-Dsonar.host.url=" + f"{PROPERTY_DATA['HOST_URL']}",
                "-Dsonar.token=" + f"{PROPERTY_DATA['USER_TOKEN']}",
                "-Dsonar.analysis.buildnum=" + f"{buildnum}"
            ]

        # print('run_command ----> ', run_commands)
        with open(os.devnull, 'w') as devnull:
            subprocess.run(run_commands,  stdout=devnull, stderr=subprocess.STDOUT, check=True)
        print("Sonar Scanner analysis completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running Sonar Scanner: {e}")


def run_sonar_in_source_branch(project_key):
    global new_branch
    global base_branch
    global repo_url
    global usr_repo
    r = usr_repo.git.checkout(new_branch)
    print('Checkout to source branch')
    run_sonar_scanner(project_key, 2)
    current_directory = os.getcwd()

    try:
        shutil.rmtree(current_directory)
        print(f"Directory '{current_directory}' successfully deleted.")
    except Exception as e:
        print(f"Error deleting directory '{current_directory}': {e}")

def get_new_code_issues(prj_name, analysed_at):
    sonanrUsr = sonar_client.SonarClient() 
    sonanrUsr.get_new_issues(prj_name, analysed_at)

def get_all_issue(prj_name, analysed_at):
    sonanrUsr = sonar_client.SonarClient() 
    sonanrUsr.get_all_issues(prj_name, analysed_at)

def delete_project(project_ke):
    sonanrUsr = sonar_client.SonarClient()
    sonanrUsr.delete_project(project_ke)

def pr_analysis(pr_url):
    global new_branch
    global base_branch
    global repo_url
    global usr_repo
    pr_details = get_pr_details(pr_url)
    pr_parts = pr_url.split('/')
    owner = pr_parts[3]
    repo = pr_parts[4]
    random_string = generate_random_string()
    project_key = owner + '-' + repo + '-' + random_string
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    root_dir = os.path.dirname(root_dir)
    issue_data_dir = os.path.join(root_dir, 'issue_data')
    file_name = f"{project_key}.json"
    file_path = os.path.join(issue_data_dir, file_name)

    if(pr_details):
        base_branch = pr_details['base']['ref']
        new_branch = pr_details['head']['ref'] 
        repo_url = pr_details['base']['repo']['clone_url']
        usr_proj_dir = tempfile.mkdtemp() 
        usr_repo = clone_project(usr_proj_dir, repo_url) 

        usr_repo.git.checkout(base_branch)
        os.chdir(usr_proj_dir)
        print('Checkout to target branch', project_key, type(project_key))
        # sonar_thread = threading.Thread(target=run_sonar_scanner, args=(project_key))
        # sonar_thread.start()
        run_sonar_scanner(project_key)
        return project_key
    return "error"

def repo_analysis(repo_url, logger):
    pr_parts = repo_url.split('/')
    owner = pr_parts[3]
    repo = pr_parts[4]
    random_string = generate_random_string()

    project_key = owner + '-' + repo + '-' + random_string
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    root_dir = os.path.dirname(root_dir)
    issue_data_dir = os.path.join(root_dir, 'issue_data')
    file_name = f"{project_key}.json"
    file_path = os.path.join(issue_data_dir, file_name)
    logger.info(f'pre_generated_file_path: {file_path}')

    usr_proj_dir = tempfile.mkdtemp() 
    usr_repo = clone_project(usr_proj_dir, repo_url)

    os.chdir(usr_proj_dir)
    sonar_thread = threading.Thread(target=run_sonar_scanner_and_delete_dir, args=(project_key, 3, usr_proj_dir, logger))
    sonar_thread.start()

    return project_key

def generate_random_string():
    num_words = random.randint(5, 10)
    random_words = [fake.word()[0] for _ in range(num_words)]
    random_string = ''.join(random_words)
    return random_string
