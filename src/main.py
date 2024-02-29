from fastapi import FastAPI, Request
import socket
import requests
import json
import os
from .services import sonar_service
from .services.logger_config import setup_logger
from fastapi.middleware.cors import CORSMiddleware
import datetime
from fastapi.staticfiles import StaticFiles
import uvicorn

is_scan_running = False

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# def get_server_ip():
#     hostname = socket.gethostname()
#     ip_address = socket.gethostbyname(hostname)
#     return ip_address


def get_server_ip():
    response = requests.get('https://api.ipify.org')
    return response.text.strip()

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
issue_data_dir = os.path.join(root_dir, 'issue_data')
log_dir = os.path.join(root_dir, 'req_logs')
app.mount("/files/issue_data", StaticFiles(directory=issue_data_dir), name="issue_list")
app.mount("/files/log", StaticFiles(directory=log_dir), name="log_file")
sonar = None
project_key = None
new_analysed_at = None

# Define a route to serve the files
@app.get("/file/{file_name}")
async def get_file(file_name: str):
    return {"file_name": file_name}

@app.post("/webhook")
async def the_webhook(request: Request):
    global is_scan_running
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
        is_scan_running = False

    elif (payload["properties"]["sonar.analysis.buildnum"] == '3'):
        new_analysed_at = payload["analysedAt"]
        sonar_service.get_all_issue(project_key, new_analysed_at)
        sonar_service.delete_project(project_key)
        current_directory = os.path.dirname(__file__)
        os.chdir(current_directory)
        is_scan_running = False

    return payload

@app.post("/pr_analysis")
async def my_func(request: Request):
    global is_scan_running
    if(is_scan_running):
        return "Previous Scan is still running"
    is_scan_running = True
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))
    file_path = sonar_service.pr_analysis(payload["url"])
    server_ip = get_server_ip()
    port_number = uvicorn.Config(app).port
    return { 
        "issue_list":  f'http://{server_ip}:{3000}/files/issue_data/{file_path}.json',
        "log_file": f'http://{server_ip}:{3000}/files/log/program.log'
    }

@app.post("/repo_analysis")
async def my_func(request: Request):
    global is_scan_running
    if(is_scan_running):
        return "Previous Scan is still running"
    is_scan_running = True
    req_body = await request.body()
    payload = json.loads(req_body.decode('utf-8'))

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_name = f'{payload["url"].split("/")[3]}_{payload["url"].split("/")[4]}_{timestamp}.log'
    
    logger = setup_logger(__name__, log_file_name)
    file_path = sonar_service.repo_analysis(payload["url"], logger)
    server_ip = get_server_ip()
    port_number = uvicorn.Config(app).port
    return {
        "issue_list": f'http://{server_ip}:{3000}/files/issue_data/{file_path}.json',
        "log_file": f'http://{server_ip}:{3000}/files/log/program.log'
    }


@app.get("/health")
def health():
    return { "status": "up" }


@app.get("/")
def health():
    return { "status": "up" }

