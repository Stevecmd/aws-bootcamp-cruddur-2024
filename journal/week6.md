# Week 6 — Deploying Containers and DNS
## Implementation

This week we start to implement AWS ECS with fargate.
### RDS

Create a script to check if we can estabilish a connection with the RDS:

script: `backend-flask/bin/db/test`

```
#!/usr/bin/env python3

import psycopg
import os
import sys

connection_url = os.getenv("PROD_CONNECTION_URL")

conn = None
try:
  print('attempting connection')
  conn = psycopg.connect(connection_url)
  print("Connection successful!")
except psycopg.Error as e:
  print("Unable to connect to the database:", e)
finally:
  conn.close()

```
Change the file permissions: `chmod u+x backend-flask/bin/db/test`

#### Health-check (Backend)
Create a health check of our `backend-flask` container.
Add the following code to `app.py` and optionally comment out the rollbar test to disable it.

```
@app.route('/api/health-check')
def health_check():
  return {'success': True}, 200
```

Create a new bash script for in `bin/flask/health-check`:

```
#!/usr/bin/env python3

import urllib.request

try:
  response = urllib.request.urlopen('http://localhost:4567/api/health-check')
  if response.getcode() == 200:
    print("[OK] Flask server is running")
    exit(0) # success
  else:
    print("[BAD] Flask server is not running")
    exit(1) # false
# This for some reason is not capturing the error....
#except ConnectionRefusedError as e:
# so we'll just catch on all even though this is a bad practice
except Exception as e:
  print(e)
  exit(1) # false
```
#### Change the file permissions: `chmod u+x ./backend-flask/bin/flask/health-check` 

Cloudwatch log group. <br />
Use the following command on the terminal:
```
aws logs create-log-group --log-group-name cruddur
aws logs put-retention-policy --log-group-name cruddur --retention-in-days 1
```
or
```
aws logs create-log-group --log-group-name "/cruddur/fargate-cluster"

aws logs put-retention-policy --log-group-name "/cruddur/fargate-cluster" --retention-in-days 1
```

#### Create the container registry the images:

Create the `cruddur` cluster in cli

```
aws ecs create-cluster \
--cluster-name cruddur \
--service-connect-defaults namespace=cruddur
```

The next step is to prepare the docker configurations as shown below. <br />
We need to create 3 repo's in ECR. 
- Python, 
- backend-flask and 
- frontend-react-js

#### Create the python repo using the CLI:
```
aws ecr create-repository \
  --repository-name cruddur-python \
  --image-tag-mutability MUTABLE
```

Login to ECR using the following command **(Note this has to be done everytime you need to connect to ECR)**:
```
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"

```

Use the following command on the cli to set the url of the repo created:
```
export ECR_PYTHON_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/cruddur-python"
echo $ECR_PYTHON_URL
```

The following commands will pull the python:3.10-slim-buster, tag the image and push to ECR:
```
docker pull python:3.10-slim-buster
docker tag python:3.10-slim-buster $ECR_PYTHON_URL:3.10-slim-buster
docker push $ECR_PYTHON_URL:3.10-slim-buster
```

#### Modify dockerfile in backend-flask as below:</br>
Before:
```
FROM python:3.10-slim-buster

ENV FLASK_ENV=development
````
After:
```
FROM <repo-url>.dkr.ecr.us-east-1.amazonaws.com/cruddur-python

ENV FLASK_DEBUG=1
```
Note:
- to make sure it works, try to do Compose Up 
- to remove an image use the following code docker image `rm name:tag`
- to check the images of docker use docker images

The command to start `backend-flask` and `db` using the cli is:
```
docker compose up backend-flask db
```
Visit the backend port:**(4567)** and append `/api/health-check` to check for the response, it should return:
```sh
success: true
```
An alternative to running exposed service such as `CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]` in our Dockerfile, you can rely on 3rd party services such as [Gunicorn](https://gunicorn.org/)

#### Create the repo for the backend flask:
```
aws ecr create-repository \
  --repository-name backend-flask \
  --image-tag-mutability MUTABLE
```

Use the following command in the cli to set the url of the repo created above:
```
export ECR_BACKEND_FLASK_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/backend-flask"
echo $ECR_BACKEND_FLASK_URL
```

Build the backend-flask image(make sure you are inside the `backend-flask`)
```
docker build -t backend-flask .
```

Tag the image
```
docker tag backend-flask:latest $ECR_BACKEND_FLASK_URL:latest
```

Push the image to the repo:

```
docker push $ECR_BACKEND_FLASK_URL:latest
```
## Tip
On ECS the difference between the two items below is: <br/>
- A Task destroys itself once it has completed its purpose.
- A Service is a continuously running application and is suitable for a web app.
To create a service you need to create a task definition before-hand.

## CREATING THE CONTAINER
Pass the parameters to the CLI to initialize AWS Systems Manager (ssm) env vars: 
```
export OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=$HONEYCOMB_API_KEY"
```
Confirm:
```sh
echo $OTEL_EXPORTER_OTLP_HEADERS
```

```
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_ACCESS_KEY_ID" --value $AWS_ACCESS_KEY_ID
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_SECRET_ACCESS_KEY" --value $AWS_SECRET_ACCESS_KEY
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/CONNECTION_URL" --value $PROD_CONNECTION_URL
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/ROLLBAR_ACCESS_TOKEN" --value $ROLLBAR_ACCESS_TOKEN
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/OTEL_EXPORTER_OTLP_HEADERS" --value "x-honeycomb-team=$HONEYCOMB_API_KEY"
```


Create the required policies for the container:

Create the task role `CruddurTaskRole`:

```
aws iam create-role \
    --role-name CruddurTaskRole \
    --assume-role-policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[\"sts:AssumeRole\"],
    \"Effect\":\"Allow\",
    \"Principal\":{
      \"Service\":[\"ecs-tasks.amazonaws.com\"]
    }
  }]
}"
```

Attach the policy to allow use of Session manager:
```
aws iam put-role-policy \
  --policy-name SSMAccessPolicy \
  --role-name CruddurTaskRole \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ],
        "Effect": "Allow",
        "Resource": "*"
      }
    ]
  }'

```

#### Give access to cloudwatch to the `cruddurtaskrole`:
```
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess --role-name CruddurTaskRole
```
Attach a policy to give write access to the xraydaemon:
```
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess --role-name CruddurTaskRole
```

```sh
aws iam put-role-policy \
    --policy-name CruddurServiceExecutionPolicy \
    --role-name CruddurServiceExecutionRole \
    --policy-document file://aws/policies/service-execution-policy.json
```

from `/workspace/aws-bootcamp-cruddur-2024` run the following commands on CLI:
```sh
aws iam create-role \
    --role-name CruddurServiceExecutionPolicy \
    --assume-role-policy-document file://aws/policies/service-assume-role-execution-policy.json
```

Create the new trust entities json file under the path `aws/policies/service-assume-role-execution-policy.json`

```py
{
  "Version":"2012-10-17",
  "Statement":[{
      "Action":["sts:AssumeRole"],
      "Effect":"Allow",
      "Principal":{
        "Service":["ecs-tasks.amazonaws.com"]
    }}]
}
```

Create another json file under the path `aws/policies/service-execution-policy.json`:
```sh
{
    "Version":"2012-10-17",
    "Statement":[{
        "Action":["sts:AssumeRole"],
        "Effect":"Allow",
        "Principal":{
          "Service":["ecs-tasks.amazonaws.com"]
      }},{
        "Effect": "Allow",
        "Action": [
            "ssm:GetParameters",
            "ssm:GetParameter"
        ],
        "Resource": "arn:aws:ssm:us-east-1:652162945585:parameter/cruddur/backend-flask/*" 
      }]
}
```

```sh
aws iam put-role-policy \
    --policy-name CruddurServiceExecutionPolicy \
    --role-name CruddurServiceExecutionRole  \
    --policy-document file://aws/policies/service-execution-policy.json
