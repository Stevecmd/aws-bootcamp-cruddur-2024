# Week 4 — Postgres and RDS

**Set up RDS Instance**

* Run the following code in the CLI: <br>
Make sure to change the name(**identifier**), password and zone.
 **NB** The version below enables enhanced monitoring which may increase spend <br/>
```
aws rds create-db-instance \
  --db-instance-identifier cruddur-db-instance \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version  14.6 \
  --master-username root \
  --master-user-password goodDatabasePassword1 \
  --allocated-storage 20 \
  --availability-zone us-east-1a \
  --backup-retention-period 0 \
  --port 5432 \
  --no-multi-az \
  --db-name cruddur \
  --storage-type gp2 \
  --publicly-accessible \
  --storage-encrypted \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --no-deletion-protection
```
Below is a version without enhanced monitoring:
```
aws rds create-db-instance \
  --db-instance-identifier cruddur-db-instance \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 14.6 \
  --master-username root \
  --master-user-password goodDatabasePassword1 \
  --allocated-storage 20 \
  --availability-zone us-east-1a \
  --backup-retention-period 0 \
  --port 5432 \
  --no-multi-az \
  --db-name cruddur \
  --storage-type gp2 \
  --publicly-accessible \
  --storage-encrypted \
  --no-deletion-protection
```
Once the commands run, confirm creation on the web interface.
Postgres should already be setup but check `docker-compose.yml` to confirm that the following code exists:
```
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
```
**Tip**: Comment out DynamoDB as it is not necessary atm:
```
  #dynamodb-local:
    ## https://stackoverflow.com/questions/67533058/persist-local-dynamodb-data-in-volumes-lack-permission-unable-to-open-databa
    ## We needed to add user:root to get this working.
    #user: root
    #command: "-jar DynamoDBLocal.jar -sharedDb -dbPath ./data"
    #image: "amazon/dynamodb-local:latest"
    #container_name: dynamodb-local
   # ports:
      #- "8000:8000"
   # volumes:
     # - "./docker/dynamodb:/home/dynamodblocal/data"
    #working_dir: /home/dynamodblocal
```
Once RDS is running, stop it temporarily using the Console.
<br>**NB** It will automatically restart after 7 days.

Run `docker-compose up` to check if we can connect to Postgres. <br>
On Gitpod, Check if the Postgres container is running.

Connect to Postgres locally, using the command below:

```
psql -U postgres --host localhost
```
When prompted for the password, the default is 'password'.

* Common PSQL Commands:

```sql
\x on -- expanded display when looking at data
\q -- Quit PSQL
\l -- List all databases
\c database_name -- Connect to a specific database
\dt -- List all tables in the current database
\d table_name -- Describe a specific table
\du -- List all users and their roles
\dn -- List all schemas in the current database
CREATE DATABASE database_name; -- Create a new database
DROP DATABASE database_name; -- Delete a database
CREATE TABLE table_name (column1 datatype1, column2 datatype2, ...); -- Create a new table
DROP TABLE table_name; -- Delete a table
SELECT column1, column2, ... FROM table_name WHERE condition; -- Select data from a table
INSERT INTO table_name (column1, column2, ...) VALUES (value1, value2, ...); -- Insert data into a table
UPDATE table_name SET column1 = value1, column2 = value2, ... WHERE condition; -- Update data in a table
DELETE FROM table_name WHERE condition; -- Delete data from a table
```

#### PSQL Database

Once we are logged into the local PSQL database, we create a database named `cruddur` using the command below. 

