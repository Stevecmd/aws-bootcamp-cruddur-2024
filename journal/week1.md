# Week 1 — App Containerization
Container repo's:
- [DockerHub](https://hub.docker.com/)
- [Jfrog](https://jfrog.com/) - For artifacts / images

## Containerize Backend
### Create Docker File

Create a file here: `backend-flask/Dockerfile` containing the code below:

```dockerfile
FROM python:3.10-slim-buster

# Inside container
# Make a new folder inside the container
WORKDIR /backend-flask

# Outside container -> Inside container
# Requirements contains the python libraries to be installed
COPY requirements.txt requirements.txt

# Inside container
# installing python libraries
RUN pip3 install -r requirements.txt

# Outside container -> Inside container
# first period /backend-flask (outside container)
# second period /backend-flask (inside container) 
COPY . .

# Setting env vars inside container
# and will remain set while container is running
ENV FLASK_ENV=development

EXPOSE ${PORT}
# The command itself is invoking the Python interpreter (python3) with
# the -m flag, which allows running a module as a script.
# The module being run is flask, and the additional arguments provided
# to Flask are run --host=0.0.0.0 --port=4567.
# This essentially starts a Flask web application and
# binds it to all network interfaces (0.0.0.0) on port 4567.

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]
```

On the terminal run:
```sh
export FRONTEND_URL="*"
export BACKEND_URL="*"
```

<bold>NB:</bold>To unset the env vars run the code below:
```sh
unset FRONTEND_URL
unset BACKEND_URL
```
Confirm that they are unset:
```sh
env | grep FRONTEND_URL
env | grep BACKEND_URL
```
cd into the project directory 'aws-bootcamp-cruddur-2024':
```sh
  cd aws-bootcamp-cruddur-2024
```

### Build Container

```sh
docker build -t  backend-flask ./backend-flask
```

* Make sure that the image builds succesfully then run it:

```sh
docker run --rm -p 4567:4567 -it -e FRONTEND_URL='*' -e BACKEND_URL='*' backend-flask
```
If the command runs successfully, exit the server by pressing 'Ctrl+C':
On the terminal set the env vars:
```sh
set FRONTEND_URL="*"
set BACKEND_URL="*"
```

Run the container
```sh
docker run --rm -p 4567:4567 -it -e FRONTEND_URL='*' -e BACKEND_URL='*' -d backend-flask
```
The command above upon running succesfully will output your container number.

Visit the port link in a new Tab and make sure to append '/api/activities/home' to the URL, you should get Javascript response.

On gitpod open a new terminal and run the code below to see the running docker containers:
```sh
  docker ps
```
To see the images available run:
```sh
  docker images
```
### Delete an Image
NB to delete an image we use the 'rm' flag to make sure the container does not simply stop and stay in a suspended
state, 'rm' deletes the container.

```sh
docker image rm backend-flask --force
```

## Containerize Frontend

## Run NPM Install

We have to run NPM Install before building the container since it needs to copy the contents of node_modules

```
cd frontend-react-js
npm i
```

### Create Docker File

Create a file here: `frontend-react-js/Dockerfile`

```dockerfile
FROM node:16.18

ENV PORT=3000

COPY . /frontend-react-js
WORKDIR /frontend-react-js
RUN npm install
EXPOSE ${PORT}
CMD ["npm", "start"]
```
Go back a directory:
```sh
  cd ..
```
You should now be in the directory: 'aws-bootcamp-cruddur-2024'

### Create a docker-compose file

Create `docker-compose.yml` at the root' of your project ie within 'aws-bootcamp-cruddur-2024'. 
and put the following code in...

```yaml
version: "3.8"
services:
  backend-flask:
    environment:
      FRONTEND_URL: "https://3000-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
      BACKEND_URL: "https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
    build: ./backend-flask
    ports:
      - "4567:4567"
    volumes:
      - ./backend-flask:/backend-flask
  frontend-react-js:
    environment:
      REACT_APP_BACKEND_URL: "https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
    build: ./frontend-react-js
    ports:
      - "3000:3000"
    volumes:
      - ./frontend-react-js:/frontend-react-js

# the name flag is a hack to change the default prepend folder
# name when outputting the image names
networks: 
  internal-network:
    driver: bridge
    name: cruddur
```
Once done run docker compose up on the file docker-compose.yml to validate the file and see whether it runs.
Unlock port 3000 and 4567 and ensure they are in a running state.
Port 3000 should link to the running Cruddur website.
If the website does not have some mockposts or any other error, check the website logs to ensure there are no errors such as 'CORS'

## Adding DynamoDB Local and Postgres

We are going to use Postgres and DynamoDB local in future labs
We can bring them in as containers and reference them externally.

Lets integrate the following into our existing docker compose file:

### Postgres
Add postgres as a service to the docker-compose.yml file after frontend-react-js:

```yaml
services:
  db:
    image: postgres:13-alpine
    restart: always
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - '5432:5432'
    volumes: 
      - db:/var/lib/postgresql/data
volumes:
  db:
    driver: local
```

To install the postgres client into Gitpod, add the code below to the gitpod.yml file:

```sh
  - name: postgres
    init: |
      curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
      echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |sudo tee  /etc/apt/sources.list.d/pgdg.list
      sudo apt update
      sudo apt install -y postgresql-client-13 libpq-dev
```

### DynamoDB Local
Add DynamoDB as a service to the docker-compose.yml file after postgres:
```yaml
services:
  dynamodb-local:
    # https://stackoverflow.com/questions/67533058/persist-local-dynamodb-data-in-volumes-lack-permission-unable-to-open-databa
    # We needed to add user:root to get this working.
    user: root
    command: "-jar DynamoDBLocal.jar -sharedDb -dbPath ./data"
    image: "amazon/dynamodb-local:latest"
    container_name: dynamodb-local
    ports:
      - "8000:8000"
    volumes:
      - "./docker/dynamodb:/home/dynamodblocal/data"
    working_dir: /home/dynamodblocal
```

Example of using DynamoDB local
https://github.com/100DaysOfCloud/challenge-dynamodb-local


## Open-API

### Document the Notification Endpoint for the OpenAPI Document, Write a Flask Backend Endpoint for Notifications, and Write a React Page for Notifications
In this task, we created the openapi-3.0.yml file as a standard for defining APIs. The API is providing us with mock data, as there's currently no database hooked to the backend. 

[Open API](https://dash.readme.com/)

[Open API Initiative Registry](https://spec.openapis.org/)
> To understand the Open Api file in: 'backend-flask/openapi-3.0.yml'; 
  visit the link above.

We added a new section to the Open Api file at line 150 directly after:
```yml 
  $ref: '#/components/schemas/Message'
```
The section to add is as below:

```yml
  /api/activities/notifications:
    get:
      description: 'Return a feed of activity for all of those that I follow'
      tags:
        - activities
      parameters: []
      responses:
        '200':
          description: Returns an array of activities
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Activity'
```

To write a Flask Backend Endpoint for Notifications, we selected the 'app.py' file in 'backend-flask' and added the following to create a micro service:
At Line 7 add:

```Python

from services.notifications_activities import * 

```
Define a route for the notifications endpoint in the Flask app:
Line 68, after: 
```python
  @app.route("/api/activities/home"
```
...insert the code code below:

```Python
@app.route("/api/activities/notifications", methods=['GET'])
def data_notifications():
  data = NotificationsActivities.run()
  return data, 200
```
In 'backend-flask/services' we defined the micro service notifications_activites.py:

```Python
from datetime import datetime, timedelta, timezone
class NotificationsActivities:
  def run():
    now = datetime.now(timezone.utc).astimezone()
    results = [{
      'uuid': '68f126b0-1ceb-4a33-88be-d90fa7109eee',
      'handle':  'coco',
      'message': 'I am white unicorn',
      'created_at': (now - timedelta(days=2)).isoformat(),
      'expires_at': (now + timedelta(days=5)).isoformat(),
      'likes_count': 5,
      'replies_count': 1,
      'reposts_count': 0,
      'replies': [{
        'uuid': '26e12864-1c26-5c3a-9658-97a10f8fea67',
        'reply_to_activity_uuid': '68f126b0-1ceb-4a33-88be-d90fa7109eee',
        'handle':  'Worf',
        'message': 'This post has no honor!',
        'likes_count': 0,
        'replies_count': 0,
        'reposts_count': 0,
        'created_at': (now - timedelta(days=2)).isoformat()
      }],
    },
    ]
    return results
```

For the Frontend, to implement the notifications tab, we went to the frontend-react-js folder>src. We accessed App.js, and added something new to import at line 4:

```Javascript
import NotificationsFeedPage from './pages/NotificationsFeedPage';
```

Line 23 - Using react-router, we added a new path for the element:

```Javascript
  {
    path: "/notifications",
    element: <NotificationsFeedPage />
  },
```

Then under 'frontend-react-js/src/pages', we created the pages NotificationsFeedPage.js and NotificationsFeedPage.css.
Add the code below to 'NotificationsFeedPage.js':

```Javascript
import './NotificationsFeedPage.css';
import React from "react";

import DesktopNavigation  from '../components/DesktopNavigation';
import DesktopSidebar     from '../components/DesktopSidebar';
import ActivityFeed from '../components/ActivityFeed';
import ActivityForm from '../components/ActivityForm';
import ReplyForm from '../components/ReplyForm';

// [TODO] Authenication
import Cookies from 'js-cookie'

export default function NotificationsFeedPage() {
  const [activities, setActivities] = React.useState([]);
  const [popped, setPopped] = React.useState(false);
  const [poppedReply, setPoppedReply] = React.useState(false);
  const [replyActivity, setReplyActivity] = React.useState({});
  const [user, setUser] = React.useState(null);
  const dataFetchedRef = React.useRef(false);

  const loadData = async () => {
    try {
      const backend_url = `${process.env.REACT_APP_BACKEND_URL}/api/activities/notifications`
      const res = await fetch(backend_url, {
        method: "GET"
      });
      let resJson = await res.json();
      if (res.status === 200) {
        setActivities(resJson)
      } else {
        console.log(res)
      }
    } catch (err) {
      console.log(err);
    }
  };

  const checkAuth = async () => {
    console.log('checkAuth')
    // [TODO] Authenication
    if (Cookies.get('user.logged_in')) {
      setUser({
        display_name: Cookies.get('user.name'),
        handle: Cookies.get('user.username')
      })
    }
  };

  React.useEffect(()=>{
    //prevents double call
    if (dataFetchedRef.current) return;
    dataFetchedRef.current = true;

    loadData();
    checkAuth();
  }, [])

  return (
    <article>
      <DesktopNavigation user={user} active={'notifications'} setPopped={setPopped} />
      <div className='content'>
        <ActivityForm  
          popped={popped}
          setPopped={setPopped} 
          setActivities={setActivities} 
        />
        <ReplyForm 
          activity={replyActivity} 
          popped={poppedReply} 
          setPopped={setPoppedReply} 
          setActivities={setActivities} 
          activities={activities} 
        />
        <ActivityFeed 
          title="Notifications" 
          setReplyActivity={setReplyActivity} 
          setPopped={setPoppedReply} 
          activities={activities} 
        />
      </div>
      <DesktopSidebar user={user} />
    </article>
  );
}
```


Then at the bottom of the docker-compose.yml file, we added the rest of the Postgress code for the volumes:

```yml
volumes:
  db:
    driver: local
```



To test your local DynamoDB orchestration run:
## Run Docker Local

```
docker-compose up
```

## Create a table

```sh
aws dynamodb create-table \
    --endpoint-url http://localhost:8000 \
    --table-name Music \
    --attribute-definitions \
        AttributeName=Artist,AttributeType=S \
        AttributeName=SongTitle,AttributeType=S \
    --key-schema AttributeName=Artist,KeyType=HASH AttributeName=SongTitle,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
    --table-class STANDARD
```

## Create an Item

```sh
aws dynamodb put-item \
    --endpoint-url http://localhost:8000 \
    --table-name Music \
    --item \
        '{"Artist": {"S": "No One You Know"}, "SongTitle": {"S": "Call Me Today"}, "AlbumTitle": {"S": "Somewhat Famous"}}' \
    --return-consumed-capacity TOTAL  
```

## List Tables

```sh
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

## Get Records

```sh
aws dynamodb scan --table-name Music --query "Items" --endpoint-url http://localhost:8000
```


To add Postgres as a dependency that installs on startup, add the code below in the '.gitpod.yml' file:
Place it under the vs-code extensions,
```yml
    - cweijan.vscode-mysql-client2
```

Make sure to install postgres via the terminal, run:
```sh
      curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
      echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |sudo tee  /etc/apt/sources.list.d/pgdg.list
      sudo apt update
      sudo apt install -y postgresql-client-13 libpq-dev
```

To test the postgres installation run the code below:
```sh
psql -Upostgres --host localhost
Press Enter once asked for a password or input 'password'
```

## Extra

Implement a healthcheck in the Docker compose file --> 'docker-compose.yml' :
```yaml
    healthcheck:
      test: curl --fail http://localhost || exit 1
      interval: 60s
      retries: 5
      start_period: 20s
      timeout: 10s
```

- [PostGres useful tips - CLI](https://www.prisma.io/dataguide/postgresql/setting-up-a-local-postgresql-database#setting-up-postgresql-on-linux)

Hardcoded pass for cruddur users = 1234

## Save the work on its own branch named "week-1"
```sh
cd aws-bootcamp-cruddur-2024
git checkout -b week-1
```
<hr/>

## Commit
Add the changes and create a commit named: "App Containerization"
```sh
git add .
git commit -m "App Containerization"
```
Push your changes to the branch
```sh
git push origin week-1
```
<hr/>

### Tag the commit
```sh
git tag -a week-1 -m "Setting up App Containerization"
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
git merge week-1
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