```

Via console attach the following policy:
Make sure to attach `CruddurServiceExecutionRole` to  `CloudWatchFullAccess`.

We were having some trouble hence confirm the permissions as below: <br />
> CruddurServiceExecutionPolicy
```js
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameters",
                "ssm:GetParameter",
                "secretsmanager:*",
                "cloudwatch:*"
            ],
            "Resource": "arn:aws:ssm:us-east-1:652162945585:parameter/cruddur/backend-flask/*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:ssm:us-east-1:652162945585:parameter/cruddur/backend-flask/*"
        }
    ]
}

```
> CruddurServiceExecutionRole
- Attach CloudWatchFullAccess and CruddurServiceExecutionPolicy
> CruddurTaskRole
- Attach `AWSXRayDaemonWriteAccess` , `CloudWatchFullAccess`, `SSMAccessPolicy`. <br />
Trust relationship:
```js
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```
## Task definition creation via cli

Create a new file /aws/task-definitions/backend-flask.json

```py
{
  "family": "backend-flask",
  "executionRoleArn": "arn:aws:iam::<account-number>:role/CruddurServiceExecutionRole",
  "taskRoleArn": "arn:aws:iam::<account-number>:role/CruddurTaskRole",
  "networkMode": "awsvpc",
  "cpu": "256",
  "memory": "512",
  "requiresCompatibilities": [ 
    "FARGATE" 
  ],
  "containerDefinitions": [
    {
      "name": "backend-flask",
      "image": "<account-number>.dkr.ecr.us-east-1.amazonaws.com/backend-flask",
      "essential": true,
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "python /backend-flask/bin/flask/health-check"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "portMappings": [
        {
          "name": "backend-flask",
          "containerPort": 4567,
          "protocol": "tcp", 
          "appProtocol": "http"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
            "awslogs-group": "cruddur",
            "awslogs-region": "us-east-1",
            "awslogs-stream-prefix": "backend-flask"
        }
      },
      "environment": [
        {"name": "OTEL_SERVICE_NAME", "value": "backend-flask"},
        {"name": "OTEL_EXPORTER_OTLP_ENDPOINT", "value": "https://api.honeycomb.io"},
        {"name": "AWS_COGNITO_USER_POOL_ID", "value": "us-east-1_rNUe2sEXo"},
        {"name": "AWS_COGNITO_USER_POOL_CLIENT_ID", "value": "3870k3kbsr6tbkj6bltab924bp"},
        {"name": "FRONTEND_URL", "value": "*"},
        {"name": "BACKEND_URL", "value": "*"},
        {"name": "AWS_DEFAULT_REGION", "value": "us-east-1"}
      ],
      "secrets": [
        {"name": "AWS_ACCESS_KEY_ID"    , "valueFrom": "arn:aws:ssm:us-east-1:<account-number>:parameter/cruddur/backend-flask/AWS_ACCESS_KEY_ID"},
        {"name": "AWS_SECRET_ACCESS_KEY", "valueFrom": "arn:aws:ssm:us-east-1:<account-number>:parameter/cruddur/backend-flask/AWS_SECRET_ACCESS_KEY"},
        {"name": "CONNECTION_URL"       , "valueFrom": "arn:aws:ssm:us-east-1:<account-number>:parameter/cruddur/backend-flask/CONNECTION_URL" },
        {"name": "ROLLBAR_ACCESS_TOKEN" , "valueFrom": "arn:aws:ssm:us-east-1:<account-number>:parameter/cruddur/backend-flask/ROLLBAR_ACCESS_TOKEN" },
        {"name": "OTEL_EXPORTER_OTLP_HEADERS" , "valueFrom": "arn:aws:ssm:us-east-1:<account-number>:parameter/cruddur/backend-flask/OTEL_EXPORTER_OTLP_HEADERS" }
      ]
    }
  ]
}
```

Launch the services and tasks using the following commands:

```sh
aws ecs register-task-definition --cli-input-json file://aws/task-definitions/backend-flask.json
```
On the console, confirm registration at `Amazon Elastic Container Service` > `Task definitions` > `backend-flask`.
Once the container is up, we now need to create a security group for it hence the need to get the default VPC env vars then 
create the SG.

Detect the default vpc from within the `backend-flask` folder:
```sh
export DEFAULT_VPC_ID=$(aws ec2 describe-vpcs \
--filters "Name=isDefault, Values=true" \
--query "Vpcs[0].VpcId" \
--output text)
echo $DEFAULT_VPC_ID
```

Create the security group:
```py
export CRUD_SERVICE_SG=$(aws ec2 create-security-group \
  --group-name "crud-srv-sg" \
  --description "Security group for Cruddur services on ECS" \
  --vpc-id $DEFAULT_VPC_ID \
  --query "GroupId" --output text)
echo $CRUD_SERVICE_SG
```

You could also hard code the SG value if the SG already exists (replace with yours):
```sh
  export CRUD_SERVICE_SG="sg-08050161e2ec5f683"
```

```py
aws ec2 authorize-security-group-ingress \
  --group-id $CRUD_SERVICE_SG \
  --protocol tcp \
  --port 4567 \
  --cidr 0.0.0.0/0
```

Create a file called `service-backend-flask.json` under the path: `/aws/json/` and replace the value of security group and subnetmask:
```py
{
  "cluster": "cruddur",
  "launchType": "FARGATE",
  "desiredCount": 1,
  "enableECSManagedTags": true,
  "enableExecuteCommand": true,
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "assignPublicIp": "ENABLED",
      "securityGroups": [
        "TO CHANGE"
      ],
      "subnets": [
        "TO CHANGE",
        "TO CHANGE",
        "TO CHANGE"
      ]
    }
  },
  "propagateTags": "SERVICE",
  "serviceName": "backend-flask",
  "taskDefinition": "backend-flask",
  "serviceConnectConfiguration": {
    "enabled": true,
    "namespace": "cruddur",
    "services": [
      {
        "portName": "backend-flask",
        "discoveryName": "backend-flask",
        "clientAliases": [{"port": 4567}]
      }
    ]
  }
}
```
Get the Default Subnet ID's:
```sh
export DEFAULT_SUBNET_IDS=$(aws ec2 describe-subnets  \
 --filters Name=vpc-id,Values=$DEFAULT_VPC_ID \
 --query 'Subnets[*].SubnetId' \
 --output json | jq -r 'join(",")')
echo $DEFAULT_SUBNET_IDS
```
Some permissions were missing so I had to run:
```sh
aws iam attach-role-policy --role-name CruddurServiceExecutionRole --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```

Launch the command below from `aws-bootcamp-cruddur-2024` to create the new service for backend flask so that the enable `executecommand` is active (Note that this function can only activated only using the CLI)

```sh
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json
```


### Connect to the containers using the session manager tool for ubuntu

Install Session manager. here is the [reference](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html#install-plugin-linux)

```py
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
session-manager-plugin
```

connect to the service:
```sh
aws ecs execute-command  \
    --region $AWS_DEFAULT_REGION \
    --cluster cruddur \
    --task <TaskName> \
    --container backend-flask \
    --command "/bin/bash" \
    --interactive
  ```

Note: the execute command is only possible via CLI.

Add the Fargate dependency to gitpod.yml:

```py
name: fargate
    before: |
      curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
      sudo dpkg -i session-manager-plugin.deb
      cd backend-flask

