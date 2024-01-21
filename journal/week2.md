# Week 2 — Distributed Tracing

## #1 HONEYCOMB 

On [Honeycomb website](https://www.honeycomb.io/), create a new environment named `bootcamp`, and get the corresponding API key.
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
Then use your API Key in `backend-flask` -> `docker-compose.yml` file >   
under
'backend-flask:
    environment:' 

add the code below:

```yaml
      OTEL_SERVICE_NAME: 'backend-flask'
      OTEL_EXPORTER_OTLP_ENDPOINT: "https://api.honeycomb.io"
      OTEL_EXPORTER_OTLP_HEADERS: "x-honeycomb-team=${HONEYCOMB_API_KEY}"
```
Add the code below in `backend-flask` -> `requirements.txt` to install required packages to use Open Telemetry (OTEL) services.
```txt
opentelemetry-api 
opentelemetry-sdk 
opentelemetry-exporter-otlp-proto-http 
opentelemetry-instrumentation-flask 
opentelemetry-instrumentation-requests
```

Then run the code below from within 'backend-flask':
```sh
      pip install -r requirements.txt
```

- **To get required packages**
Below is the `backend-flask>>app.py` code required for Honeycomb, 
To be placed at around line 16 after 'from services...' but above 'app = Flask(__name__)'
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
```py
# Honeycomb ------------
# Initialize tracing and an exporter that can send data to Honeycomb
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
```

To create a span do:
```py
  simple_processor = SimpleSpanProcessor(ConsoleSpanExporter())
  provider.add_span_processor(simple_processor)
```
- **Add the code below inside the 'app' to Initialize automatic instrumentation with Flask**
```py
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
To create span and attribute, add the following code on the app.py
```python
from opentelemetry import trace
tracer = trace.get_tracer("home.activities")
```
To create span and attribute, add the following code on the home_activities.py
```python
from opentelemetry import trace
tracer = trace.get_tracer("home.activities")
```
```python
with tracer.start_as_current_span("home-activities-mock-data"):
    span = trace.get_current_span()
```
at the end of the code, put the following
```python
span.set_attribute("app.result_lenght", len(results))
```

An idea for an additional span would be:
```python
span.set_attribute("app.now", now.isoformat())
```

add this to home_activities.py
```py
LOGGER.info("HomeActivities")
```

And comment out the following code:
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

For a full walkthrough on how to add Honeycomb check out the docs at:
```html
https://docs.honeycomb.io/getting-data-in/opentelemetry/python-distro/
```
Specifically look at **trace**, **span** and **Adding attributes to spans**.

## #2 AWS X-RAY
Amazon has another service called X-RAY which is helpful in tracing requests by microservices. analyzes and debugs application running on distributed environments. 

check the env var for the AWS region using the following command:
```sh
env | grep AWS_REGION
```
If there is no result run:
```sh
export AWS_REGION="<chosen region>"
gp env AWS_REGION="<chosen region>"
```
- To get your application traced in AWS X-RAY you need to install aws-xray-sdk module. You can do this by running the commands below:
```
pip install aws-xray-sdk
```
In the backend-flask requirements.text, insert the following:
```py
aws-xray-sdk
```
Additionally, to install all the dependencies via docker compose run:
```sh
pip install -r requirements.txt
```

Make sure to create segements and subsegments by following the instructional videos. 

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
```

- Created our own Sampling Rule name 'Cruddur'. This code was written in `aws/json/xray.json` file
```json
{
  "SamplingRule": {
      "RuleName": "Cruddur",
      "ResourceARN": "*",
      "Priority": 9000,
      "FixedRate": 0.1,
      "ReservoirSize": 5,
      "ServiceName": "Cruddur",
      "ServiceType": "*",
      "Host": "*",
      "HTTPMethod": "*",
      "URLPath": "*",
      "Version": 1
  }
}
```
- **To create a new group for tracing and analyzing errors and faults in a Flask application.**
```py
FLASK_ADDRESS="https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
aws xray create-group \
   --group-name "Cruddur" \
   --filter-expression "service(\"$FLASK_ADDRESS\")"
```
<bold> or better yet run </bold>:
```py
aws xray create-group \
   --group-name "Cruddur" \
   --filter-expression "service(\"backend-flask")"
```
The above code is useful for setting up monitoring for a specific Flask service using AWS X-Ray. It creates a group that can be used to visualize and analyze traces for that service, helping developers identify and resolve issues more quickly.

Then run this command to get the above code executed 
```bash
aws xray create-sampling-rule --cli-input-json file://aws/json/xray.json
```

- **Install Daemon Service**
To install the  X-RAY Daemon Service for that we add the code below to `docker-compose.yml` file.
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
Also add Environment Variables in the `docker-compose.yml` file:
```yaml
   AWS_XRAY_URL: "*4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}*"
   AWS_XRAY_DAEMON_ADDRESS: "xray-daemon:2000"
```

```python
# xray
XRayMiddleware(app, xray_recorder)
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

add the following code on the app.py on our backend-flask
```python
# Cloudwatch
import watchtower
import logging
from time import strftime
```
```py
# Configuring Logger to Use CloudWatch
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
cw_handler = watchtower.CloudWatchLogHandler(log_group='cruddur')
LOGGER.addHandler(console_handler)
LOGGER.addHandler(cw_handler)
LOGGER.info("some message")
```
```py
@app.after_request
def after_request(response):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    LOGGER.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
    return response
```
Test the Logs via an API endpoint
```
LOGGER.info('Hello Cloudwatch! from  /api/activities/home')
```

## #4 ROLLBAR
Rollbar is used to **track errors** and monitor applications for error, it tracks and helps one to debug by providing detailed information about the Error.
- **Created my Rollbar account** ->  https://rollbar.com/
- **Then created a new Rollbar Project** : It asks you to setup your project , you get chance to select your SDK and also provides instructions on how to start. 
- **Access token** is provided for your new Rollbar Project.
- **Installed** `blinker` and `rollbar`.
  add this code to requirements.text
      ```py
      blinker
      rollbar
      ```
- Set the access token as an env var:
```
export ROLLBAR_ACCESS_TOKEN="<token>"
gp env ROLLBAR_ACCESS_TOKEN="<token>"
```
- **Added to backend-flask -> `docker-compose.yml`**
```yaml
ROLLBAR_ACCESS_TOKEN: "${ROLLBAR_ACCESS_TOKEN}"
```
- **Imported** for Rollbar
  insert the following code in -> backend-flask/app.py
```py
import rollbar
import rollbar.contrib.flask
from flask import got_request_exception
```
```py
# Rollbar
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
```py
@app.route('/rollbar/test')
def rollbar_test():
    rollbar.report_message('Hello World!', 'warning')
    return "Hello World!"
```

## [Note] Changes to Rollbar:

During the original bootcamp cohort, there was a newer version of flask.
This resulted in rollback implementation breaking due to a change is the flask api.

If you notice rollbar is not tracking, utilize the code from this file:

https://github.com/omenking/aws-bootcamp-cruddur-2023/blob/week-x/backend-flask/lib/rollbar.py


### Demo

To view the endpoints visit ports:
Frontend - port 3000
> Backend - port 4567, 
<br />
The link will be similar to: 'https://4567-stevecmd-awsbootcampcru-c7fjn6b3pzb.ws-eu107.gitpod.io/api/activities/home' to see Home or, 
<br />
'https://4567-stevecmd-awsbootcampcru-c7fjn6b3pzb.ws-eu107.gitpod.io/api/activities/notifications' to see the notifications endpoint. 
<br />
> The frontend - port 3000,
The link will be similar to: 'https://3000-stevecmd-awsbootcampcru-c7fjn6b3pzb.ws-eu107.gitpod.io/'