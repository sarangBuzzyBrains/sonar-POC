### Webhook setup
1. Go to Administration > Configuration > Webhook and create a webhook
2. While running program in local use 3rd party payload delivery service, here is the example for smee
    1. Install smee `npm install --global smee-client`
    2. Then run `smee --url https://smee.io/QiUVT5eZ3x3AtnS --path /webhook --port 9001` to forward webhooks to our local development, please update the url endpoint and port according to your local setup 
![Alt text](image.png)

### Project setup

1. update the project.properties.yaml file
2. Create virtual env
`python3 -m venv venv`
3. Activate virtual env
`source venv/bin/activate `
4. Install dependencies
`pip install -r requirements.txt`
5. Run command
`uvicorn src.main:app --port 9001`

6. To get the PR analysis
`curl --location --request POST 'http://localhost:9001/pr_analysis' \
--header 'Content-Type: application/json' \
--data-raw '{
    "url": "https://github.com/sarangBuzzyBrains/fastapi/pull/1"
}'`

7. To get the analysis of a repo
`curl --location --request POST 'http://localhost:9001/repo_analysis' \
--header 'Content-Type: application/json' \
--data-raw '{
    "url": "https://github.com/socketio/socket.io"
}'`

8. Output will be stored in `issue_data` folder in root