```

Create the folder `ecs` on the following path:
`/backend-flask/bin/` <br/>

Create the new file `connect-to-service` with the code below and make it executable `chmod u+x bin/ecs/connect-to-service`<br />

```sh
#! /usr/bin/bash

if [ -z "$1" ]; then
    echo "No TASK_ID argument supplied eg ./bin/ecs/connect-to service 291661114f174777aeeaff30522b972d backend-flask"
    exit 1
fi
TASK_ID=$1

if [ -z "$2" ]; then
    echo "No CONTAINER_NAME argument supplied eg ./bin/ecs/connect-to service 291661114f174777aeeaff30522b972d backend-flask"
    exit 2
fi
CONTAINER_NAME=$2


aws ecs execute-command  \
    --region $AWS_DEFAULT_REGION \
    --cluster cruddur \
    --task $TASK_ID \
    --container $CONTAINER_NAME \
    --command "/bin/bash" \
    --interactive
```
Supply the task ID for backend-flask when running it.

In the CLI, we can list our tasks by running:
`aws ecs list-tasks --cluster cruddur`

For the **Frontend** repo: <br />
Create the task for **frontend-react-js**.

First create the task definitiion called **frontend-react-js.json** under `/aws/task-definition`.
```py
"family": "frontend-react-js",
    "executionRoleArn": "arn:aws:iam::<account-number>:role/CruddurServiceExecutionRole",
    "taskRoleArn": "arn:aws:iam::<account-number>:role/CruddurTaskRole",
    "networkMode": "awsvpc",
    "cpu": "256",
    "memory": "512",
    "requiresCompatibilities": [ 
      "FARGATE" 
    ],
    "containerDefinitions": [
      {
        "name": "frontend-react-js",
        "image": "number.dkr.ecr.REGION.amazonaws.com/frontend-react-js",
        "essential": true,
        "portMappings": [
          {
            "name": "frontend-react-js",
            "containerPort": 3000,
            "protocol": "tcp", 
            "appProtocol": "http"
          }
        ],
  
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
              "awslogs-group": "cruddur",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "frontend-react-js"
          }
        }
      }
    ]
  }
```


create the Dockerfile.prod in `frontend-react-js`:
```sh
# Base Image ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FROM node:16.18 AS build

ARG REACT_APP_BACKEND_URL
ARG REACT_APP_AWS_PROJECT_REGION
ARG REACT_APP_AWS_COGNITO_REGION
ARG REACT_APP_AWS_USER_POOLS_ID
ARG REACT_APP_CLIENT_ID

ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV REACT_APP_AWS_PROJECT_REGION=$REACT_APP_AWS_PROJECT_REGION
ENV REACT_APP_AWS_COGNITO_REGION=$REACT_APP_AWS_COGNITO_REGION
ENV REACT_APP_AWS_USER_POOLS_ID=$REACT_APP_AWS_USER_POOLS_ID
ENV REACT_APP_CLIENT_ID=$REACT_APP_CLIENT_ID

COPY . ./frontend-react-js
WORKDIR /frontend-react-js
RUN npm install
RUN npm run build

# New Base Image ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FROM nginx:1.23.3-alpine

# --from build is coming from the Base Image
COPY --from=build /frontend-react-js/build /usr/share/nginx/html
COPY --from=build /frontend-react-js/nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000
```

Create the file `nginx.conf` under `frontend-react-js`: <br />
**NB:** Only run one container per process. <br />
```py
# Set the worker processes
worker_processes 1;

# Set the events module
events {
  worker_connections 1024;
}

