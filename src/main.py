from fastapi import FastAPI, Request
import requests
import json
import datetime
import os
from .services import sonar_service
from .services.logger_config import logger, setup_logger, custom_write_file
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .services.config import PROJECT_WORKING_DIRECTORY
from .services.config import is_scan_running

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_server_ip():
    response = requests.get('https://api.ipify.org')
    return response.text.strip()

SERVER_IP = get_server_ip()
PORT = 3000

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
issue_data_dir = os.path.join(root_dir, 'issue_data')
log_dir = os.path.join(root_dir, 'req_logs')
sonar = None
project_key = None
new_analysed_at = None

# route to serve the files
app.mount("/files/issue_data", StaticFiles(directory=issue_data_dir), name="issue_list")
app.mount("/files/log", StaticFiles(directory=log_dir), name="log_file")

@app.get("/file/{file_name}")
async def get_file(file_name: str):
    return {"file_name": file_name}

@app.post("/webhook")
async def the_webhook(request: Request):
    global is_scan_running
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))
    project_key = payload["project"]["key"]
    
    logger.info(f'***************** Scan details details ******************\n TaskId: {payload["taskId"]}\n analysedAt: {payload["analysedAt"]}\n project: {payload["project"]["key"]}\n Buildnum: {payload["properties"]["sonar.analysis.buildnum"]}')
    custom_write_file(project_key, f'***************** Scan details details ******************\n TaskId: {payload["taskId"]}\n analysedAt: {payload["analysedAt"]}\n project: {payload["project"]["key"]}\n Buildnum: {payload["properties"]["sonar.analysis.buildnum"]} \n preserve_project:{payload["properties"]["sonar.analysis.preserve_project"]} \n\n\n')
    
    try:
        if(payload["properties"]["sonar.analysis.buildnum"] == '1'):
            custom_write_file(project_key, 'Starting second run in source branch')
            logger.info('Starting second run in source branch')
            preserve_project = payload["properties"]["sonar.analysis.preserve_project"]
            # print('sonar_scanning_for_source_branch', preserve_project)
            sonar_service.run_sonar_in_source_branch(project_key, preserve_project)

        elif (payload["properties"]["sonar.analysis.buildnum"] == '2'):
            new_analysed_at = payload["analysedAt"]
            sonar_service.get_new_code_issues(project_key, new_analysed_at)
            preserve_project = payload["properties"]["sonar.analysis.preserve_project"]
            if preserve_project == 'False':
                sonar_service.delete_project(project_key)
            current_directory = os.getcwd()
            os.chdir(current_directory)
            is_scan_running.append(False)

        elif (payload["properties"]["sonar.analysis.buildnum"] == '3'):
            # print(payload["properties"]["sonar.analysis.buildnum"], payload["analysedAt"])
            new_analysed_at = payload["analysedAt"]
            sonar_service.get_all_issue(project_key, new_analysed_at)
            preserve_project = payload["properties"]["sonar.analysis.preserve_project"]
            if preserve_project == 'False':
                sonar_service.delete_project(project_key)

            current_directory = os.path.dirname(__file__)
            os.chdir(current_directory)
            is_scan_running.append(False)
        return payload
    except Exception as e:
        is_scan_running.append(False)
        logger.error(f'Error in repo analysis: {e}')
        os.chdir(PROJECT_WORKING_DIRECTORY)


@app.post("/pr_analysis")
async def get_pr_analysis(request: Request):
    global is_scan_running
    global SERVER_IP

    try:
        if(is_scan_running[len(is_scan_running)-1]):
            return { "message": "Previous Scan is still running" }
        is_scan_running.append(True)

        req_body = await request.body()
        payload = json.loads(req_body.decode('utf-8'))
        current_time = datetime.datetime.now()

        access_token = None
        preserve_project = False
        if "token" in payload:
            access_token = payload["token"]

        if "preserve_project" in payload:
            preserve_project = payload["preserve_project"]

        pr_parts = payload["url"].split('/')
        owner = pr_parts[3]
        repo = pr_parts[4]
        random_string = sonar_service.generate_random_string()
        project_key = owner + '-' + repo + '-' + random_string

        custom_write_file(project_key, f"================ PR analysis started {current_time}====================")
        
        logger.info(f"================= PR analysis started {current_time} ===================")
        prj_key = sonar_service.pr_analysis(payload["url"], project_key, access_token, preserve_project)
        
        return { 
            "issue_list":  f'http://{SERVER_IP}:{PORT}/files/issue_data/{prj_key}.json',
            "log_file": f'http://{SERVER_IP}:{PORT}/files/log/{project_key}.log'
        }
    except Exception as e:
        is_scan_running.append(False)
        logger.error(f'Error in pr analysis: {e}')
        os.chdir(PROJECT_WORKING_DIRECTORY)
        return { "message": "Error: try again" }

