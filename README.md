### Webhook setup
1. Go to Administration > General setting > security and disable `Enable local webhooks validation`
2. Go to Administration > Configuration > Webhook and create a webhook
3. Add the url `http://localhost:3001/webhook`
4. Keep the secret empty


### Project setup

1. update the `project.properties.yaml` file
2. Create virtual env
`python3 -m venv venv`
3. Activate virtual env
`source venv/bin/activate `
4. Install dependencies
`pip install -r requirements.txt`
5. Run command
`uvicorn src.main:app --port 3001`

6. The analysis only works with open source PR and repo only

7. To get the PR analysis, replace the pr url in request body you want to analyse 
`curl --location --request POST 'http://localhost:3001/pr_analysis' \
--header 'Content-Type: application/json' \
--data-raw '{
    "url": "https://github.com/sarangBuzzyBrains/fastapi/pull/1"
}'`

8. To get the analysis of a repo, replace the repo url in request body you want to analyse
`curl --location --request POST 'http://localhost:3001/repo_analysis' \
--header 'Content-Type: application/json' \
--data-raw '{
    "url": "https://github.com/socketio/socket.io"
}'`

9. Output will be stored in `issue_data` folder in root as `user_repo_name_analysed_at.json`

10. Only support one analysis as of now