```sql
CREATE database cruddur;
```
Type `\l` to confirm that the database has been created.
In `backend-flask`, create a folder called `db` and inside create a file `schema.sql`
and insert the following code into the it.

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```
**NB** `UUID` - Universally unique identifiers.

exit from the psql command by typing the following command:
```
exit 
```
or
```
\q
```

After this, from the `postgres:bash` terminal, in the directory `aws-bootcamp-cruddur-2024/backend-flask` run 
the code below, input pasword as: `password`. 
<br>

```
psql cruddur < db/schema.sql -h localhost -U postgres
```

<br>
This created the extension needed. 

To make doing this easier, we created a `connection url string` to provide all the details that are needed to connect to our database. <br>
Make sure to replace '<password>' with your actual password for the postgres DB. <br>
**NB**:  Our local username is `postgres`.

<br>
The format for a connection url string for a Postgres database is the following: 

```
postgresql://[user[:password]@][netlocation][:port][/dbname][?parameter1=value1]
```

Input your password and test the connection:
```
psql postgresql://postgres:<password>@localhost:5432/cruddur
```
In my case the command was:
```
psql postgresql://postgres:password@localhost:5432/cruddur
```
If it connects then the code is valid, exit out `\q` and edit the code below by entering your password and run it:
```
export CONNECTION_URL="postgresql://postgres:<password>@localhost:5432/cruddur"
gp env CONNECTION_URL="postgresql://postgres:<password>@localhost:5432/cruddur"
```
test the connection by running:
```
psql $CONNECTION_URL
```

We then create a connection url string for our production RDS database as well, then set the environment variable there too. <br>
In the code below, retrieve the endpoint and port from the console on `RDS` > `Databases` > `Connectivity and security`.
Replace `goodDatabasePassword1` with your actual `password` to be used in Production(RDS). Also replace `cruddur-db-instance.c8ersdfsdf.us-east-1.rds.amazonaws.com` with your endpoint connection details.
```
export PROD_CONNECTION_URL="postgresql://root:goodDatabasePassword1@cruddur-db-instance.c8ersdfsdf.us-east-1.rds.amazonaws.com:5432/cruddur"
gp env PROD_CONNECTION_URL="postgresql://root:goodDatabasePassword1@cruddur-db-instance.c8ersdfsdf.us-east-1.rds.amazonaws.com:5432/cruddur"
```

## Bash scripting for common database actions

We then created a new folder in 'backend-flask' named 'bin' which stands for binary. <br> 
In this folder, we can store bash scripts to execute commands on our database. <br> 
We then made several new files: `db-create`, `db-drop`, `db-schema-load`.

For each of the files add a shebang to instruct our app to treat the file as a bash script:

```
#! /user/bin/bash
```
From the `Backend-flask` folder, make our new files executable by running `chmod u+x bin/db-create`, `chmod u+x bin/db-drop`, `chmod u+x bin/db-schema-load`
<br>
We started off testing if we can drop our database. To do this, add the code below to `db-drop`.

```
psql $CONNECTION_URL -c "drop database cruddur";
```

This command should psql connect to our local Postgres database using our connection string url, then using `-c` it issues a SQL command of `drop database cruddur;`

<br>
Proceed to edit the files as follows:

> DB-create
```
#! /usr/bin/bash

echo "db-create"

NO_DB_CONNECTION_URL=$(sed 's/\/cruddur//g' <<<"$CONNECTION_URL")
psql $NO_DB_CONNECTION_URL -c "CREATE database cruddur;"
```
> DB-Drop
```
#! /usr/bin/bash

echo "db-drop"

NO_DB_CONNECTION_URL=$(sed 's/\/cruddur//g' <<<"$CONNECTION_URL")
psql $NO_DB_CONNECTION_URL -c "DROP database cruddur;"
```

> DB-Schema-load

```
#! /usr/bin/bash

echo "db-schema-load"

schema_path="$(realpath .)/db/schema.sql"
echo $schema_path

psql $CONNECTION_URL cruddur < $schema_path
```
To execute a file run:
`./bin/<file-name>' eg './bin/db-create`

We need a way to determine when we're running from our production environment (prod) or our local Postgres environment. <br>
To do this, we added an if statement to the code.
Below is the modified code for `schema-load`.
```
#! /usr/bin/bash

#echo "== db-schema-load"
CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-schema-load"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

schema_path="$(realpath .)/db/schema.sql"

echo $schema_path

if [ "$1" = "prod" ]; then
  echo "Running in production mode"
  URL=$PROD_CONNECTION_URL
else
  URL=$CONNECTION_URL
fi

psql $URL cruddur < $schema_path
```

The additional code under our shebang customizes the color when viewing our Postgres logs through the CLI. <br>
Add it to the other bash scripts as well. 

Back to adding tables to our database, we go back to our `schema.sql`, and add SQL commands to create our tables and activities:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.activities;


CREATE TABLE public.users (
  uuid UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  display_name text,
  handle text,
  cognito_user_id text,
  created_at TIMESTAMP default current_timestamp NOT NULL
);

CREATE TABLE public.activities (
  uuid UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_uuid UUID NOT NULL,
  message text NOT NULL,
  replies_count integer DEFAULT 0,
  reposts_count integer DEFAULT 0,
  likes_count integer DEFAULT 0,
  reply_to_activity_uuid integer,
  expires_at TIMESTAMP,
  created_at TIMESTAMP default current_timestamp NOT NULL
);
```
### `./bin/db-connect` to connect to our DB
We then made a new bash script named `db-connect` inside the bin folder `./bin/db-connect`, made it executable by running `chmod u+x ./bin/db-connect` then run the file. 
<br>

