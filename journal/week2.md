# Week 2 — Distributed Tracing

## #1 HONEYCOMB 

On [Honeycomb website](https://www.honeycomb.io/), create a new environment named `bootcamp`, and get the corresponding API key.
<br />
[Documentation](docs.honeycomb.io)
To set the Honeycomb API Key as an environment variable in Gitpod use these commands: 
```bash
gp env HONEYCOMB_API_KEY="<your API key>"
export HONEYCOMB_API_KEY="<your API key>"
```

Confirm the env vars have been set:
```sh
      env | grep HONEY
```
Then use your API Key in `backend-flask` -> `docker-compose.yml` file. 
<br />
under >
```
backend-flask:
    environment:
``` 
<br />

add the code below:

```yaml
      OTEL_SERVICE_NAME: 'backend-flask'
      OTEL_EXPORTER_OTLP_ENDPOINT: "https://api.honeycomb.io"
      OTEL_EXPORTER_OTLP_HEADERS: "x-honeycomb-team=${HONEYCOMB_API_KEY}"
```
<br />

Add the code below in `backend-flask` -> `requirements.txt` to install required packages to use Open Telemetry (OTEL) services.
```txt
opentelemetry-api 
opentelemetry-sdk 
opentelemetry-exporter-otlp-proto-http 
opentelemetry-instrumentation-flask 
opentelemetry-instrumentation-requests
```

<br />
Then run the code below from within 'backend-flask':

```sh
      pip install -r requirements.txt
```

- **To get required packages**
  <br />
Below is the `backend-flask>>app.py` code required for Honeycomb, <br />
To be placed at around line 16 after `from services...` but above `app = Flask(__name__)` <br />

```py
# Honeycomb ------------
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
```
- **Initialize tracing and an exporter that can send data to Honeycomb**
```python
# Honeycomb ------------
# Initialize tracing and an exporter that can send data to Honeycomb
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
```
<br />

To create a span do: 
<br />
```python
  # OTEL --------------
  # Show this in the logs within backend-flask app (STDOUT)
  simple_processor = SimpleSpanProcessor(ConsoleSpanExporter())
  provider.add_span_processor(simple_processor)
```

- **Add the code below inside the 'app' to Initialize automatic instrumentation with Flask**
  <br />
```python
# Honeycomb ------------
# Initialize automatic instrumentation with Flask
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

frontend = os.getenv('FRONTEND_URL')
backend = os.getenv('BACKEND_URL')
origins = [frontend, backend]
cors = CORS(
  app, 
  resources={r"/api/*": {"origins": origins}},
  expose_headers="location,link",
  allow_headers="content-type,if-modified-since",
  methods="OPTIONS,GET,HEAD,POST"
)
```

<br />
To create a span and attribute, add the following code on 'app.py':

```python
      from opentelemetry import trace
      tracer = trace.get_tracer("home.activities")
```

<br />
To create span and attribute, add the following code in 'home_activities.py':

```python
      from opentelemetry import trace
      tracer = trace.get_tracer("home.activities")
```

```python
      with tracer.start_as_current_span("home-activities-mock-data"):
          span = trace.get_current_span()
```

at the end of the code, add the following:
```python
      span.set_attribute("app.result_length", len(results))
```

An idea for an additional span would be:
```python
span.set_attribute("app.now", now.isoformat())
```

add the code below to home_activities.py for testing:
```py
LOGGER.info("HomeActivities")
```

Once you receive info on Honeycomb, comment out the following code:
```py
#def run(Logger):
   #Logger.info("HomeActivities")
```

<Bold>Enable Gitpod to auto load ports:</Bold>
In the gitpod.yml file, after the extensions add:
```python
ports:
  - name: frontend
    port: 3000
    onOpen: open-browser
    visibility: public
  - name: backend
    port: 4567
    visibility: public
  - name: xray-daemon
    port: 2000
    visibility: public
```

<Bold>Enable Gitpod to auto install frontend-react dependencies:</Bold>
In the gitpod.yml file, after the aws-cli dependencie add:
```python
  - name: react-js
    init: |
      cd frontend-react-js
      npm i
```

<br />

For a full walkthrough on how to add Honeycomb check out the docs at:
```html
      https://docs.honeycomb.io/getting-data-in/opentelemetry/python-distro/
```
Specifically look at **trace**, **span** and **Adding attributes to spans**.

## #2 AWS X-RAY
Amazon has another service called X-RAY which is helpful in tracing requests by microservices. analyzes and debugs application running on distributed environments. 

### Resources:
[AWS X-Ray](https://pages.github.com/](https://docs.aws.amazon.com/xray/latest/devguide/aws-xray.html))
<br />
[AWS X-Ray Best practices](https://pages.github.com/](https://stackoverflow.com/questions/54236375/what-are-the-best-practises-for-setting-up-x-ray-daemon))
<br />
[AWS X-ray GitHub repo](https://github.com/aws/aws-xray-sdk-python)
[Hashnode Article by Olga](https://olley.hashnode.dev/aws-free-cloud-bootcamp-instrumenting-aws-x-ray-subsegments)

check the env var for the AWS region using the following command:
```sh
env | grep AWS_REGION
```
If there is no result run:
```sh
export AWS_REGION="<chosen region>"
gp env AWS_REGION="<chosen region>"
```
Check that your authentication details are still in place and that you are able to connect to AWS:
```py
aws sts get-caller-identity
```
The prompt should return data similar to:
```py
      "UserId": "<AccountName>"
      "Account": "<AccountNumber>"
      "Arn": "<AccountARN>"
```
<br />

- To get your application traced in AWS X-RAY you need to install aws-xray-sdk module. You can do this by running the commands below:
```
pip install aws-xray-sdk
```
In the backend-flask requirements.text, insert the following:
```py
aws-xray-sdk
```
Additionally, to install all the dependencies via Python package manager run:
```sh
pip install -r requirements.txt
```

Make sure to create segments and subsegments by following the instructional videos. 

Insert the following code inside the app.py
```python
# Xray
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
```
```python
# Xray
xray_url = os.getenv("AWS_XRAY_URL")
xray_recorder.configure(service='backend-flask', dynamic_naming=xray_url)
XRayMiddleware(app, xray_recorder)
```
Modify the code in app.py as follows:
around line 116:
```py
@app.route("/api/activities/home", methods=['GET'])
@xray_recorder.capture('activities_home')
def data_home():
  data = HomeActivities.run()
  return data, 200
```

around line 127:
```py
@app.route("/api/activities/@<string:handle>", methods=['GET'])
@xray_recorder.capture('activities_users')
def data_handle(handle):
  model = UserActivities.run(handle)
  if model['errors'] is not None:
```

around line 160:
```py
@app.route("/api/activities/<string:activity_uuid>", methods=['GET'])
@xray_recorder.capture('activities_show')
```

- Created our own Sampling Rule name 'Cruddur'. This code was written in `aws/json/xray.json` file:
```json
{
  "SamplingRule": {
      "RuleName": "Cruddur",
      "ResourceARN": "*",
      "Priority": 9000,
      "FixedRate": 0.1,
      "ReservoirSize": 5,
      "ServiceName": "backend-flask",
      "ServiceType": "*",
      "Host": "*",
      "HTTPMethod": "*",
      "URLPath": "*",
      "Version": 1
  }
}
```
- **To create a new group for tracing and analyzing errors and faults in a Flask application.**
<br> Add a sampling group to monitor log events:
```py
aws xray create-group \
   --group-name "Cruddur" \
   --filter-expression "service(\"backend-flask\")"
```
The above code is useful for setting up monitoring for a specific Flask service using AWS X-Ray. It creates a group that can be used to visualize and analyze traces for that service, helping developers identify and resolve issues more quickly. We are specifically monitoring backend-flask.

Then run this command to get the above code executed 
```bash
aws xray create-sampling-rule --cli-input-json file://aws/json/xray.json
```

- **Install Daemon Service**
Add the code below to `docker-compose.yml` file.
```yaml
 xray-daemon:
    image: "amazon/aws-xray-daemon"
    environment:
      AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
      AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
      AWS_REGION: "us-east-1"
    command:
      - "xray -o -b xray-daemon:2000"
    ports:
      - 2000:2000/udp
```
Also add Environment Variables in the `docker-compose.yml` file under environment in backend-flask:
```yaml
   AWS_XRAY_URL: "*4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}*"
   AWS_XRAY_DAEMON_ADDRESS: "xray-daemon:2000"
```
Add the entry below to app.py after the entry 'app = Flask(__name__)'
```python
# xray
XRayMiddleware(app, xray_recorder)
```

The full code for 'user_activities.py' service having implemented x-ray should be similar to:
```py
from datetime import datetime, timedelta, timezone
class UserActivities:
  def run(user_handle):
    model = {
      'errors': None,
      'data': None
    }

    now = datetime.now(timezone.utc).astimezone()

    if user_handle == None or len(user_handle) < 1:
      model['errors'] = ['blank_user_handle']
    else:
      now = datetime.now()
      results = [{
        'uuid': '248959df-3079-4947-b847-9e0892d1bab4',
        'handle':  'Andrew Brown',
        'message': 'Cloud is fun!',
        'created_at': (now - timedelta(days=1)).isoformat(),
        'expires_at': (now + timedelta(days=31)).isoformat()
      }]
      model['data'] = results
    return model
```

## #3 CloudWatch
For CLoudWatch install `watchtower` and import `watchtower`, `logging` and `strftime from time`.

In `backend-flask requirements.text`, insert the following text:
```yaml
watchtower
```

To install all dependencies>> <bold>`only necessary this time as it will be run automatically via docker compose`</bold>

```sh
pip install -r requirements.txt
```

Also set env vars in backend flask > `docker-compose.yml` 
```yaml
      AWS_DEFAULT_REGION: "${AWS_DEFAULT_REGION}"
      AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
      AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
```

- **Configure LOGGER to use CloudWatch**

add the following code on the 'app.py' file in backend-flask after the X-Ray Middleware import:
```python
# Cloudwatch
import watchtower
import logging
from time import strftime
```
Add the code below directly afterwards:
```py
# Configuring Logger to Use CloudWatch
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
cw_handler = watchtower.CloudWatchLogHandler(log_group='cruddur')
LOGGER.addHandler(console_handler)
LOGGER.addHandler(cw_handler)
LOGGER.info("test log")
```

To log any errors after every request put the code below into app.py just before '@app.route("/api/message_groups...")'
```py
# ------- Cloudwatch Logs ----------
@app.after_request
def after_request(response):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    LOGGER.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
    return response
```
The code should be similar to:
```py
class HomeActivities:
      def run(logger):
        logger.info("HomeActivities")
```
In app.py add the new logger:
```py
      LOGGER.info('test log')
```
Modify 'app.py' as follows:
```py
      @app.route("/api/activities/home", methods=['GET'])
      def data_home():
        data = HomeActivities.run(logger=LOGGER)
        return data, 200
```
Also confirm you have set env vars in backend flask > `docker-compose.yml` 
```yaml
      AWS_DEFAULT_REGION: "${AWS_DEFAULT_REGION}"
      AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
      AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
```
Modify 'backend-flask/services/user_activities.py' to look as below:
```py
from datetime import datetime, timedelta, timezone
from aws_xray_sdk.core import xray_recorder
class UserActivities:
  def run(user_handle):
    try:
      model = {
        'errors': None,
        'data': None
      }

      now = datetime.now(timezone.utc).astimezone()
      
      if user_handle == None or len(user_handle) < 1:
        model['errors'] = ['blank_user_handle']
      else:
        now = datetime.now()
        results = [{
          'uuid': '248959df-3079-4947-b847-9e0892d1bab4',
          'handle':  'Andrew Brown',
          'message': 'Cloud is fun!',
          'created_at': (now - timedelta(days=1)).isoformat(),
          'expires_at': (now + timedelta(days=31)).isoformat()
        }]
        model['data'] = results

      subsegment = xray_recorder.begin_subsegment('mock-data')
      # xray ---
      dict = {
        "now": now.isoformat(),
        "results-size": len(model['data'])
      }
      subsegment.put_metadata('key', dict, 'namespace')
      xray_recorder.end_subsegment()
    finally:  
    #  # Close the segment
      xray_recorder.end_subsegment()
    return model
```

Modify 'backend-flask/app.py' to look as below:
```py
from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
import os

from services.home_activities import *
from services.user_activities import *
from services.create_activity import *
from services.create_reply import *
from services.search_activities import *
from services.message_groups import *
from services.messages import *
from services.create_message import *
from services.show_activity import *

# HoneyComb ---------
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# X-RAY ----------
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

# CloudWatch Logs ----
import watchtower
import logging

# Rollbar ------
from time import strftime
import os
import rollbar
import rollbar.contrib.flask
from flask import got_request_exception

# Configuring Logger to Use CloudWatch
# LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)
# console_handler = logging.StreamHandler()
# cw_handler = watchtower.CloudWatchLogHandler(log_group='cruddur')
# LOGGER.addHandler(console_handler)
# LOGGER.addHandler(cw_handler)
# LOGGER.info("test log")

# HoneyComb ---------
# Initialize tracing and an exporter that can send data to Honeycomb
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)

# X-RAY ----------
xray_url = os.getenv("AWS_XRAY_URL")
xray_recorder.configure(service='backend-flask', dynamic_naming=xray_url)

# OTEL ----------
# Show this in the logs within the backend-flask app (STDOUT)
#simple_processor = SimpleSpanProcessor(ConsoleSpanExporter())
#provider.add_span_processor(simple_processor)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = Flask(__name__)

# X-RAY ----------
XRayMiddleware(app, xray_recorder)

# HoneyComb ---------
# Initialize automatic instrumentation with Flask
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


frontend = os.getenv('FRONTEND_URL')
backend = os.getenv('BACKEND_URL')
origins = [frontend, backend]
cors = CORS(
  app, 
  resources={r"/api/*": {"origins": origins}},
  expose_headers="location,link",
  allow_headers="content-type,if-modified-since",
  methods="OPTIONS,GET,HEAD,POST"
)

# CloudWatch Logs -----
#@app.after_request
#def after_request(response):
#    timestamp = strftime('[%Y-%b-%d %H:%M]')
#    LOGGER.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
#    return response

# Rollbar
rollbar_access_token = os.getenv('ROLLBAR_ACCESS_TOKEN')
with app.app_context():
  def init_rollbar():
      """init rollbar module"""
      rollbar.init(
          # access token
          rollbar_access_token,
          # environment name
          'production',
          # server root directory, makes tracebacks prettier
          root=os.path.dirname(os.path.realpath(__file__)),
          # flask already sets up logging
          allow_logging_basic_config=False)

      # send exceptions from `app` to rollbar, using flask's signal system.
      got_request_exception.connect(rollbar.contrib.flask.report_exception, app)

@app.route('/rollbar/test')
def rollbar_test():
    rollbar.report_message('Hello World!', 'warning')
    return "Hello World!"

@app.route("/api/message_groups", methods=['GET'])
def data_message_groups():
  user_handle  = 'andrewbrown'
  model = MessageGroups.run(user_handle=user_handle)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200

@app.route("/api/messages/@<string:handle>", methods=['GET'])
def data_messages(handle):
  user_sender_handle = 'andrewbrown'
  user_receiver_handle = request.args.get('user_reciever_handle')

  model = Messages.run(user_sender_handle=user_sender_handle, user_receiver_handle=user_receiver_handle)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200
  return

@app.route("/api/messages", methods=['POST','OPTIONS'])
@cross_origin()
def data_create_message():
  user_sender_handle = 'andrewbrown'
  user_receiver_handle = request.json['user_receiver_handle']
  message = request.json['message']

  model = CreateMessage.run(message=message,user_sender_handle=user_sender_handle,user_receiver_handle=user_receiver_handle)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200
  return

@app.route("/api/activities/home", methods=['GET'])
@xray_recorder.capture('activities_home')
def data_home():
  data = HomeActivities.run()
  return data, 200

@app.route("/api/activities/@<string:handle>", methods=['GET'])
@xray_recorder.capture('activities_users')
def data_handle(handle):
  model = UserActivities.run(handle)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200

@app.route("/api/activities/search", methods=['GET'])
def data_search():
  term = request.args.get('term')
  model = SearchActivities.run(term)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200
  return

@app.route("/api/activities", methods=['POST','OPTIONS'])
@cross_origin()
def data_activities():
  user_handle  = 'andrewbrown'
  message = request.json['message']
  ttl = request.json['ttl']
  model = CreateActivity.run(message, user_handle, ttl)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200
  return

@app.route("/api/activities/<string:activity_uuid>", methods=['GET'])
@xray_recorder.capture('activities_show')
def data_show_activity(activity_uuid):
  data = ShowActivity.run(activity_uuid=activity_uuid)
  return data, 200

@app.route("/api/activities/<string:activity_uuid>/reply", methods=['POST','OPTIONS'])
@cross_origin()
def data_activities_reply(activity_uuid):
  user_handle  = 'andrewbrown'
  message = request.json['message']
  model = CreateReply.run(message, user_handle, activity_uuid)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200
  return

if __name__ == "__main__":
  app.run(debug=True)
```
At this point X-ray should be working.
Visit the frontend link and append '/@AndrewBrown' to test X-ray
The link will be similar to:
'https://3000-stevecmd-awsbootcampcru-c7fjn6b3pzb.ws-eu107.gitpod.io/@AndrewBrown'
This is similar to pressing the 'Home' button on the webpage then clicking on the 'logged in users name' in this example its 'Andrew Brown'

Cloud watch logs can get expensive, to deactivate them revert the code above as follows:
'home_activities.py'
```py
class HomeActivities:
      def run():
        #logger.info("HomeActivities")
```
and 'app.py'
```py
# Configuring Logger to Use CloudWatch
# LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)
# console_handler = logging.StreamHandler()
# cw_handler = watchtower.CloudWatchLogHandler(log_group='cruddur')
# LOGGER.addHandler(console_handler)
# LOGGER.addHandler(cw_handler)
# LOGGER.info("test log")
```
```py
      @app.route("/api/activities/home", methods=['GET'])
      def data_home():
        data = HomeActivities.run()
        return data, 200
```
We can now disable x-ray as well in 'app.py':
```python
# Xray
# from aws_xray_sdk.core import xray_recorder
# from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
```
```python
# Xray
# xray_url = os.getenv("AWS_XRAY_URL")
# xray_recorder.configure(service='backend-flask', dynamic_naming=xray_url)
```

```python
# xray
# XRayMiddleware(app, xray_recorder)
```

```py
#@app.after_request
#def after_request(response):
#    timestamp = strftime('[%Y-%b-%d %H:%M]')
#    LOGGER.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
#   return response
```
In 'backend-flask > services > user_activities.py':
```py
class UserActivities:
  def run(user_handle):
    # xray ---
    #segment = xray_recorder.begin_segment('user_activities')
```
```py
    #subsegment = xray_recorder.begin_subsegment('mock-data')
    # xray ---
    #dict = {
    #  "now": now.isoformat(),
    #  "results-size": len(model['data'])
    #}
    #subsegment.put_metadata('key', dict, 'namespace')

    return model
```


Once done name the commit 'Implement cloudwatch logs' and push the changes.

## #4 ROLLBAR
Rollbar is used to **track errors** and monitor applications for error, it tracks and helps one to debug by providing detailed information about the Error.
- **Create your Rollbar account** ->  https://rollbar.com/
- **Then create a new Rollbar Project** : It asks you to setup your project , you get the chance to select your SDK and also provides instructions on how to start.
  Proceed from the Welcome Screen
  Skip 'Add apps'
  On the 'Add SDK' menu' > 'All SDKS' > 'Flask'
- **Access token** is provided for your new Rollbar Project. save it. We will refer to it as <Rollbartoken>
  Skip their installation instructions as they are incomplete for our purposes.

- **Installation** `of blinker` and `rollbar`.
  add these dependencies to 'backend-flask > requirements.txt'
      ```py
      blinker
      rollbar
      ```
  change directories to 'backend-flask' and run:
  ```sh
      pip install -r requirements.txt
  ```
Set the access token as an env var:
```
export ROLLBAR_ACCESS_TOKEN="<Rollbartoken>"
gp env ROLLBAR_ACCESS_TOKEN="<Rollbartoken>"
```
Confirm that the env var has been saved:
```sh
      env | grep ROLLBAR
```
- **Added to backend-flask -> `docker-compose.yml`**
```yaml
ROLLBAR_ACCESS_TOKEN: "${ROLLBAR_ACCESS_TOKEN}"
```
- **Imported** for Rollbar
  insert the following code in -> backend-flask/app.py after the cloudwatch logs imports (line 33)
```py
---- Rollbar -----
from time import strftime
import rollbar
import rollbar.contrib.flask
from flask import got_request_exception
```
After the Honeycomb intialization steps ending in:
```py
provider.add_span_processor(processor)
```
add the entry below at around line 95 just above '.../rollbar/test':
```py
# Rollbar ---------
rollbar_access_token = os.getenv('ROLLBAR_ACCESS_TOKEN')
@app.before_first_request
def init_rollbar():
    """init rollbar module"""
    rollbar.init(
        # access token
        rollbar_access_token,
        # environment name
        'production',
        # server root directory, makes tracebacks prettier
        root=os.path.dirname(os.path.realpath(__file__)),
        # flask already sets up logging
        allow_logging_basic_config=False)

    # send exceptions from `app` to rollbar, using flask's signal system.
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)
```
- **Add an endpoint to `app.py` to allow rollbar testing:**
  <br>
  Place it just above '@app.route("/api/message_groups'
```py
@app.route('/rollbar/test')
def rollbar_test():
    rollbar.report_message('Hello World!', 'warning')
    return "Hello World!"
```

At this point I wanted to test the notifications endpoint and realized it wasnt working, below are the fixes:


- **Add an endpoint to `app.py` to allow notification:**
  <br>
  Add an import `from services.notifications_activities import *` <br>
  Add the route:
```py
@app.route("/api/activities/notifications", methods=['GET'])
def data_notifications():
  data = NotificationsActivities.run()
  return data, 200
```

Run the app (docker-compose up) to confirm that Rollbar is getting a response.
On the browser, visit the the backend url and append: '.../api/activities/home'
You should see some 'json'.

In 'docker-compose.yml' under backend-flask > environment, add the Rollbar variables:
```py
      ROLLBAR_ACCESS_TOKEN: "${ROLLBAR_ACCESS_TOKEN}"
```

On the browser, visit the the backend url and append: '.../rollbar/test'
You should get the response:
'Hello World!'
Check the Rollbar website for your logs and make sure to select all the checkboxes under Items > Levels.

## [Note] Changes to Rollbar:

During the original bootcamp cohort, there was a newer version of flask.
This resulted in rollback implementation breaking due to a change is the flask api.

If you notice rollbar is not tracking, utilize the code from this file:

https://github.com/omenking/aws-bootcamp-cruddur-2023/blob/week-x/backend-flask/lib/rollbar.py

You can test the logs by janking the code eg deleting 'return' at the bottom of the 'home_activities.py' file.
Once you get your responses, make sure to fix the janked code and commit the changes as 'finished implementing rollbar'.

### Demo

To view the endpoints visit ports:
Frontend - port 3000
- Backend - port 4567, <br />
The link will be similar to: 'https://4567-stevecmd-awsbootcampcru-c7fjn6b3pzb.ws-eu107.gitpod.io/api/activities/home' to see Home or, 
'https://4567-stevecmd-awsbootcampcru-c7fjn6b3pzb.ws-eu107.gitpod.io/api/activities/notifications' to see the notifications endpoint. 
<br />

- The frontend - port 3000, <br />
The link will be similar to: 'https://3000-stevecmd-awsbootcampcru-c7fjn6b3pzb.ws-eu107.gitpod.io/'

## Save the work on its own branch named "week-2"
```sh
cd aws-bootcamp-cruddur-2024
git checkout -b week-2
```
<hr/>

## Commit
Add the changes and create a commit named: "Distributed Tracing"
```sh
git add .
git commit -m "Distributed Tracing"
```
Push your changes to the branch
```sh
git push origin week-2
```
<hr/>

### Tag the commit
```sh
git tag -a week-2 -m "Setting up Distributed Tracing"
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
git merge week-2
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
git branch -d week-2  # Deletes the local branch
git push origin --delete week-2  # Deletes the remote branch
```

