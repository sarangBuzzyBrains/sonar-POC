import os
import tempfile
import requests
import git
import subprocess
import threading
import shutil
from faker import Faker
import random

from .logger_config import logger, custom_write_file
from ..services import sonar_client
from .sonar_client import PROPERTY_DATA
from .config import is_scan_running, PROJECT_WORKING_DIRECTORY

fake = Faker()
base_branch = None
new_branch = None
repo_url = None
usr_repo = None
usr_proj_dir = None

def create_repo_url(repo_url, access_token=None):
    if(access_token):
        repo_url = repo_url.replace('https://', f'https://token:{access_token}@')
    # print('repo_url_____________> ', repo_url)
    return repo_url

def get_pr_details(pr_url, access_token=None):
    pr_parts = pr_url.split('/')
    owner = pr_parts[3]
    repo = pr_parts[4]
    pr_number = pr_parts[6]

    headers = {}
    if(access_token):
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        pr_details = response.json()
        return pr_details
    else:
        logger.error(f"Failed to fetch PR details. Status code: {response.status_code}")
        return None

def clone_project(usr_proj_dir, repo_url, project_key=''):
    repo = git.Repo.clone_from(repo_url, usr_proj_dir)
    custom_write_file(project_key,f'Cloned project to directory {usr_proj_dir}')
    logger.info(f'Cloned project to directory {usr_proj_dir}')
    return repo

def run_sonar_scanner_and_delete_dir(project_key, buildnum, usr_proj_dir, preserve_project=False):
    run_sonar_scanner(project_key, buildnum, preserve_project)
    try:
        shutil.rmtree(usr_proj_dir)
        custom_write_file(project_key, f"Directory '{usr_proj_dir}' successfully deleted.")
        logger.info(f"Directory '{usr_proj_dir}' successfully deleted.")
    except Exception as e:
        custom_write_file(project_key, f"Error deleting directory '{usr_proj_dir}': {e}")
        logger.error(f"Error deleting directory '{usr_proj_dir}': {e}")
        raise Exception()
    

def run_sonar_scanner(project_key, buildnum = 1, preserve_project=False):
    global is_scan_running
    try:
        logger.info(f'Running sonarscan for project {project_key}')
        # mvn clean verify sonar:sonar
        run_options = [
                "-Dsonar.projectKey=" + f"{project_key}",
                "-Dsonar.sources=.",
                "-Dsonar.host.url=" + f"{PROPERTY_DATA['HOST_URL']}",
                "-Dsonar.token=" + f"{PROPERTY_DATA['USER_TOKEN']}",
                "-Dsonar.analysis.buildnum=" + f"{buildnum}",
                "-Dsonar.analysis.preserve_project=" + f"{preserve_project}"
            ]

        try:
            if os.path.exists("pom.xml"):
                run_java_command = ["mvn clean verify sonar:sonar -DskipTests=true " + run_options[0] +" " + run_options[1] +" "+ run_options[2] +" "+ run_options[3] +" "+ run_options[4] +" "+ run_options[5]]
                custom_write_file(project_key, f"Running sonarscanner command: {run_java_command}")
                
                with open(f'{PROJECT_WORKING_DIRECTORY}/req_logs/{project_key}.log', 'a') as curLogFile:
                    subprocess.run(run_java_command, stdout=curLogFile, stderr=curLogFile, check=True, shell=True)
                logger.info(f"pom.xml exists. Executing sonarscan for java code, command: {run_options}")
            else:
                run_generic_command = ["sonar-scanner"] + run_options
                custom_write_file(project_key, f"Running sonarscanner for generic code, command: {run_generic_command}")
                with open(f'{PROJECT_WORKING_DIRECTORY}/req_logs/{project_key}.log', 'a') as curLogFile:
                    subprocess.run(run_generic_command, stdout=curLogFile, stderr=curLogFile, check=True, shell=False)
                  
        except Exception as e:
            print(e)
            is_scan_running.append(False)
            logger.error(f'subprocess failer, is scan running: {is_scan_running}')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Sonar Scanner: {e}")
        raise Exception('v')


def run_sonar_in_source_branch(project_key, preserve_project):
    global new_branch
    global base_branch
    global repo_url
    global usr_repo
    global usr_proj_dir

    usr_repo.git.checkout(new_branch)
    usr_repo.git.checkout(base_branch)

    # current branch -> base branch
    merge_response = usr_repo.git.merge(new_branch)
   
    logger.info('Checkout to source branch')
    custom_write_file(project_key, f'Merged source in target branch { new_branch}')
    sonar_thread = threading.Thread(target=run_sonar_scanner_and_delete_dir, args=(project_key, 2, usr_proj_dir, preserve_project))
    sonar_thread.start()


def get_new_code_issues(prj_name, analysed_at):
    sonanrUsr = sonar_client.SonarClient() 
    sonanrUsr.get_new_issues(prj_name, analysed_at)

def get_all_issue(prj_name, analysed_at):
    sonanrUsr = sonar_client.SonarClient() 
    sonanrUsr.get_all_issues(prj_name, analysed_at)

def delete_project(project_ke):
    sonanrUsr = sonar_client.SonarClient()
    sonanrUsr.delete_project(project_ke)