The file contains:
```sh
#! /usr/bin/bash

if [ "$1" = "prod" ]; then
  echo "Running in production mode"
  URL=$PROD_CONNECTION_URL
else
  URL=$CONNECTION_URL
fi

psql $URL
```

You should be able to successfully connect to the local Postgres database using this bash script. <br>
Run `\dt` from the Postgres database to view the tables.

### `./bin/db-create` to create a new table 'cruddur'
```
#! /usr/bin/bash

#echo "== db-create"
CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-create"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

NO_DB_CONNECTION_URL=$(sed 's/\/cruddur//g' <<<"$CONNECTION_URL")
psql $NO_DB_CONNECTION_URL -c "CREATE database cruddur;"
```

### `./bin/db-drop` to delete an existing table:
```
#! /usr/bin/bash

#echo "== db-drop"
CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-drop"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

NO_DB_CONNECTION_URL=$(sed 's/\/cruddur//g' <<<"$CONNECTION_URL")
psql $NO_DB_CONNECTION_URL -c "DROP DATABSE IF EXISTS cruddur;"
```

### `./bin/db-schema-load` to load the schema:
```
#! /usr/bin/bash

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-schema-load"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

schema_path="$(realpath .)/db/schema.sql"
echo $schema_path

if [ "$1" = "prod" ]; then
  echo "Running in production mode"
  URL=$PROD_CONNECTION_URL
else
  URL=$CONNECTION_URL
fi

psql $URL cruddur < $schema_path
```
**NB** 
- '$(realpath .)' is used to get the actual path of a specified file.
- For example the code below reveals the path of `schema.sql`
```
schema_path="$(realpath .)/db/schema.sql"
echo $schema_path
```
- To print colors in Bash we use codes for example: `'\033[1;36m'`
  
### `./bin/db-seed` to insert the data into schema loaded:
```
#! /usr/bin/bash

#echo "== db-seed"
CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-seed"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

seed_path="$(realpath .)/db/seed.sql"

echo $seed_path

psql $CONNECTION_URL cruddur < $seed_path

```
This db-seed script will run `seed.sql` file. Create it in `backend-flask/db` and input: 

```sql
-- this file was manually created
INSERT INTO public.users (display_name, handle, cognito_user_id)
VALUES
  ('Andrew Brown', 'andrewbrown' ,'MOCK'),
  ('Andrew Bayko', 'bayko' ,'MOCK');

INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = 'andrewbrown' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  )
```

### `./bin/db-update-sg-rule` to setup our Security groups to access our RDS database:
```sh
#! /usr/bin/bash

aws ec2 modify-security-group-rules \
    --group-id $DB_SG_ID \
    --security-group-rules "SecurityGroupRuleId=$DB_SG_RULE_ID,SecurityGroupRule={IpProtocol=tcp,FromPort=5432,ToPort=5432,CidrIpv4=$GITPOD_IP/32}"
```
Remember to make the files executable:
```sh
chmod u+x bin/db-seed
chmod u+x bin/db-update-sg-rule 
```

To connect to the `PROD` environment, you can affix the command with PROD to the scripts eg. `./bin/db-connect prod`


## Install Postgres Driver in Backend Application
### db-sessions
We may need to see which connections are running on our Postgres database in order to perform some actions eg `db-drop`.
<br>
For this, we implement `db-sessions` and make it executable. <br>
Create a file called `db-sessions` under `backend-flask/bin`

```sh
#! /usr/bin/bash
CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-sessions"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

if [ "$1" = "prod" ]; then
  echo "Running in production mode"
  URL=$PROD_CONNECTION_URL
else
  URL=$CONNECTION_URL
fi

NO_DB_URL=$(sed 's/\/cruddur//g' <<<"$URL")
psql $NO_DB_URL -c "select pid as process_id, \
       usename as user,  \
       datname as db, \
       client_addr, \
       application_name as app,\
       state \
from pg_stat_activity;"
```
```sh
 chmod u+x ./db-sessions
```

Run this, to see the active connections to the database, and close unnecessary connections. 

We then create a script to run all of our commands, so that we don't have to run them individually. We create `db-setup` and made it executable.

### db-setup
```sh
#! /usr/bin/bash
-e # stop if it fails at any point

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-setup"
printf "${CYAN}==== ${LABEL}${NO_COLOR}\n"

bin_path="$(realpath .)/bin"

source "$bin_path/db-drop"
source "$bin_path/db-create"
source "$bin_path/db-schema-load"
source "$bin_path/db-seed"
```
```sh
 chmod u+x ./db-setup
```
## Install the Postgres Driver
With the foregoing setup, we can now install the Postgres driver in our Backend application. <br> 
We're going to use a AWS Lambda to to insert users into our database. <br> 
We need to add PostgreSQL libraries as a dependency to run the Postgres driver and the `Psycopg2 C library for Python`. <br> 
To implement this, add the following libraries to the `backend-flask` >`requirements.txt` file. 

