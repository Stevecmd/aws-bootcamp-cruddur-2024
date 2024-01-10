# Week 1 — App Containerization

### Add Dockerfile

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
To start the container run the code below in the terminal:
```sh
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]
```
Upon visiting your gitpod backend port link and appending '/api/activities/home' you should see some json output. 
1 hr mark on week 1 video
Unset the env vars below
```sh
unset FRONTEND_URL
unset BACKEND_URL
```
Confirm that they are unset:
```sh
env | grep FRONTEND_URL
env | grep BACKEND_URL
```
cd into the project directory 'aws-bootcamp-cruddur- 2024'

### Build Container

```sh
docker build -t  backend-flask ./backend-flask
```

* Make sure that the image builds succesfully

```sh
docker run --rm -p 4567:4567 -it -e FRONTEND_URL='*' -e BACKEND_URL='*' backend-flask
```
On the terminal set the env vars:
```sh
set FRONTEND_URL="*"
set BACKEND_URL="*"
```

Run the container
```sh
docker run --rm -p 4567:4567 -it -e FRONTEND_URL='*' -e BACKEND_URL='*' -d backend-flask
```
Visit the port link and make sure to append '/api/activities/home', you should get Javascript response.

On gitpod open a new terminal and run the code below to see the running docker containers:
```sh
  docker ps
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
If the website does not have some mockposts or any other error, check the website logs to endure there are no errors such as 'CORS'

## Adding DynamoDB Local and Postgres

We are going to use Postgres and DynamoDB local in future labs
We can bring them in as containers and reference them externally

Lets integrate the following into our existing docker compose file:

### Postgres

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

To install the postgres client into Gitpod

```sh
  - name: postgres
    init: |
      curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
      echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |sudo tee  /etc/apt/sources.list.d/pgdg.list
      sudo apt update
      sudo apt install -y postgresql-client-13 libpq-dev
```

### DynamoDB Local

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
