# Week 0 — Billing and Architecture
---
**Todo Checklist:**
- [x] [Watched Week 0 - Live Streamed Video](https://www.youtube.com/watch?v=tDPqmwKMP7Y&list=PLBfufR7vyJJ7k25byhRXJldB5AiwgNnWv&index=29)
- [x] [Watched Chirag's Week 0 - Spend Considerations](https://www.youtube.com/watch?v=FKAScachFgk&list=PLBfufR7vyJJ7k25byhRXJldB5AiwgNnWv&index=25)
- [x] [Watched Ashish's Week 0 - Security Considerations](https://www.youtube.com/watch?v=zJnNe5Nv4tE&list=PLBfufR7vyJJ7k25byhRXJldB5AiwgNnWv&index=22)
- [x] [Recreate Conceptual Diagram in Lucid Charts or on a Napkin](https://www.youtube.com/watch?v=b-idMgFFcpg&list=PLBfufR7vyJJ7k25byhRXJldB5AiwgNnWv&index=23)
- [x] [Recreate Logical Architectual Diagram in Lucid Charts](https://www.youtube.com/watch?v=OAMHu1NiYoI&list=PLBfufR7vyJJ7k25byhRXJldB5AiwgNnWv&index=24)
- [x] [Create an Admin User](https://www.youtube.com/watch?v=OdUnNuKylHg&list=PLBfufR7vyJJ7k25byhRXJldB5AiwgNnWv&index=14)
- [x] Use CloudShell
- [x] Generate AWS Credentials
- [x] Installed AWS CLI
- [x] Create a Billing Alarm
- [x] Create a Budget

- [x] Complete 100% of the tasks

<hr/>

## Getting the AWS CLI Working

We'll be using the AWS CLI often in this bootcamp,
so we'll proceed to installing this account.

<hr/>

### Install AWS CLI

- We are going to install the AWS CLI when our Gitpod enviroment lanuches.
- We are are going to set AWS CLI to use partial autoprompt mode to make it easier to debug CLI commands.
- The bash commands we are using are the same as the [AWS CLI Install Instructions](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

Update our `.gitpod.yml` to include the following task.

```sh
tasks:
  - name: aws-cli
    env:
      AWS_CLI_AUTO_PROMPT: on-partial
    init: |
      cd /workspace
      curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
      unzip awscliv2.zip
      sudo ./aws/install
      cd $THEIA_WORKSPACE_ROOT
vscode:
  extensions:
    - 42Crunch.vscode-openapi
```

We'll also run these commands individually to perform the install manually at first.

<hr/>

### Create a new User and Generate AWS Credentials

- Go to [IAM Users Console](https://us-east-1.console.aws.amazon.com/iamv2/home?region=us-east-1#/users) and create a new user
- `Enable console access` for the user
- Create a new `Admin` Group and apply `AdministratorAccess`
- Create the user and go find and click into the user
- Click on `Security Credentials` and `Create Access Key`
- Choose AWS CLI Access
- Download the CSV with the credentials and store it securely

<hr/>

### Set Env Vars

We will set these credentials for the current bash terminal
```
export AWS_ACCESS_KEY_ID="<ACCESS_KEY>"
export AWS_SECRET_ACCESS_KEY="<SECRET_ACCESS_KEY>"
export AWS_DEFAULT_REGION=us-east-1
```

Enable Gitpod to save these credentials for use when we relaunch our workspaces
```
gp env AWS_ACCESS_KEY_ID=""
gp env AWS_SECRET_ACCESS_KEY=""
gp env AWS_DEFAULT_REGION=us-east-1
```

Confirm Gitpod has save these credentials as env vars
```
env | grep AWS_ACCESS_KEY_ID
env | grep AWS_SECRET_ACCESS_KEY
env | grep AWS_DEFAULT_REGION
```

<hr/>

### Check that the AWS CLI is working and you are the expected user

```sh
aws sts get-caller-identity
```

Output should be similar to:
```json
{
    "UserId": "AIFBZRJIQN2ONP4ET4EK4",
    "Account": "655602346534",
    "Arn": "arn:aws:iam::655602346534:user/andrewcloudcamp"
}
```

<hr/>

## Enable Billing via console

Turn on Billing Alerts to recieve alerts...

- In your Root Account go to the [Billing Page](https://console.aws.amazon.com/billing/)
- Under `Billing Preferences` Choose `Receive Billing Alerts`
- Save Preferences

<hr/>

## Creating a Billing Alarm via CLI
- Supply your AWS Account ID:
  ```sh
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  ```

- Confirm that your AWS Account ID is valid:
  ```sh
  aws sts get-caller-identity --query Account --output text
  ```

- Make your AWS Account ID an env var:
  ```sh
  export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  ```

- Confirm your AWS Account ID env var has been saved:
  ```
  env | grep AWS_ACCOUNT_ID
  ```
  
- Export your account ID as a gitpod variable: 
  ```
  export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

  gp env AWS_ACCOUNT_ID="<insert account id>"
   ```

### Create SNS (Subscriber Notification Service) Topic

- We need an SNS topic before we create an alarm.
- The SNS topic is what will delivery us an alert when we get overbilled
- [aws sns create-topic](https://docs.aws.amazon.com/cli/latest/reference/sns/create-topic.html)

We'll create an SNS Topic
```sh
aws sns create-topic --name billing-alarm
```
This will return a TopicARN

We'll create a subscription by supplying the TopicARN gotten from the above command and our Email:
```sh
aws sns subscribe \
    --topic-arn="<TopicARN>" \
    --protocol= email \
    --notification-endpoint <your@email.com>
```

Check your email and confirm the subscription

<hr/>

## Create an AWS Budget

[aws budgets create-budget](https://docs.aws.amazon.com/cli/latest/reference/budgets/create-budget.html)

- Create a folder at the top level named aws if it is not already there, in it create a folder named json: 
  ```
  cd aws-bootcamp-cruddur-2024
  mkdir aws
  cd aws
  mkdir json
  cd json
   ```

  
- Update the json files in aws/json :
Create a file named 'budget.json' and insert the code below:
```sh
{
    "BudgetLimit": {
        "Amount": "1",
        "Unit": "USD"
    },
    "BudgetName": "Example Tag Budget",
    "BudgetType": "COST",
    "CostFilters": {
        "TagKeyValue": [
            "user:Key$value1",
            "user:Key$value2"
        ]
    },
    "CostTypes": {
        "IncludeCredit": true,
        "IncludeDiscount": true,
        "IncludeOtherSubscription": true,
        "IncludeRecurring": true,
        "IncludeRefund": true,
        "IncludeSubscription": true,
        "IncludeSupport": true,
        "IncludeTax": true,
        "IncludeUpfront": true,
        "UseBlended": false
    },
    "TimePeriod": {
        "Start": 1477958399,
        "End": 3706473600
    },
    "TimeUnit": "MONTHLY"
}
```

Create a file named 'budget-notifications-with-subscribers.json' and insert the code below:
```sh
[
    {
        "Notification": {
            "ComparisonOperator": "GREATER_THAN",
            "NotificationType": "ACTUAL",
            "Threshold": 80,
            "ThresholdType": "PERCENTAGE"
        },
        "Subscribers": [
            {
                "Address": "<Your email>",
                "SubscriptionType": "EMAIL"
            }
        ]
    }
]
```
Then run the following code in the CLI:

```sh
cd aws-bootcamp-cruddur-2024
```
```sh
aws budgets create-budget \
    --account-id $ACCOUNT_ID \
    --budget file://aws/json/budget.json \
    --notifications-with-subscribers file://aws/json/budget-notifications-with-subscribers.json
```
<hr/>

#### Create Alarm

- [aws cloudwatch put-metric-alarm](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/put-metric-alarm.html)
- [Create an Alarm via AWS CLI](https://aws.amazon.com/premiumsupport/knowledge-center/cloudwatch-estimatedcharges-alarm/)
- We need to update the configuration json script with the TopicARN we generated earlier
- We are just a json file because --metrics is is required for expressions and so its easier to us a JSON file.

Create the file aws/json/alarm-config.json and insert the following code and also edit the ACCOUNT_ID to match your aws account id:
```sh
{
    "AlarmName": "DailyEstimatedCharges",
    "AlarmDescription": "This alarm would be triggered if the daily estimated charges exceeds 1$",
    "ActionsEnabled": true,
    "AlarmActions": [
        "arn:aws:sns:us-east-1:<ACCOUNT_ID>:billing-alarm"
    ],
    "EvaluationPeriods": 1,
    "DatapointsToAlarm": 1,
    "Threshold": 1,
    "ComparisonOperator": "GreaterThanOrEqualToThreshold",
    "TreatMissingData": "breaching",
    "Metrics": [{
        "Id": "m1",
        "MetricStat": {
            "Metric": {
                "Namespace": "AWS/Billing",
                "MetricName": "EstimatedCharges",
                "Dimensions": [{
                    "Name": "Currency",
                    "Value": "USD"
                }]
            },
            "Period": 86400,
            "Stat": "Maximum"
        },
        "ReturnData": false
    },
    {
        "Id": "e1",
        "Expression": "IF(RATE(m1)>0,RATE(m1)*86400,0)",
        "Label": "DailyEstimatedCharges",
        "ReturnData": true
    }]
  }
```
Deploy the creation of the alarm by running the code below:
```sh
aws cloudwatch put-metric-alarm --cli-input-json file://aws/json/alarm-config.json
```
<hr/>

## Add the Backend dependencies to the requirements file
File location:
```sh
backend-flask/requirements.txt
```
Dependencies to be added:
```
flask
flask-cors
opentelemetry-api 
opentelemetry-sdk 
opentelemetry-exporter-otlp-proto-http 
opentelemetry-instrumentation-flask 
opentelemetry-instrumentation-requests
aws-xray-sdk
watchtower
blinker
rollbar
```
<hr/>

## Save the work on its own branch named "week-0"
```sh
git checkout -b week-0
```
<hr/>

## Commit
Add the changes and create a commit named: "Install AWS CLI into Gitpod tasks"
```sh
git add .
git commit -m "Install AWS CLI into Gitpod tasks"
```
Push your changes to the branch
```sh
git push origin week-0
```
<hr/>

### Tag the commit
```sh
git tag -a week-0 -m "Setting up project env vars"
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
git merge week-0
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
git branch -d week-1  # Deletes the local branch
git push origin --delete week-1  # Deletes the remote branch
```