```py
psycopg[binary]
psycopg[pool]
```

Run `pip install -r requirements.txt` to install the drivers. <br>
Ref: `psycopg.org`

## Connect Gitpod to RDS Instance

We're going to have to use pooling as a way of dealing with connections to our database. There's a certain amount of connections your database can handle in relational databases. <br>
There's concurrent connections, where some are running, some aren't. These connection pools allow us to re-use connections with concurrent connections. <br>
Because we're running Lambda functions, if our app became widely popular, we'd need to use a proxy because Lambda functions create new functions each time they run, which could become **expensive**.

To create our connection pool, we create a new file in `backend-flask/lib` named `db.py`

```py
from psycopg_pool import ConnectionPool
import os

def query_wrap_object(template):
  sql = f"""
  (SELECT COALESCE(row_to_json(object_row),'{{}}'::json) FROM (
  {template}
  ) object_row);
  """
  return sql

def query_wrap_array(template):
  sql = f"""
  (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
  {template}
  ) array_row);  
  """   
  return sql

connection_url = os.getenv("CONNECTION_URL")  
pool = ConnectionPool(connection_url)
```

We open `docker-compose.yml` and add an environment variable for our `CONNECTION_URL` within `backend-flask` > `environment`.

```yml
      CONNECTION_URL: "${CONNECTION_URL}"
      # CONNECTION_URL: "postgresql://postgres:password@db:5432/cruddur"
```
If it doesnt work use the code below:
```yml
CONNECTION_URL: "postgresql://postgres:password@localhost:5432/cruddur"
```

Edit **home_activities.py** and import the connection pool, remove our mock data, and add our query to establish our connection. 

```py
from lib.db import pool, query_wrap_array #at line 4
```
Below is a sample SQL query that we can later run for home activities:
```sh
...........................

    sql = query_wrap_array("""
    SELECT
        activities.uuid,
        users.display_name,
        users.handle,
        activities.message,
        activities.replies_count,
        activities.reposts_count,
        activities.likes_count,
        activities.reply_to_activity_uuid,
        activities.expires_at,
        activities.created_at
      FROM public.activities
      LEFT JOIN public.users ON users.uuid = activities.user_uuid
      ORDER BY activities.created_at DESC
    """)
    print("SQL=========")    
    print(sql)
    print("SQL+++++++++")       
    with pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(sql)
        # this will return a tuple
        # the first field being the data
        json = cur.fetchone()
    print("---------") 
    print(json[0])      
    return json[0]   
    return results

```
This will fetch the data and return the results. Since we're writing raw SQL, this will allows us to return json directly as well. 

After working through some SQL errors, we pointed our attention back towards RDS. We spin up our RDS database, then test connecting to it using the terminal.

```sh
echo $PROD_CONNECTION_URL # To see whether the connection details are set
psql $PROD_CONNECTION_URL # Connecting to RDS
```
If it isnt set:
```
export PROD_CONNECTION_URL="postgresql://cruddurroot:<RDSdatabasepassword>@cruddur-db-instance.<unique-db-identifier>.us-east-1.rds.amazonaws.com:5432/cruddur"
gp env PROD_CONNECTION_URL="postgresql://cruddurroot:<RDSdatabasepassword>@cruddur-db-instance.<unique-db-identifier>.us-east-1.rds.amazonaws.com:5432/cruddur"
```
confirm the env vars:
```
env | grep PROD
```
You may test out connecting to the DB:
```
psql $CONNECTION_URL #works
```
### Production connection:

From the terminal, we run `curl ifconfig.me` which outputs our Gitpod IP address. Next we pass `GITPOD_IP=$(curl ifconfig.me)` as variable so that we can grab the GITPOD_IP and connect to RDS. <br>
Confirm this by running:
```
echo $GITPOD_IP
```

Test the `psql` connection, this time it should work. <br>

Production connection:
```
psql $PROD_CONNECTION_URL #will not work because of Security group rules are not set
```
On the console, create the relevant security group/s and take note of their ID's. Ideally it should be one security group that allows connections to `POSTGRES` from your gitpod IP and or your computer. <br>

There is no problem if you modify the default `SG` or create your own, simply take note of its `ID` and `rule-id`. 
 