def pr_analysis(pr_url, project_key, access_token, preserve_project):
    global new_branch
    global base_branch
    global repo_url
    global usr_repo
    global usr_proj_dir

    # genrate unique projectkey
    pr_details = get_pr_details(pr_url, access_token)
    pr_parts = pr_url.split('/')
    owner = pr_parts[3]
    repo = pr_parts[4]
    logger.info(f'Project key : {project_key}')

    if(pr_details):
        base_branch = pr_details['base']['ref']
        new_branch = pr_details['head']['ref'] 
        repo_url = pr_details['base']['repo']['clone_url']
        usr_proj_dir = tempfile.mkdtemp() 
        repo_url = create_repo_url(repo_url, access_token)

        # print('pr_branches--> ', new_branch, base_branch, usr_proj_dir)

        usr_repo = clone_project(usr_proj_dir, repo_url) 
        usr_repo.git.checkout(base_branch) # target
        custom_write_file(project_key, f'Checkout to target branch { base_branch}')
        os.chdir(usr_proj_dir)

        logger.info(f'Checkout to target branch')
        
        sonar_thread = threading.Thread(target=run_sonar_scanner, args=(project_key, 1, preserve_project))
        sonar_thread.start()

        return project_key
    return "error"

def repo_analysis(repo_url, project_key, access_token=None, preserve_project=False, repo_branch=None):
    
    logger.info(f'Project key : {project_key}')
    custom_write_file(project_key, f'Project key : {project_key}')

    # make temporary directory and clone project
    usr_proj_dir = tempfile.mkdtemp() 
    repo_url = create_repo_url(repo_url, access_token)
    usr_repo = clone_project(usr_proj_dir, repo_url, project_key)
    if repo_branch:
        usr_repo.git.checkout(repo_branch)
    os.chdir(usr_proj_dir)

    # start sonar scan on separate thread
    sonar_thread = threading.Thread(target=run_sonar_scanner_and_delete_dir, args=(project_key, 3, usr_proj_dir, preserve_project))
    sonar_thread.start()

    return project_key

def generate_random_string():
    num_words = random.randint(5, 10)
    random_words = [fake.word()[0] for _ in range(num_words)]
    random_string = ''.join(random_words)
    return random_string



# ------------------ Bitbucket code --------------------

def bitbucket_clone_project(usr_proj_dir, repo_url, access_token, bitbucket_username, project_key):
    # repo = git.Repo.clone_from(repo_url, usr_proj_dir, auth=(bitbucket_username, access_token))
    repo = git.Repo.clone_from(repo_url, usr_proj_dir)
    custom_write_file(project_key,f'Cloned bitbucket project to directory {usr_proj_dir}')
    logger.info(f'Cloned project to directory {usr_proj_dir}')
    return repo

def create_repo_url_for_bitbucket(repo_url, access_token):
    if(access_token):
        repo_url = repo_url.replace('https://', f'https://x-token-auth:{access_token}@')
    # print('repo_url_____________> ', repo_url)
    return repo_url

def get_bitbucket_pr_details(pr_url, access_token):
    pr_parts = pr_url.split('/')
    workspace = pr_parts[3]
    repo_slug = pr_parts[4]
    pr_id = pr_parts[6]

    api_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}"
    headers = {}
    if access_token:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
    # print('api_url_for_pr_______> ', api_url)
    # print('header__________> ', headers)
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        pr_details = response.json()
        return pr_details
    else:
        print(f"Failed to fetch PR details. Status code: {response.status_code}")
        return None

def bitbucket_repo_analysis(repo_url, project_key, access_token, preserve_project, repo_branch, bitbucket_username):
    
    logger.info(f'Project key : {project_key}')
    custom_write_file(project_key, f'Project key : {project_key}')

    # make temporary directory and clone project
    usr_proj_dir = tempfile.mkdtemp()
    repo_url = create_repo_url_for_bitbucket(repo_url, access_token)
    usr_repo = bitbucket_clone_project(usr_proj_dir, repo_url, access_token, bitbucket_username, project_key)
    if repo_branch:
        usr_repo.git.checkout(repo_branch)
    os.chdir(usr_proj_dir)

    # start sonar scan on separate thread
    sonar_thread = threading.Thread(target=run_sonar_scanner_and_delete_dir, args=(project_key, 3, usr_proj_dir, preserve_project))
    sonar_thread.start()

    return project_key

def bitbucket_pr_analysis(pr_url, project_key, access_token, preserve_project):
    global new_branch
    global base_branch
    global repo_url
    global usr_repo
    global usr_proj_dir

    # genrate unique projectkey
    pr_details = get_bitbucket_pr_details(pr_url, access_token)
    # print('pr_details____________> ', pr_details)
    pr_parts = pr_url.split('/')
    owner = pr_parts[3]
    repo = pr_parts[4]
    logger.info(f'Project key : {project_key}')

    if(pr_details):
        base_branch = pr_details['destination']['branch']['name']
        new_branch = pr_details['source']['branch']['name'] 
        repo_url = pr_details['destination']['repository']['links']['html']['href']
        usr_proj_dir = tempfile.mkdtemp() 
        # print('base_branch___> ', base_branch)
        # print('new_branch___> ', new_branch)
        # print('repo_url___> ', repo_url)
        repo_url = create_repo_url_for_bitbucket(repo_url, access_token)
        # print('repo_url___> ', repo_url)

        # print('pr_branches--> ', new_branch, base_branch, usr_proj_dir)

        usr_repo = clone_project(usr_proj_dir, repo_url) 
        usr_repo.git.checkout(base_branch) # target
        custom_write_file(project_key, f'Checkout to target branch { base_branch}')
        os.chdir(usr_proj_dir)

        logger.info(f'Checkout to target branch')
        
        sonar_thread = threading.Thread(target=run_sonar_scanner, args=(project_key, 1, preserve_project))
        sonar_thread.start()

        return project_key
    return "error"
