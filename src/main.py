from fastapi import FastAPI, Request
import json
from .services import sonar_service

app = FastAPI()
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

    elif (payload["properties"]["sonar.analysis.buildnum"] == '3'):
        new_analysed_at = payload["analysedAt"]
        sonar_service.get_new_code_issues(project_key, new_analysed_at)
        sonar_service.delete_project(project_key)

    return payload

@app.post("/pr_analysis")
async def my_func(request: Request):
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))
    sonar_service.pr_analysis(payload["url"])
    return 'success'

@app.post("/repo_analysis")
async def my_func(request: Request):
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))
    sonar_service.repo_analysis(payload["url"])
    return 'success'

@app.get("/health")
def health():
    return { "status": "up" }