In the CLI set the env variables of the `security group id` and `security group rule id` as variables: `DB_SG_ID` and `DB_SG_RULE_ID`

```sh
export DB_SG_ID="<sg-12345>"
gp env DB_SG_ID="<sg-12345>"
export DB_SG_RULE_ID="<sgr-12345>"
gp env DB_SG_RULE_ID="<sgr-12345>"
```
The script below can be used on the terminal to test the connection to RDS and whether the security group is being modified appropriately:

```sh
aws ec2 modify-security-group-rules \
    --group-id $DB_SG_ID \
    --security-group-rules "SecurityGroupRuleId=$DB_SG_RULE_ID,SecurityGroupRule={Description=GITPOD,IpProtocol=tcp,FromPort=5432,ToPort=5432,CidrIpv4=$GITPOD_IP/32}"
```

Because the IP address changes on Gitpod restart, we need to change the ip on the security group of the rds instance, below is the script to be run to handle this, save it to `backend-flask` > `bin` > `rds-update-sg-rule`:
```py
#! /usr/bin/bash

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="rds-update-sg-rule"
printf "${CYAN}==== ${LABEL}${NO_COLOR}\n"

aws ec2 modify-security-group-rules \
    --group-id $DB_SG_ID \
    --security-group-rules "SecurityGroupRuleId=$DB_SG_RULE_ID,SecurityGroupRule={Description=GITPOD,IpProtocol=tcp,FromPort=5432,ToPort=5432,CidrIpv4=$GITPOD_IP/32}"
```
Make the file executable:
```
chmod u+x bin/db/rds/update-sg-rule
```
From with `backend-flask` run the file:
```
./bin/db/rds/update-sg-rule
```
In case of an error, execute the code below and rerun the script above:
`export GITPOD_IP=$(curl ifconfig.me)` 
<br>

We also store our env var in `.gitpod.yml` as well as program `rds-update-sg-rule` to run every time our environment launches:

```yml
  - name: postgres
    init: |
      curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
      echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |sudo tee  /etc/apt/sources.list.d/pgdg.list
      sudo apt update
      sudo apt install -y postgresql-client-13 libpq-dev      
      sudo apt install -y postgresql-client-13 libpq-dev  
    command: |
      export GITPOD_IP=$(curl ifconfig.me)
      source  "$THEIA_WORKSPACE_ROOT/backend-flask/bin/rds-update-sg-rule" 
```
Confirm settings by restarting gitpod and running:
```
cd backend-flask
./bin/db/connect prod
```
You should get the message:
```
Running in production mode
psql
```
Type the code below to quit the psql connection:
```
\q
```

After confirming connection to RDS from Gitpod, modify `docker-compose.yml` to use production env vars for PROD_CONNECTION_URL. 

```yml
CONNECTION_URL: "${PROD_CONNECTION_URL}"
```
Load your schema to the database:
```
./bin/db/schema-load
```
After the table is created, if you visit Logs you should get a status `200` code. <br>
The website will still be empty because there is no data in the database.

# Create Lambda
Create a lambda in the region where your services. <br>
Create the file `cruddur-post-confirmation.py` within the folder `aws/lambdas`

```py
import json
import psycopg2

def lambda_handler(event, context):
    user = event['request']['userAttributes']
    print('userAttributes')
    print(user)

    user_display_name = user['name']
    user_email        = user['email']
    user_handle       = user['preferred_username']
    user_cognito_id   = user['sub']
    try:
        conn = psycopg2.connect(os.getenv('CONNECTION_URL'))
        cur = conn.cursor()
        sql = f"""
            "INSERT INTO users (
                display_name,
                email,
                handle,
                cognito_user_id
            ) 
            VALUES(
                {user_display_name},
                {user_email},
                {user_handle},
                {user_cognito_id}
            )"
        """            
        cur.execute(sql)
        conn.commit() 

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            cur.close()
            conn.close()
            print('Database connection closed.')

    return event
```

The env var for the lambda will be **CONNECTION_URL** which has the variable of the **PROD_CONNECTION_URL** set on gitpod/codespace example: `PROD_CONNECTION_URL="postgresql://userofthedb:masterpassword@endpointofthedb:5432/cruddur"`
<br/>
**Considerations**
If this was an actual production website, in anticipation of lots of traffic we would need to use a `lambda proxy` in order to avoid the users flooding the connection but this incurs an additional cost and is complex to implement. To keep the project costs low, I am not using a connection pool. <br/> 
**Tip** The above lambda can be run directly in the lambda console. Configure the env vars and deploy when done. <br/>
Env vars:
`CONNECTION_URL`: `postgresql://userofthedb:masterpassword@endpointofthedb:5432/cruddur` <br/>