# Set the http module
http {
  # Set the MIME types
  include /etc/nginx/mime.types;
  default_type application/octet-stream;

  # Set the log format
  log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

  # Set the access log
  access_log  /var/log/nginx/access.log main;

  # Set the error log
  error_log /var/log/nginx/error.log;

  # Set the server section
  server {
    # Set the listen port
    listen 3000;

    # Set the root directory for the app
    root /usr/share/nginx/html;

    # Set the default file to serve
    index index.html;

    location / {
        # First attempt to serve request as file, then
        # as directory, then fall back to redirecting to index.html
        try_files $uri $uri/ $uri.html /index.html;
    }

    # Set the error page
    error_page  404 /404.html;
    location = /404.html {
      internal;
    }

    # Set the error page for 500 errors
    error_page  500 502 503 504  /50x.html;
    location = /50x.html {
      internal;
    }
  }
}
```
In the `.git-ignore` file add the entry to ignore the frontend build:
```py
frontend-react-js/build/*
```

from the folder `frontend-react-js` run the command to build:

```sh
npm run build
```

Build the image pointing to the local env using the commands below: 

```sh
docker build \
--build-arg REACT_APP_BACKEND_URL="https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="$AWS_USER_POOLS_ID" \
--build-arg REACT_APP_CLIENT_ID="$APP_CLIENT_ID" \
-t frontend-react-js \
-f Dockerfile.prod \
.
```

If you have a Load balancer in place you can point to the url of the load balancer:
```sh
docker build \
--build-arg REACT_APP_BACKEND_URL="http://cruddur-alb-1044769460.us-east-1.elb.amazonaws.com:4567" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="$AWS_USER_POOLS_ID" \
--build-arg REACT_APP_CLIENT_ID="$APP_CLIENT_ID" \
-t frontend-react-js \
-f Dockerfile.prod \
.
```

Create the repo for the frontend ECR:

```sh
aws ecr create-repository \
  --repository-name frontend-react-js \
  --image-tag-mutability MUTABLE
```

Set the env var:

```sh
export ECR_FRONTEND_REACT_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/frontend-react-js"
echo $ECR_FRONTEND_REACT_URL
```

Tag the image:
```sh
docker tag frontend-react-js:latest $ECR_FRONTEND_REACT_URL:latest
echo $ECR_FRONTEND_REACT_URL
```

Test locally:
```sh
docker run --rm -p 3000:3000 -it frontend-react-js 

```

Push the repo to ecr:
```
docker push $ECR_FRONTEND_REACT_URL:latest
```

Create the `task definition` for the frontend-react-js in `aws` > `task-definitions` > `frontend-react-js.json`

```py
{
    "family": "frontend-react-js",
    "executionRoleArn": "arn:aws:iam::<account-number>:role/CruddurServiceExecutionRole",
    "taskRoleArn": "arn:aws:iam::<account-number>:role/CruddurTaskRole",
    "networkMode": "awsvpc",
    "cpu": "256",
    "memory": "512",
    "requiresCompatibilities": [ 
      "FARGATE" 
    ],
    "containerDefinitions": [
      {
        "name": "frontend-react-js",
        "image": "<account-number>.dkr.ecr.us-east-1.amazonaws.com/frontend-react-jss",
        "essential": true,
        "portMappings": [
          {
            "name": "frontend-react-js",
            "containerPort": 3000,
            "protocol": "tcp", 
            "appProtocol": "http"
          }
        ],
  
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
              "awslogs-group": "cruddur",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "frontend-react-js"
          }
        }
      }
    ]
  }
```

Create the service `service-frontend-react-js.json` in `aws` > `json`:
**We are launching it without a load balancer so that we can shell into it and inspect it.**
```
{
    "cluster": "cruddur",
    "launchType": "FARGATE",
    "desiredCount": 1,
    "enableECSManagedTags": true,
    "enableExecuteCommand": true,
    "networkConfiguration": {
      "awsvpcConfiguration": {
        "assignPublicIp": "ENABLED",
        "securityGroups": [
            "sg-08050161e2ec5f683"
          ],
          "subnets": [
            "<subnet-name>",
            "<subnet-name>",
            "<subnet-name>"
          ]
      }
    },
    "propagateTags": "SERVICE",
    "serviceName": "frontend-react-js",
    "taskDefinition": "frontend-react-js",
    "serviceConnectConfiguration": {
      "enabled": true,
      "namespace": "cruddur",
      "services": [
        {
          "portName": "frontend-react-js",
          "discoveryName": "frontend-react-js",
          "clientAliases": [{"port": 3000}]
        }
      ]
    }
  }
```

Invoke the creation of the services in frontend-react-js using the following command:

```sh
aws ecs create-service --cli-input-json file://aws/json/service-frontend-react-js.json
```

Launch the task definition for the `front end`:

```
aws ecs register-task-definition --cli-input-json file://aws/task-definitions/frontend-react-js.json
```

If you encounter a problem with the frontend image, build the image locally (pointing to the local env), within the folder `frontend-react-js` and build it locally then run it:
```sh
docker build \
--build-arg REACT_APP_BACKEND_URL="https://4567-$GITPOD_WORKSPACE_ID.$GITPOD_WORKSPACE_CLUSTER_HOST" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="$AWS_USER_POOLS_ID" \
--build-arg REACT_APP_CLIENT_ID="$APP_CLIENT_ID" \
-t frontend-react-js \
-f Dockerfile.prod \
.
```
Run the container:
```sh
docker run --rm -p 3000:3000 -dt frontend-react-js
```
Find the container ID and inspect it:
```
docker ps

docker inspect <docker-container-number>
```
Once done, redeploy it to ECS by refistering the task definition and restarting the service. <br />
Note that by default bash is not included with busybox and alpine linux.
**Bash and sh are not the same** <br />

To shell into the container run the code below and input the containers number as a parameter: <br />
```sh
./bin/ecs/connect-to-service <container-number eg 46e57sd8sd94ds1dsd575gh> frontend-react-js
```
Insert this **health check** in `frontend-react-js-json` under `aws > task-definitions`:
```py
"healthCheck": {
          "command": [
            "CMD-SHELL",
            "curl -f http://localhost:3000 || exit 1"
          ],
          "interval": 30,
          "timeout": 5,
          "retries": 3
        },
```

### Service Connect
We can also enable service connect by adding the following code to `service-backend-flask.json`:
```py
    "serviceConnectConfiguration": {
      "enabled": true,
      "namespace": "cruddur",
      "services": [
        {
          "portName": "backend-flask",
          "discoveryName": "backend-flask",
          "clientAliases": [{"port": 4567}]
        }
      ]
    },
    "propagateTags": "SERVICE",
```

Do the same for the frontend `service-frontend-react-js.json`:
```py
    },
    "propagateTags": "SERVICE",
    "serviceName": "frontend-react-js",
    "taskDefinition": "frontend-react-js",
    "serviceConnectConfiguration": {
      "enabled": true,
      "namespace": "cruddur",
      "services": [
        {
          "portName": "frontend-react-js",
          "discoveryName": "frontend-react-js",
          "clientAliases": [{"port": 3000}]
        }
      ]
    }
  }
```
**Application Load Balancer** <br />
Create a new Security group:
- Name: `cruddur-alb-sg`
- Description: `cruddur-alb-sg`
- Inbound rules: HTTP and HTTPS from anywhere.
- Outbound rules: Anywhere IPv4 and/or IPv6
  Once created note the security group ID.

#### Modify original SG.
The original Security group allowed traffic to your Gitpod IP address on port 4567, we can now add a setting and allow 
traffic to our security group that we just created, port 4567 as well, description: Cruddur ALB. <br />
**You may delete the previous rule as it is not necessary anymore.**

### Create a Target Groups
Frontend TG <br />
- Target: `IP Addresses`
- Target group name: `cruddur-frontend-react-js-tg`
- Protocol: `HTTP` : Port `3000`
- IP address type: `IPv4`
- VPC - 'default VPC'
- Health-check: None
- Healthy threshold: `3`
- Interval: '30'
- Skip `Register targets` and Create.

Backend TG <br />
- Target: `IP Addresses`
- Target group name: `cruddur-backend-flask-tg`
- Protocol: `HTTP` : Port `4567`
- IP address type: `IPv4`
- VPC - 'default VPC'
- Health-check: `/api/health-check`
- Healthy threshold: `3`
- Interval: '30'
- Skip `Register targets` and Create.

  On the console create an **Application Load Balancer**.
- Load balancer name: `cruddur-alb`
- Internet facing
- IPv4
- VPC: <select your VPC(default)>
- Subnets (select atleast 2)
- Security group: SG we just created. `cruddur-alb-sg` **remove the default one**.
- Listener: HTTP: `4567`
- Default action: `cruddur-backend-flask-tg`
- Add a listener on port `3000`.
- Target: `cruddur-frontend-react-js-tg`
- Tags: Name: `Cruddur TG`
- **Create Load Balancer**

Allow communication between the ALB and the target group. 
**Solution:** Ensure that the security group allows incoming connections on port 3000.

Confirm that RDS is running then confirm access to RDS, in `backend-flask` run:
```sh
./bin/db/test
```
It may fail due to the Security group not having the correct permissions, update them by running:
```
./bin/db/rds/update-sg-rule
```
**NB** - The CLI can provide a template to create various services eg:
```sh
aws ecs create-service --generate-cli-skeleton
```
Create a `load balancer` to control traffic to the containers:

Add the following code to `service-backend-flask.json` and `service-frontend-react-js.json` and fill in the details: <br />
```py
"loadBalancers": [
      {
          "targetGroupArn": "",
          "containerName": "",
          "containerPort": 0
      }
    ],
```
Details: <br />
`backend`
- targetGroupArn - "`arn:aws:elasticloadbalancing:<input backend TG arn>`"
- containerName - "`backend-flask` ",
- `containerPort` - 4567

`frontend`
- targetGroupArn - "`arn:aws:elasticloadbalancing:<input frontend TG arn>`"
- containerName - "`frontend-react-js` ",
- `containerPort` - 3000

Get the Load balancer DNS name and rebuild the container while in the `frontend-react-js` directory:

```sh
docker build \
--build-arg REACT_APP_BACKEND_URL="http://cruddur-alb-<account-number>.<region>.elb.amazonaws:4567" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="$AWS_USER_POOLS_ID" \
--build-arg REACT_APP_CLIENT_ID="$APP_CLIENT_ID" \
-t frontend-react-js \
-f Dockerfile.prod \
.
```
Tag the Image and push it:
```
docker tag frontend-react-js-prod:latest $ECR_FRONTEND_REACT_URL:latest
docker push $ECR_FRONTEND_REACT_URL:latest
```
Stop and Delete any previously running containers on ECS. <br />
From `aws-bootcamp-cruddur-2024` <br />
Create new Task definitions: <br />
Frontend: <br />
```
aws ecs register-task-definition --cli-input-json file://aws/task-definitions/frontend-react-js.json
```
Backend: <br />
```sh
aws ecs register-task-definition --cli-input-json file://aws/task-definitions/backend-flask.json
```

Redeploy the services: <br />
```sh
aws ecs create-service --cli-input-json file://aws/json/service-frontend-react-js.json
```
```sh
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json
```
If it fails, go to the security group `cruddur-alb-sg` and create a temporary rule that allows coonections from anywhere on ports `4567` and `3000`. They can be named `TMP1` and `TMP2`. <br />
Confirm Load balancer and ECS are online, <br />
Visit the ECS public port and append `:4567/api/health-check`. <br />
- It should return `success`.
Similarly, you should be able to visit the other routes:
```txt
<load balancer DNS Name>:4567/api/activities/home
<load balancer DNS Name>:4567/api/activities/notifications
<load balancer DNS Name>:4567/api/activities/messages
<load balancer DNS Name>:4567/api/activities/message_group
```
**Extra** <br />
To enable cloudwatch logs on the Load balancer via the console: <br />
- Create a new S3 Bucket eg `cruddur-alb-access-logs-2024`, same region as the `Load Balancer`, 
Uncheck `Block all public access`.
Check `Block the ACL permissions`.
Once created, go to `Permissions` and upload an access policy that will allow cloudwatch logs access to the ALB as per your region.
Encryption: `Amazon S3 Managed Keys(SSE-S3)`
- From the ALB page, go to `Attributes` > `Edit` > Enable `Access Logs` (Incurs cost)
- Select the S3 bucket created: `s3://cruddur-alb-access-logs-2024`
- Create
- It might fail and this has to do with creating the appropriate bucket policy as per your region and referencing the correct ALB account as provided by the docs. <br />
Refer to `https://docs.aws.amazon.com/general/latest/gr/elb.html` <br />
Confirm the front-end task definion is okay. `aws` > `task-definitions` > `frontend-react-js.json`. <br />
Create Production Dockerfile. <br />
Refer to: <br />
1. [Monitor your Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-monitoring.html) <br />
2. [CloudWatch metrics for your Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html) 
3. [Monitoring load balancers using Amazon CloudWatch anomaly detection alarms](https://aws.amazon.com/blogs/networking-and-content-delivery/monitoring-load-balancers-using-amazon-cloudwatch-anomaly-detection-alarms/) 
4. [CloudWatch metrics for your Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html#load-balancer-metric-table)



# Implementation of the SSL and configuration of Domain from Route53

Create the hosted zone for your domain.
Once created, take note of the "Value/route traffic". it should be something like this:
```txt
ns-207.awsdns-25.com.
ns-1481.awsdns-57.org.
ns-1728.awsdns-24.co.uk.
ns-595.awsdns-10.net.
```

On route53 under domains > registered domain > name servers (above the DNSSEC status): <br /> 
Check if info is the same as that of the values in the "Value/route traffic".

To create a SSL/TLS certificate go to AWS Certificate Manager.
Go to request and select "Request a public certificate".
Under "fully qualified domain name" insert your domain. for example:
```example.com or
*.example.com```
As a validation method, select "DNS validation - reccommended" and as key algorithm select `RSA 2048`.
Once you have created the certificate request, on route 53, go to the certificate request > create records.

Note: it takes a few minutes to have the status changed from "pending validation" to "issued".

Once you have the certificate, Modify route53 alb and task definition and redeploy the images for the backend and frontend to ECR.

On the hosted zone previously created, create 2 new records.

Select as a record type "CNAME - routes traffic to another domain name and to some aws resource", toggle alias on and select the endpoint and region. The routing policy should be "simple routing".

Repeat for any subdomains eg `api.domain.co.uk` with the same configuration above.

In the task definition of the backend, edit the following lines:
```sh
   {"name": "FRONTEND_URL", "value": "https://example.co.uk"},
   {"name": "BACKEND_URL", "value": "https://api.example.co.uk"},
```

Once you, relaunch the task definition and recreate the image of the frontend and push it. 


```sh
docker build \
--build-arg REACT_APP_BACKEND_URL="https://example.com" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="$AWS_USER_POOLS_ID" \
--build-arg REACT_APP_CLIENT_ID="$APP_CLIENT_ID" \
-t frontend-react-js \
-f Dockerfile.prod \
.
```

Note: make sure to open the SG of the container backend flask from the SG of the RDS for the port 5432 otherwise you wont be able to use the test script to check the RDS from the container backendflask in ECS.
I had to do some debugging to remove errors and get all the endpoints to work, this is evdienced by the commit: <br />
[Debugging updates](https://github.com/Stevecmd/aws-bootcamp-cruddur-2024/commit/d75da25fc5794f75a84178f1c0fea1de465d5a2d) <br />
Alternatively you could check the branch:
[Debugging](https://github.com/Stevecmd/aws-bootcamp-cruddur-2024/tree/Debugging)

# Securing Backend flask

In this part of implementation, we need to create 2 docker files. 

1. `Dockerfile` with the following code which the debugging on:
```sh
FROM <account-number>.dkr.ecr.us-east-1.amazonaws.com/cruddur-python:3.10-slim-buster

WORKDIR /backend-flask

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE ${PORT}
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567", "--debug"]
```

the other file called Dockerfile.prod with the following code which does not debugging enabled.

```sh
FROM <account-number>.dkr.ecr.us-east-1.amazonaws.com/cruddur-python:3.10-slim-buster

WORKDIR /backend-flask

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .


EXPOSE ${PORT}

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567", "--no-debug", "--no-debugger", "--no-reload"]

```

Make sure to test the docker production changes before pushing the image to the ECR repo.
In this case run `docker compose up` using the dockerfile rather than deploying the build and run process.

Below are the scripts for the building the repo's: <br /> 
**backend**:

```
#! /usr/bin/bash

ABS_PATH=$(readlink -f "$0")
BUILD_PATH=$(dirname $ABS_PATH)
DOCKER_PATH=$(dirname $BUILD_PATH)
BIN_PATH=$(dirname $DOCKER_PATH)
PROJECT_PATH=$(dirname $BIN_PATH)
BACKEND_FLASK_PATH="$PROJECT_PATH/backend-flask"

docker build \
-f "$BACKEND_FLASK_PATH/Dockerfile.prod" \
-t backend-flask-prod \
"$BACKEND_FLASK_PATH/."
```
Note that the REACT_APP_BACKEND_URL should point to your domain instead to your gitpod/codespace. <br />
**frontend** <br />
```
#! /usr/bin/bash

docker build \
--build-arg REACT_APP_BACKEND_URL="https://4567-$GITPOD_WORKSPACE_ID.$GITPOD_WORKSPACE_CLUSTER_HOST" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="$AWS_USER_POOLS_ID" \
--build-arg REACT_APP_CLIENT_ID="$APP_CLIENT_ID" \
-t frontend-react-js \
-f Dockerfile.prod \
.
```

and the script to run the backend image: 
```
#! /usr/bin/bash

docker run --rm \
-p 4567:4567 \
--env AWS_ENDPOINT_URL="http://dynamodb-local:8000" \
--env CONNECTION_URL="postgresql://postgres:password@db:5432/cruddur" \
--env FRONTEND_URL="https://3000-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}" \
--env BACKEND_URL="https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}" \
--env OTEL_SERVICE_NAME='backend-flask' \
--env OTEL_EXPORTER_OTLP_ENDPOINT="https://api.honeycomb.io" \
--env OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=${HONEYCOMB_API_KEY}" \
--env AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION}" \
--env AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
--env AWS_XRAY_URL="*4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}*" \
--env AWS_XRAY_DAEMON_ADDRESS="xray-daemon:2000" \
--env AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
--env ROLLBAR_ACCESS_TOKEN="${ROLLBAR_ACCESS_TOKEN}" \
--env AWS_COGNITO_USER_POOL_ID="${AWS_USER_POOLS_ID}" \
--env AWS_COGNITO_USER_POOL_CLIENT_ID="${APP_CLIENT_ID}" \
-it backend-flask-prod
```

Push the image to ecr. 
Create a script under `/backend-flask/bin/docker/push/backend-flask-prod`

```
#! /usr/bin/bash


ECR_BACKEND_FLASK_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/backend-flask"
echo $ECR_BACKEND_FLASK_URL

docker tag backend-flask-prod:latest $ECR_BACKEND_FLASK_URL:latest
docker push $ECR_BACKEND_FLASK_URL:latest

```

Create a script under `./bin/docker/push/frontend-react-js-prod`
```sh
#! /usr/bin/bash


ECR_FRONTEND_REACT_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/frontend-react-js"
echo $ECR_FRONTEND_REACT_URL

docker tag frontend-react-js-prod:latest $ECR_FRONTEND_REACT_URL:latest
docker push $ECR_FRONTEND_REACT_URL:latest
```

Script to simplify the deployment of the ecs backend-flask.
This file is under `/bin/ecs/force-deploy-backend-flask`

```py
#! /usr/bin/bash

CLUSTER_NAME="cruddur"
SERVICE_NAME="backend-flask"
TASK_DEFINTION_FAMILY="backend-flask"


LATEST_TASK_DEFINITION_ARN=$(aws ecs describe-task-definition \
--task-definition $TASK_DEFINTION_FAMILY \
--query 'taskDefinition.taskDefinitionArn' \
--output text)

echo "TASK DEF ARN:"
echo $LATEST_TASK_DEFINITION_ARN

aws ecs update-service \
--cluster $CLUSTER_NAME \
--service $SERVICE_NAME \
--task-definition $LATEST_TASK_DEFINITION_ARN \
--force-new-deployment

#aws ecs describe-services \
#--cluster $CLUSTER_NAME \
#--service $SERVICE_NAME \
#--query 'services[0].deployments' \
#--output table
```

Create the absolute path using the following configuration for the scripts in `/backend-flask/bin`.
```
ABS_PATH=$(readlink -f "$0")
BUILD_PATH=$(dirname $ABS_PATH)
DOCKER_PATH=$(dirname $BUILD_PATH)
BIN_PATH=$(dirname $DOCKER_PATH)
PROJECT_PATH=$(dirname $BIN_PATH)
echo $PROJECT_PATH

```
the files affected are
/db/schema-load
/db/seed
/db/setup
/docker/build/backend-flask-prod
/docker/build/frontend-react-js-prod

The location of the ./backend-flask/bin has been moved to the previous folder apart from the ./flask/health-check

For any changes of the backend or frontend, build, tag, push and force the redeployment.

# Fixing the Check Auth Token
As you may already know, at the moment the token wont update.
To do this replace the checkAuth.js with the following code

```
import { Auth } from 'aws-amplify';
import { resolvePath } from 'react-router-dom';

export async function getAccessToken(){
  Auth.currentSession()
  .then((cognito_user_session) => {
    const access_token = cognito_user_session.accessToken.jwtToken
    localStorage.setItem("access_token", access_token)
  })
  .catch((err) => console.log(err));
}

export async function checkAuth(setUser){
  Auth.currentAuthenticatedUser({
    // Optional, By default is false. 
    // If set to true, this call will send a 
    // request to Cognito to get the latest user data
    bypassCache: false 
  })
  .then((cognito_user) => {
    setUser({
      cognito_user_uuid: cognito_user.attributes.sub,
      display_name: cognito_user.attributes.name,
      handle: cognito_user.attributes.preferred_username
    })
    return Auth.currentSession()
  }).then((cognito_user_session) => {
      localStorage.setItem("access_token", cognito_user_session.accessToken.jwtToken)
  })
  .catch((err) => console.log(err));
};
```

Replace and add the following code for the respective files:
- rontend-react-js/src/components/MessageForm.js  (the first line of code)
- frontend-react-js/src/pages/HomeFeedPage.js   (the first line of code)
- frontend-react-js/src/pages/MessageGroupNewPage.js   (the first line of code)
- frontend-react-js/src/pages/MessageGroupPage.js   (the first line of code)
- frontend-react-js/src/components/MessageForm.js   (the second line of code)

```
import {checkAuth, getAccessToken} from '../lib/CheckAuth';

import {getAccessToken} from '../lib/CheckAuth';
```


```py
  await getAccessToken()
  const access_token = localStorage.getItem("access_token")
```


```
Authorization': `Bearer ${access_token}`
```

## Implementation of Xray on ECS and Container Insights.

On our task definitions for both backend and frontend, add the following part to invoke `aws xray`:
```
{
      "name": "xray",
      "image": "public.ecr.aws/xray/aws-xray-daemon" ,
      "essential": true,
      "user": "1337",
      "portMappings": [
        {
          "name": "xray",
          "containerPort": 2000,
          "protocol": "udp"
        }
      ]
    },
```

Create the new task definition:
in the folder `aws-bootcamp-cruddur-2023/bin/backend` create a file called `register`:
```sh
#! /usr/bin/bash

ABS_PATH=$(readlink -f "$0")
FRONTEND_PATH=$(dirname $ABS_PATH)
BIN_PATH=$(dirname $FRONTEND_PATH)
PROJECT_PATH=$(dirname $BIN_PATH)
TASK_DEF_PATH="$PROJECT_PATH/aws/task-definitions/backend-flask.json"

echo $TASK_DEF_PATH

aws ecs register-task-definition \
--cli-input-json "file://$TASK_DEF_PATH"
```

Repeat in frontend. <br />
In the folder `aws-bootcamp-cruddur-2024/bin/frontend` create a file `register`.

```sh
#! /usr/bin/bash

ABS_PATH=$(readlink -f "$0")
BACKEND_PATH=$(dirname $ABS_PATH)
BIN_PATH=$(dirname $BACKEND_PATH)
PROJECT_PATH=$(dirname $BIN_PATH)
TASK_DEF_PATH="$PROJECT_PATH/aws/task-definitions/frontend-react-js.json"

echo $TASK_DEF_PATH

aws ecs register-task-definition \
--cli-input-json "file://$TASK_DEF_PATH"
```

In the folder `aws-bootcamp-cruddur-2024/bin/backend` create the file `run`.
```sh
#! /usr/bin/bash

ABS_PATH=$(readlink -f "$0")
BACKEND_PATH=$(dirname $ABS_PATH)
BIN_PATH=$(dirname $BACKEND_PATH)
PROJECT_PATH=$(dirname $BIN_PATH)
ENVFILE_PATH="$PROJECT_PATH/backend-flask.env"

docker run --rm \
--env-file $ENVFILE_PATH \
--network cruddur-net \
--publish 4567:4567 \
-it backend-flask-prod

```
NOTE:
add the  /bin/bash after the -it backend-flask-prod if you want to shell into the contianer. <br />

In the folder `aws-bootcamp-cruddur-2023/bin/frontend` create the file `run`.
```sh
#! /usr/bin/bash

ABS_PATH=$(readlink -f "$0")
FRONTEND_PATH=$(dirname $ABS_PATH)
BIN_PATH=$(dirname $FRONTEND_PATH)
PROJECT_PATH=$(dirname $BIN_PATH)
ENVFILE_PATH="$PROJECT_PATH/frontend-react-js.env"

docker run --rm \
--env-file $ENVFILE_PATH \
--network cruddur-net \
--publish 3000:3000 \
-it frontend-react-js-prod

```

Change the code in docker-compose-gitpod.yml of the backend

```
environment:
      AWS_ENDPOINT_URL: "http://dynamodb-local:8000"
      #CONNECTION_URL: "${PROD_CONNECTION_URL}"
      CONNECTION_URL: "postgresql://postgres:password@db:5432/cruddur"
      #FRONTEND_URL: "https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
      #BACKEND_URL: "https://${CODESPACE_NAME}-4567.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
      FRONTEND_URL: "https://3000-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
      BACKEND_URL: "https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
      OTEL_SERVICE_NAME: 'backend-flask'
      OTEL_EXPORTER_OTLP_ENDPOINT: "https://api.honeycomb.io"
      OTEL_EXPORTER_OTLP_HEADERS: "x-honeycomb-team=${HONEYCOMB_API_KEY}"
      AWS_DEFAULT_REGION: "${AWS_DEFAULT_REGION}"
      AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
      AWS_XRAY_URL: "*4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}*"
      #AWS_XRAY_URL: "*${CODESPACE_NAME}-4567.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}*"
      AWS_XRAY_DAEMON_ADDRESS: "xray-daemon:2000"
      AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
      ROLLBAR_ACCESS_TOKEN: "${ROLLBAR_ACCESS_TOKEN}"
      #env var for jwttoken
      AWS_COGNITO_USER_POOL_ID: "${AWS_USER_POOLS_ID}"
      AWS_COGNITO_USER_POOL_CLIENT_ID: "${APP_CLIENT_ID}"
```

with the following code:
```
  env_file:
      - backend-flask.env
```

Repeat for the `frontend`:

```sh
environment:
      REACT_APP_BACKEND_URL: "https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
      #REACT_APP_BACKEND_URL: "https://${CODESPACE_NAME}-4567.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
      REACT_APP_AWS_PROJECT_REGION: "${AWS_DEFAULT_REGION}"
      #REACT_APP_AWS_COGNITO_IDENTITY_POOL_ID: ""
      REACT_APP_AWS_COGNITO_REGION: "${AWS_DEFAULT_REGION}"
      REACT_APP_AWS_USER_POOLS_ID: "${AWS_USER_POOLS_ID}"
      REACT_APP_CLIENT_ID: "${APP_CLIENT_ID}"
```

with the following code

```sh
  env_file:
      - frontend-react-js.env
```

Since the file env does not pass the value of the env var, there is additional configuration that needs to be done. <br />

Create the file `generate-env-gitpod` under the `aws-bootcamp-cruddur-2024/bin/backend`

and paste the following code:
```sh
#! /usr/bin/env ruby

require 'erb'

template = File.read 'erb/backend-flask-gitpod.env.erb'
content = ERB.new(template).result(binding)
filename = "backend-flask.env"
File.write(filename, content)

```

Create a file `generate-env-gitpod` under the `aws-bootcamp-cruddur-2024/bin/frontend`:
```py
#! /usr/bin/env ruby

require 'erb'

template = File.read 'erb/frontend-react-js-gitpod.env.erb'
content = ERB.new(template).result(binding)
filename = "frontend-react-js.env"
File.write(filename, content)

```

Create  a folder `erb` and create the following file `backend-flask-gitpod.env.erb` in it:
```sh
AWS_ENDPOINT_URL=http://dynamodb-local:8000
CONNECTION_URL=postgresql://postgres:password@db:5432/cruddur
FRONTEND_URL=https://3000-<%= ENV['GITPOD_WORKSPACE_ID'] %>.<%= ENV['GITPOD_WORKSPACE_CLUSTER_HOST'] %>
BACKEND_URL=https://4567-<%= ENV['GITPOD_WORKSPACE_ID'] %>.<%= ENV['GITPOD_WORKSPACE_CLUSTER_HOST'] %>
OTEL_SERVICE_NAME=backend-flask
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io
OTEL_EXPORTER_OTLP_HEADERS=x-honeycomb-team=<%= ENV['HONEYCOMB_API_KEY'] %>
AWS_XRAY_URL=*4567-<%= ENV['GITPOD_WORKSPACE_ID'] %>.<%= ENV['GITPOD_WORKSPACE_CLUSTER_HOST'] %>*
AWS_XRAY_DAEMON_ADDRESS=xray-daemon:2000
AWS_DEFAULT_REGION=<%= ENV['AWS_DEFAULT_REGION'] %>
AWS_ACCESS_KEY_ID=<%= ENV['AWS_ACCESS_KEY_ID'] %>
AWS_SECRET_ACCESS_KEY=<%= ENV['AWS_SECRET_ACCESS_KEY'] %>
ROLLBAR_ACCESS_TOKEN=<%= ENV['ROLLBAR_ACCESS_TOKEN'] %>
AWS_COGNITO_USER_POOL_ID=<%= ENV['AWS_USER_POOLS_ID'] %>
AWS_COGNITO_USER_POOL_CLIENT_ID=<%= ENV['APP_CLIENT_ID'] %>

```

In the folder `erb` and create the file `frontend-react-js-gitpod.env.erb`: 

```sh
REACT_APP_BACKEND_URL=https://4567-<%= ENV['GITPOD_WORKSPACE_ID'] %>.<%= ENV['GITPOD_WORKSPACE_CLUSTER_HOST'] %>
REACT_APP_AWS_PROJECT_REGION=<%= ENV['AWS_DEFAULT_REGION'] %>
REACT_APP_AWS_COGNITO_REGION=<%= ENV['AWS_DEFAULT_REGION'] %>
REACT_APP_AWS_USER_POOLS_ID=<%= ENV['AWS_USER_POOLS_ID'] %>
REACT_APP_CLIENT_ID=<%= ENV['APP_CLIENT_ID'] %>
```

In `gitpod.yml` add the scripts to create the `env vars` necessary for the backend and frontend containers.
```
  source  "$THEIA_WORKSPACE_ROOT/bin/backend/generate-env-gitpod"
  source  "$THEIA_WORKSPACE_ROOT/bin/frontend/generate-env-gitpod
```


Link all the containers to connect to a specific network. <br />
Change the configuration of your `docker-compose.yml`: <br />
From:
```py
networks: 
  internal-network:
    driver: bridge
    name: cruddur
```
to:

```py
networks: 
  cruddur-net:
    driver: bridge
    name: cruddur-net
```

For each of services, make sure to attach the `cruddur-net` network by adding the following code:
```py
  networks:
      - cruddur-net
```

To troublshoot, use a `busy box`.
Create a file under `aws-bootcamp-cruddur-2024/bin` called `busybox`:
```sh
#! /usr/bin/bash

docker run --rm \
  --network cruddur-net \
  -p 4567:4567 \
  -it busybox
```

We can also  add some tools such as `ping` in the `dockerfile.prod`
after the url of the image for `debugging`:

```sh
RUN apt-get update -y
RUN apt-get install iputils-ping -y
```
# Enable Container Insights

To enable this function, go to the `cluster` and click on `update cluster`.

Under the section `Monitoring`, toggle on `Use Container Insights`.

# Implementation Time Zone

from `ddb/seed` change the following line of code: <br />
From:
```
now = datetime.now(timezone.utc).astimezone()
```

To: <br />

```
now = datetime.now()
```
In the same file, change: <br />
From: 
```
  created_at = (now + timedelta(hours=-3) + timedelta(minutes=i)).isoformat()
```
To: <br />

```
  created_at = (now - timedelta(days=1) + timedelta(minutes=i)).isoformat()
```

In `ddb.py` change the following code:
From:
```
 now = datetime.now(timezone.utc).astimezone().isoformat()
created_at = now
```

To: <br />
```
created_at = datetime.now().isoformat()

```

In `frontend-react-js/src/lib/` create a file called `DateTimeFormats.js` with the following code:
```py
import { DateTime } from 'luxon';

export function format_datetime(value) {
  const datetime = DateTime.fromISO(value, { zone: 'utc' })
  const local_datetime = datetime.setZone(Intl.DateTimeFormat().resolvedOptions().timeZone);
  return local_datetime.toLocaleString(DateTime.DATETIME_FULL)
}

export function message_time_ago(value){
  const datetime = DateTime.fromISO(value, { zone: 'utc' })
  const created = datetime.setZone(Intl.DateTimeFormat().resolvedOptions().timeZone);
  const now     = DateTime.now()
  console.log('message_time_group',created,now)
  const diff_mins = now.diff(created, 'minutes').toObject().minutes;
  const diff_hours = now.diff(created, 'hours').toObject().hours;

  if (diff_hours > 24.0){
    return created.toFormat("LLL L");
  } else if (diff_hours < 24.0 && diff_hours > 1.0) {
    return `${Math.floor(diff_hours)}h`;
  } else if (diff_hours < 1.0) {
    return `${Math.round(diff_mins)}m`;
  } else {
    console.log('dd', diff_mins,diff_hours)
    return 'unknown'
  }
}

export function time_ago(value){
  const datetime = DateTime.fromISO(value, { zone: 'utc' })
  const future = datetime.setZone(Intl.DateTimeFormat().resolvedOptions().timeZone);
  const now     = DateTime.now()
  const diff_mins = now.diff(future, 'minutes').toObject().minutes;
  const diff_hours = now.diff(future, 'hours').toObject().hours;
  const diff_days = now.diff(future, 'days').toObject().days;

  if (diff_hours > 24.0){
    return `${Math.floor(diff_days)}d`;
  } else if (diff_hours < 24.0 && diff_hours > 1.0) {
    return `${Math.floor(diff_hours)}h`;
  } else if (diff_hours < 1.0) {
    return `${Math.round(diff_mins)}m`;
  }
}
```

 do some modifications for the following files: <br />
 - In `RecoverPage.js` and `ConfirmationPage.js` change `setCognitoErrors` to `setErrors`
 - `messageitem.js`

remove the following code:
```py
import { DateTime } from 'luxon';
```

and replace with:

```py
import { format_datetime, message_time_ago } from '../lib/DateTimeFormats';
```

Repeat for the following code:
From:
```
<div className="created_at" title={props.message.created_at}>
<span className='ago'>{format_time_created_at(props.message.created_at)}</span> 
```

To:
```
  <div className="created_at" title={format_datetime(props.message.created_at)}>
  <span className='ago'>{message_time_ago(props.message.created_at)}</span> 
```

Replace:
```
<Link className='message_item' to={`/messages/@`+props.message.handle}>
<div className='message_avatar'></div>
```

With:
```
 <div className='message_item'>
      <Link className='message_avatar' to={`/messages/@`+props.message.handle}></Link>
```

and do remove the following
```sh
 </Link>
```
with
```
 </div>
```

from the `messageitem.css` make the following changes:

move portion of the code:
```
 cursor: pointer;
text-decoration: none;
```

add  the following code:
```sh

.message_item .avatar {
  cursor: pointer;
  text-decoration: none;
}

```



Do the same for the following file:
- `messagegroupitem.js`

remove the following code:

```
import { DateTime } from 'luxon';
```

and replace with:

```
import { format_datetime, message_time_ago } from '../lib/DateTimeFormats';
```

same for the following code:
```
   <div className="created_at" title={props.message_group.created_at}>
  <span className='ago'>{format_time_created_at(props.message_group.created_at)}</span> 
```

and replace with the following:

```sh

<div className="created_at" title={format_datetime(props.message_group.created_at)}>
<span className='ago'>{message_time_ago(props.message_group.created_at)}</span> 
```
Also remove this portion of the code:
```
const format_time_created_at = (value) => {
    // format: 2050-11-20 18:32:47 +0000
    const created = DateTime.fromISO(value)
    const now     = DateTime.now()
    const diff_mins = now.diff(created, 'minutes').toObject().minutes;
    const diff_hours = now.diff(created, 'hours').toObject().hours;

    if (diff_hours > 24.0){
      return created.toFormat("LLL L");
    } else if (diff_hours < 24.0 && diff_hours > 1.0) {
      return `${Math.floor(diff_hours)}h`;
    } else if (diff_hours < 1.0) {
      return `${Math.round(diff_mins)}m`;
    }
  };
```

from the `activitycontent.js` do the following ammendments:

Remove the following code:
```sh
import { DateTime } from 'luxon';
```
and replace with:

```sh
import { format_datetime, time_ago } from '../lib/DateTimeFormats';
```

Modify the following code:
```
  <div className="created_at" title={props.activity.created_at}>
  <span className='ago'>{format_time_created_at(props.activity.created_at)}</span> 
```
to the following:

```
<div className="created_at" title={format_datetime(props.activity.created_at)}>
<span className='ago'>{time_ago(props.activity.created_at)}</span> 
```

Also remove this portion of the code:
```sh
 const format_time_created_at = (value) => {
    // format: 2050-11-20 18:32:47 +0000
    const past = DateTime.fromISO(value)
    const now     = DateTime.now()
    const diff_mins = now.diff(past, 'minutes').toObject().minutes;
    const diff_hours = now.diff(past, 'hours').toObject().hours;

    if (diff_hours > 24.0){
      return past.toFormat("LLL L");
    } else if (diff_hours < 24.0 && diff_hours > 1.0) {
      return `${Math.floor(diff_hours)}h ago`;
    } else if (diff_hours < 1.0) {
      return `${Math.round(diff_mins)}m ago`;
    }
  };

  const format_time_expires_at = (value) => {
    // format: 2050-11-20 18:32:47 +0000
    const future = DateTime.fromISO(value)
    const now     = DateTime.now()
    const diff_mins = future.diff(now, 'minutes').toObject().minutes;
    const diff_hours = future.diff(now, 'hours').toObject().hours;
    const diff_days = future.diff(now, 'days').toObject().days;

    if (diff_hours > 24.0){
      return `${Math.floor(diff_days)}d`;
    } else if (diff_hours < 24.0 && diff_hours > 1.0) {
      return `${Math.floor(diff_hours)}h`;
    } else if (diff_hours < 1.0) {
      return `${Math.round(diff_mins)}m`;
    }
  };
```

Do the same changes for the following line:
Replace:
```
 <span className='ago'>{format_time_expires_at(props.activity.expires_at)}</span>

```

 with the following:
 ```
 <span className='ago'>{time_ago(props.activity.expires_at)}</span>
 ```

Replace:
```py
     expires_at =  <div className="expires_at" title={props.activity.expires_at}>
```

with the following:

```py
   expires_at =  <div className="expires_at" title={format_datetime(props.activity.expires_at)}>
```


## Save the work on its own branch named "week-6"
```sh
cd aws-bootcamp-cruddur-2024
git checkout -b week-6
```
<hr/>

## Commit
Add the changes and create a commit named: "Deploying Containers and DNS"
```sh
git add .
git commit -m "Deploying Containers and DNS"
```
Push your changes to the branch
```sh
git push origin week-6
```
<hr/>

### Tag the commit
```sh
git tag -a week-6 -m "Setting up Deploying Containers and DNS"
```
<hr/>

### Push your tags
```sh
git push --tags
```
<hr/>

### Switching Between Branches back to Main
```sh
git checkout main
```
<hr/>

### Merge Changes
```sh
git merge week-6
```
<hr/>

### Push Changes to Main
```sh
git push origin main
```
<hr/>

#### Branches?
If you want to keep the "week-1" branch for future reference or additional work, 
you can keep it as is. If you no longer need the branch, you can delete it after merging.
```sh
git branch -d week-6  # Deletes the local branch
git push origin --delete week-6  # Deletes the remote branch
```