@app.post("/repo_analysis")
async def get_repo_analysis(request: Request):
    global is_scan_running
    global SERVER_IP

    try:
        if(is_scan_running[len(is_scan_running)-1]):
            return { "message": "Previous Scan is still running" }
        is_scan_running.append(True)

        req_body = await request.body()
        payload = json.loads(req_body.decode('utf-8'))

        access_token = None
        preserve_project = False
        repo_branch = None
        if "token" in payload:
            access_token = payload["token"]

        if "preserve_project" in payload:
            preserve_project = payload["preserve_project"]

        if "repo_branch" in payload:
            repo_branch = payload["repo_branch"]

        current_time = datetime.datetime.now()

        pr_parts = payload["url"].split('/')
        owner = pr_parts[3]
        repo = pr_parts[4]
        random_string = sonar_service.generate_random_string()
        project_key = owner + '-' + repo + '-' + random_string

        # return project_key

        custom_write_file(project_key, f"================ Repo analysis started {current_time}====================")
        
        logger.info(f"================ Repo analysis started {current_time}====================", extra={'file_id':f'req_logs/{current_time}.log'})    
        prj_key = sonar_service.repo_analysis(payload["url"], project_key, access_token, preserve_project, repo_branch)

        return {
            "issue_list": f'http://{SERVER_IP}:{PORT}/files/issue_data/{prj_key}.json',
            "log_file": f'http://{SERVER_IP}:{PORT}/files/log/{project_key}.log'
        }
    except Exception as e:
        is_scan_running.append(False)
        print('error: ', e)
        logger.error(f'Error in repo analysis: {e}')
        os.chdir(PROJECT_WORKING_DIRECTORY)
        return { "message": "Error: try again" }
        

# ------------- Bibucket Code -------------------------

@app.post("/bitbucket/repo_analysis")
async def get_bitbucket_repo_analysis(request: Request):
    global is_scan_running
    global SERVER_IP

    try:
        if(is_scan_running[len(is_scan_running)-1]):
            return { "message": "Previous Scan is still running" }
        is_scan_running.append(True)

        req_body = await request.body()
        payload = json.loads(req_body.decode('utf-8'))

        access_token = None
        preserve_project = False
        repo_branch = None
        bitbucket_username = None
        if "token" in payload:
            access_token = payload["token"]

        if "preserve_project" in payload:
            preserve_project = payload["preserve_project"]

        if "repo_branch" in payload:
            repo_branch = payload["repo_branch"]

        if "bitbucket_username" in payload:
            bitbucket_username = payload["bitbucket_username"]

        current_time = datetime.datetime.now()

        pr_parts = payload["url"].split('/')
        owner = pr_parts[3]
        repo = pr_parts[4]
        random_string = sonar_service.generate_random_string()
        project_key = owner + '-' + repo + '-' + random_string

        # return project_key

        custom_write_file(project_key, f"================ Repo analysis started {current_time}====================")
        
        logger.info(f"================ Repo analysis started {current_time}====================", extra={'file_id':f'req_logs/{current_time}.log'})    
        sonar_service.bitbucket_repo_analysis(payload["url"], project_key, access_token, preserve_project, repo_branch, bitbucket_username)

        return {
            "issue_list": f'http://{SERVER_IP}:{PORT}/files/issue_data/{project_key}.json',
            "log_file": f'http://{SERVER_IP}:{PORT}/files/log/{project_key}.log'
        }
    except Exception as e:
        is_scan_running.append(False)
        print('error: ', e)
        logger.error(f'Error in repo analysis: {e}')
        os.chdir(PROJECT_WORKING_DIRECTORY)
        return { "message": "Error: try again" }
 
 
@app.post("/bitbucket/pr_analysis")
async def get_pr_analysis(request: Request):
    global is_scan_running
    global SERVER_IP

    try:
        if(is_scan_running[len(is_scan_running)-1]):
            return { "message": "Previous Scan is still running" }
        is_scan_running.append(True)

        req_body = await request.body()
        payload = json.loads(req_body.decode('utf-8'))
        current_time = datetime.datetime.now()

        access_token = None
        preserve_project = False
        if "token" in payload:
            access_token = payload["token"]

        if "preserve_project" in payload:
            preserve_project = payload["preserve_project"]

        pr_parts = payload["url"].split('/')
        owner = pr_parts[3]
        repo = pr_parts[4]
        random_string = sonar_service.generate_random_string()
        project_key = owner + '-' + repo + '-' + random_string

        custom_write_file(project_key, f"================ PR analysis started {current_time}====================")
        
        logger.info(f"================= PR analysis started {current_time} ===================")
        prj_key = sonar_service.bitbucket_pr_analysis(payload["url"], project_key, access_token, preserve_project)
        
        return { 
            "issue_list":  f'http://{SERVER_IP}:{PORT}/files/issue_data/{prj_key}.json',
            "log_file": f'http://{SERVER_IP}:{PORT}/files/log/{project_key}.log'
        }
    except Exception as e:
        is_scan_running.append(False)
        logger.error(f'Error in pr analysis: {e}')
        os.chdir(PROJECT_WORKING_DIRECTORY)
        return { "message": "Error: try again" }



@app.get("/health")
def health():
    return { "status": "up" }


@app.get("/")
def health():
    return { "status": "up" }