Go to the Lambda layers and add a layer with reference to the arn below:
```
arn:aws:lambda:us-east-1:898466741470:layer:psycopg2-py38:1
```

## Create Cognito Pool and Lambda trigger.

From the Cognito console, select the user pool and go to the `User pool properties` to add a lambda trigger. 
```
Trigger type: Sign-up
Sign-up: Post confirmation trigger
Lambda function: cruddur-post-confirmation
Add Lambda trigger
```

Add a policy to the Lambda by creating a new one.
```json
{
  "Version": "2012-10-17",
  "Statement": [{
      "Effect": "Allow",
      "Actions": [
          "ec2:DescribeNetworkInterface",
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeInstances",
          "ec2:AttachNetworkInterface",
      ],
      "Resource": "*"
  }]
}
```

Name: **AWSLambdaVPCAccessExecutionRole** <br>
Description: Enable AWS Lambda to create a Network connection. <br>

Make sure to go to the lambda created and attach the following policy created >> `configuration` > `permission` > `Role name` > `Attach policy`. <br>

Once you attach the policy, on the left hand side of the page select `VPC` and: 
- select the VPC where RDS resides,
- the subnet mask (select atleast two) and
- select the same security group of the rds(default).
- Save

In the terminal run:
```
./bin/db/schema-load prod
```

Go back to the website and register a new user then sign in -- investigate user registration on the terminal. <br>
`./bin/db/connect prod`
Once connected run:
```
\dt #should show the tables
select * from users; #should show registered users
```
**NB** Cloudwatch can now be used to check for logs/errors.  <br>
To save on RDS spend, stop it temporarily.
<br>

## Creating Activities
Edit the file 'backend-flask' > 'services' > `create_activity.py`
after 'class CreateActivity' insert the code below:
```
from datetime import datetime, timedelta, timezone
from lib.db import db

class CreateActivity:
  def run(message, user_handle, ttl):
    model = {
      'errors': None,
      'data': None
    }

    now = datetime.now(timezone.utc).astimezone()

    if (ttl == '30-days'):
      ttl_offset = timedelta(days=30) 
    elif (ttl == '7-days'):
      ttl_offset = timedelta(days=7) 
    elif (ttl == '3-days'):
      ttl_offset = timedelta(days=3) 
    elif (ttl == '1-day'):
      ttl_offset = timedelta(days=1) 
    elif (ttl == '12-hours'):
      ttl_offset = timedelta(hours=12) 
    elif (ttl == '3-hours'):
      ttl_offset = timedelta(hours=3) 
    elif (ttl == '1-hour'):
      ttl_offset = timedelta(hours=1) 
    else:
      model['errors'] = ['ttl_blank']

    if user_handle == None or len(user_handle) < 1:
      model['errors'] = ['user_handle_blank']

    if message == None or len(message) < 1:
      model['errors'] = ['message_blank'] 
    elif len(message) > 280:
      model['errors'] = ['message_exceed_max_chars'] 

    if model['errors']:
      model['data'] = {
        'handle':  user_handle,
        'message': message
      }   
    else:
      expires_at = (now + ttl_offset)
      uuid = CreateActivity.create_activity(user_handle, message, expires_at)
      
      object_json = CreateActivity.query_object_activity(uuid)
      
      model['data'] = object_json
    return model
  
  def create_activity(handle, message, expires_at):
    sql = db.template('activities','create')
    uuid = db.query_commit(sql,{ 
      'handle': handle, 
      'message': message, 
      'expires_at': expires_at
      })
    return uuid
  
  def query_object_activity(uuid):
    sql = db.template('activities','object')
    return db.query_object_json(sql,{ 
      'uuid': uuid
      })
```
Edit the file `backend-flask/lib/db.py` and add the function `print_sql_err`:
```
  def print_sql_err(self,err):
    # get details about the exception
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    line_num = traceback.tb_lineno

    # print the connect() error
    print ("\npsycopg ERROR:", err, "on line number:", line_num)
    print ("psycopg traceback:", traceback, "-- type:", err_type)

    # print the pgcode and pgerror exceptions
    print ("pgerror:", err.pgerror)
    print ("pgcode:", err.pgcode, "\n")

db = Db()
```
Add the function below to `db.py`:
```
def sql_execute
```
Edit the `create_activity.py` as follows:
```
import uuid
from datetime import datetime, timedelta, timezone

# from lib.db import db

class CreateActivity:
  def run(message, user_handle, ttl):
    model = {
      'errors': None,
      'data': None,
      'message': message
    }

    now = datetime.now(timezone.utc).astimezone()

    if (ttl == '30-days'):
      ttl_offset = timedelta(days=30) 
    elif (ttl == '7-days'):
      ttl_offset = timedelta(days=7) 
    elif (ttl == '3-days'):
      ttl_offset = timedelta(days=3) 
    elif (ttl == '1-day'):
      ttl_offset = timedelta(days=1) 
    elif (ttl == '12-hours'):
      ttl_offset = timedelta(hours=12) 
    elif (ttl == '3-hours'):
      ttl_offset = timedelta(hours=3) 
    elif (ttl == '1-hour'):
      ttl_offset = timedelta(hours=1) 
    else:
      model['errors'] = ['ttl_blank']

    if user_handle == None or len(user_handle) < 1:
      model['errors'] = ['user_handle_blank']

    if message == None or len(message) < 1:
      model['errors'] = ['message_blank'] 
    elif len(message) > 280:
      model['errors'] = ['message_exceed_max_chars'] 

    if model['errors']:
      model['data'] = {
        'handle':  user_handle,
        'message': message
      }   
    else:
      self.create_activity()
      model['data'] = {
        'uuid': uuid.uuid4(),
        'display_name': 'Andrew Brown',
        'handle':  user_handle,
        'message': message,
        'created_at': now.isoformat(),
        'expires_at': (now + ttl_offset).isoformat()
      }
    return model
  def create_activity(user_uuid, message, expires_at):
    sql = f"""
    INSERT INTO (
      user_uuid,
      message,
      expires_at
    )
    VALUES (
      "{user_uuid}",
      "{message}",
      "{expires_at}"
    )
    """
    #query_commit(sql)
```

