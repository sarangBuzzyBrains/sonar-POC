from fastapi import FastAPI, Request
import json
import os
from .services import sonar_service
from .services.logger_config import setup_logger
from fastapi.middleware.cors import CORSMiddleware
import datetime

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
sonar = None
project_key = None
new_analysed_at = None

@app.post("/webhook")
async def the_webhook(request: Request):
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))

    print('----------- Scan details details ---------------')
    print('TaskId: ', payload["taskId"])
    print('analysedAt: ', payload["analysedAt"])
    print('project: ', payload["project"]["key"])
    print('Buildnum: ', payload["properties"]["sonar.analysis.buildnum"])
    print('------------------------------------------------')
    
    project_key = payload["project"]["key"]
    if(payload["properties"]["sonar.analysis.buildnum"] == '1'):
        sonar_service.run_sonar_in_source_branch(project_key)

    elif (payload["properties"]["sonar.analysis.buildnum"] == '2'):
        new_analysed_at = payload["analysedAt"]
        sonar_service.get_new_code_issues(project_key, new_analysed_at)
        sonar_service.delete_project(project_key)
        current_directory = os.path.dirname(__file__)
        os.chdir(current_directory)

    elif (payload["properties"]["sonar.analysis.buildnum"] == '3'):
        new_analysed_at = payload["analysedAt"]
        sonar_service.get_all_issue(project_key, new_analysed_at)
        sonar_service.delete_project(project_key)
        current_directory = os.path.dirname(__file__)
        os.chdir(current_directory)

    return payload

@app.post("/pr_analysis")
async def my_func(request: Request):
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))
    file_path = sonar_service.pr_analysis(payload["url"])
    return {"Sonarqbe-Pr-Analysis-Response": file_path}

@app.post("/repo_analysis")
async def my_func(request: Request):
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_name = f'{payload["url"].split("/")[3]}_{payload["url"].split("/")[4]}_{timestamp}.log'
    
    logger = setup_logger(__name__, log_file_name)
    file_path = sonar_service.repo_analysis(payload["url"], logger)
    return {"Sonarqbe-Repo-Analysis-Response": file_path}

@app.get("/health")
def health():
    return { "status": "up" }

@app.get("/")
def health():
    return { "status": "up" }

