from fastapi import FastAPI, Request, HTTPException
import requests
import json
from .services import sonar_service

app = FastAPI()
sonar = None
new_code_analysis = False
project_key = None
old_analysed_at = None
new_analysed_at = None

@app.post("/webhook")
async def the_webhook(request: Request):
    global new_code_analysis
    global project_key
    global old_analysed_at
    global new_analysed_at
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))
    print(payload)
    print('----------- Scan details details ---------------')
    print('TaskId: ', payload["taskId"])
    print('analysedAt: ', payload["analysedAt"])
    print('project: ', payload["project"]["key"])
    print('Buildnum: ', payload["project"]["sonar.analysis.buildnum"])
    print('------------------------------------------------')
    
    if(payload["project"]["sonar.analysis.buildnum"] == 1):
        project_key = payload["project"]["key"]
        old_analysed_at = payload["analysedAt"]
        # print('task_details___> ', project_name, old_analysed_at)
        new_code_analysis = True
        # sonar_service.get_new_code_issues(project_name, old_analysed_at)

        # merge source branch in target branch
        sonar_service.run_sonar_in_source_branch(project_key)
    elif (payload["project"]["sonar.analysis.buildnum"] == 2):
        new_analysed_at = payload["analysedAt"]
        sonar_service.get_new_code_issues(project_key, new_analysed_at)
        sonar_service.delete_project(project_key)
    elif (payload["project"]["sonar.analysis.buildnum"] == 3):
        new_analysed_at = payload["analysedAt"]
        sonar_service.get_new_code_issues(project_key, new_analysed_at)
    return payload

@app.post("/pr_analysis")
async def my_func(request: Request):
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))
    sonar_service.pr_analysis(payload["url"])

@app.post("/repo_analysis")
async def my_func(request: Request):
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))
    sonar_service.repo_analysis(payload["url"])

@app.get("/health")
def health():
    return { "status": "up" }