The full `db.py` file will contain:
```
from psycopg_pool import ConnectionPool
import os
import re
import sys
from flask import current_app as app

class Db: #using a constructor to create an instance of the class
  def __init__(self):
    self.init_pool()

  def template(self,*args):
    pathing = list((app.root_path,'db','sql',) + args)
    pathing[-1] = pathing[-1] + ".sql"

    template_path = os.path.join(*pathing)

    green = '\033[92m'
    no_color = '\033[0m'
    print("\n")
    print(f'{green} Load SQL Template: {template_path} {no_color}')

    with open(template_path, 'r') as f:
      template_content = f.read()
    return template_content

  def init_pool(self):
    connection_url = os.getenv("CONNECTION_URL")
    self.pool = ConnectionPool(connection_url)
  # when we want to commit data such as an insert
  # be sure to check for RETURNING in all uppercases
  def print_params(self,params):
    blue = '\033[94m'
    no_color = '\033[0m'
    print(f'{blue} SQL Params:{no_color}')
    for key, value in params.items():
      print(key, ":", value)

  def print_sql(self,title,sql,params={}):
    cyan = '\033[96m'
    no_color = '\033[0m'
    print(f'{cyan} SQL STATEMENT-[{title}]------{no_color}')
    print(sql,params) # Get richer data when we print out the values
  def query_commit(self,sql,params={}):
    self.print_sql('commit with returning',sql,params)

    pattern = r"\bRETURNING\b"
    is_returning_id = re.search(pattern, sql)

    try:
      with self.pool.connection() as conn:
        cur =  conn.cursor()
        cur.execute(sql,params)
        if is_returning_id:
          returning_id = cur.fetchone()[0]
        conn.commit() 
        if is_returning_id:
          return returning_id
    except Exception as err:
      self.print_sql_err(err)
  # when we want to return a json object
  def query_array_json(self,sql,params={}):
    self.print_sql('array',sql,params)

    wrapped_sql = self.query_wrap_array(sql)
    with self.pool.connection() as conn:
      with conn.cursor() as cur:  
        cur.execute(wrapped_sql,params)
        json = cur.fetchone()
        return json[0]
  # When we want to return an array of json objects
  def query_object_json(self,sql,params={}):

    self.print_sql('json',sql,params)
    self.print_params(params)
    wrapped_sql = self.query_wrap_object(sql)

    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(wrapped_sql,params)
        json = cur.fetchone()
        if json == None:
          "{}"
          return "{}"
        else:
          return json[0]
  def query_value(self,sql,params={}):
    self.print_sql('value',sql,params)
    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(sql,params)
        json = cur.fetchone() # Runs execute and fetch only one item from the DB
        return json[0]
  def query_wrap_object(self,template):
    sql = f"""
    (SELECT COALESCE(row_to_json(object_row),'{{}}'::json) FROM (
    {template}
    ) object_row);
    """
    return sql
  def query_wrap_array(self,template):
    sql = f"""
    (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
    {template}
    ) array_row);
    """
    return sql
  def print_sql_err(self,err):
    # get details about the exception
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    line_num = traceback.tb_lineno

    # print the connect() error
    print ("\npsycopg ERROR:", err, "on line number:", line_num)
    print ("psycopg traceback:", traceback, "-- type:", err_type)

    # print the pgcode and pgerror exceptions
    print ("pgerror:", err.pgerror)
    print ("pgcode:", err.pgcode, "\n")

db = Db()
```
Edit 'home_activities.py':
```
# from lib.db import pool, query_wrap_array
from lib.db import db
```

Create the following files in: 'backend-flask' > 'db' > 'sql' > 'activities' and place the following code in it:
'create.sql':
```python
INSERT INTO public.activities (
  user_uuid,
  message,
  expires_at
)
VALUES (
  (SELECT uuid 
    FROM public.users 
    WHERE users.handle = %(handle)s
    LIMIT 1
  ),
  %(message)s,
  %(expires_at)s
) RETURNING uuid;
```
`home.sql`:
```py
SELECT
  activities.uuid,
  users.display_name,
  users.handle,
  activities.message,
  activities.replies_count,
  activities.reposts_count,
  activities.likes_count,
  activities.reply_to_activity_uuid,
  activities.expires_at,
  activities.created_at
FROM public.activities
LEFT JOIN public.users ON users.uuid = activities.user_uuid
ORDER BY activities.created_at DESC
```

`object.sql`:
```py
SELECT
  activities.uuid,
  users.display_name,
  users.handle,
  activities.message,
  activities.created_at,
  activities.expires_at
FROM public.activities
INNER JOIN public.users ON users.uuid = activities.user_uuid 
WHERE 
  activities.uuid = %(uuid)s
```

Edit **home_activities.py** as follows:
```py
from datetime import datetime, timedelta, timezone
from opentelemetry import trace

# from lib.db import pool, query_wrap_array
from lib.db import db

tracer = trace.get_tracer("home.activities")

class HomeActivities:
  #def run(Logger):
    #logger.info("HomeActivities")
  def run(cognito_user_id=None):
    with tracer.start_as_current_span("home-activities-mock-data"):
      span = trace.get_current_span()
      now = datetime.now(timezone.utc).astimezone()
      span.set_attribute("app.now", now.isoformat)

      # sql = query_wrap_array("""
      results = [{
        'uuid': '68f126b0-1ceb-4a33-88be-d90fa7109eee',
        'handle':  'Andrew Brown',
                'replies': []
      }
      ]
      if cognito_user_id != None:
        extra_crud = {
          'uuid': '248959df-3079-4947-b847-9e0892d1bab4',
          'handle':  'Lore',
          'message': 'My dear brother, it the humans that are the problem',
          'created_at': (now - timedelta(hours=1)).isoformat(),
          'expires_at': (now + timedelta(hours=12)).isoformat(),
          'likes': 1042,
          'replies': []
        }
        results.insert(0,extra_crud)

      span.set_attribute("app.result_length", len(results))
      return results

      
      
      
      
      
      
      
      
#       if param != None:
#         else:

#       results.insert(0,)
#       span.set_attribute("app.result_length", len(results))
#       return results
    

from datetime import datetime, timedelta, timezone
from opentelemetry import trace

from lib.db import db

#tracer = trace.get_tracer("home.activities")

class HomeActivities:
  def run(cognito_user_id=None):
    #logger.info("HomeActivities")
    #with tracer.start_as_current_span("home-activites-mock-data"):
    #  span = trace.get_current_span()
    #  now = datetime.now(timezone.utc).astimezone()
    #  span.set_attribute("app.now", now.isoformat())
    sql = db.template('activities','home')
    results = db.query_array_json(sql)
    return results
```

**Test** the app by posting a **CRUD**

## Save the work on its own branch named "week-4"
```sh
cd aws-bootcamp-cruddur-2024
git checkout -b week-4
```
<hr/>

## Commit
Add the changes and create a commit named: "Postgres and RDS"
```sh
git add .
git commit -m "Postgres and RDS"
```
Push your changes to the branch
```sh
git push origin week-4
```
<hr/>

### Tag the commit
```sh
git tag -a week-4 -m "Setting up Postgres and RDS"
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
git merge week-4
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
git branch -d week-4  # Deletes the local branch
git push origin --delete week-4  # Deletes the remote branch
```