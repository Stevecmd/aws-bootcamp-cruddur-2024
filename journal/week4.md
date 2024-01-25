# Week 4 — Postgres and RDS

**Set up RDS Instance**

* Run the following code in the CLI:
Make sure to change the name(**identifier**), password and zone.
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
Once the commands run, confirm creation on the web interface.

Postgres should already be setup but check 'docker-compose.yml' to confirm that the following code exists:
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
**Tip** Comment out DynamoDB as it is not necessary atm:
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
**NB** It will automatically restart after 7 days.

Do docker-compose up to check if we can connect to Postgres.
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

Once we are logged into the local PSQL database, we create a database named cruddur using the command below. 

```sql
CREATE database cruddur;
```
Type '\l' to confirm that the database has been created.
In 'backend-flask', create a folder called db and inside a file called 'schema.sql'
and insert the following code into the 'schema.sql'.

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```
**NB** UUID - universally unique identifiers

exit from the psql command by typing the following command:
```
\q
```

After this, from the postgres:bash terminal, in the root directory ie 'aws-bootcamp-cruddur-2024/backend-flask' run: 

```
psql cruddur < db/schema.sql -h localhost -U postgres
```
When asked for a pasword type: 'password'.

This created the extension needed. 

To make doing this easier, we created a 'connection url string' to provide all thed details that are needed to connect to our database.
Make sure to replace '<password>' with your actual password for the postgres DB.
**NB** Our local username is 'postgres'.

The format for a connection url string for a Postgres database is the following: 

```
postgresql://[user[:password]@][netlocation][:port][/dbname][?parameter1=value1]
```

test the connection by running:
```
psql postgresql://postgres:<password>@localhost:5432/cruddur
```
If it connects then the code is valid, exit out '\q' and run the code below:
```
export CONNECTION_URL="postgresql://postgres:<password>@localhost:5432/cruddur"
gp env CONNECTION_URL="postgresql://postgres:<password>@localhost:5432/cruddur"
```
test the connection by running:
```
psql $CONNECTION_URL
```

We then created a connection url string for our production RDS database as well, then set the environment variable there too.
In the code below, retrieve the endpoint and port from the console on 'RDS' > 'Databases' > 'Connectivity and security'.
Replace 'thisisntmyproductionpassword' with your actual password.
```
export PROD_CONNECTION_URL="postgresql://root:goodDatabasePassword1@cruddur-db-instance.c8ersdfsdf.us-east-1.rds.amazonaws.com:5432/cruddur"
gp env PROD_CONNECTION_URL="postgresql://root:goodDatabasePassword1@cruddur-db-instance.c8ersdfsdf.us-east-1.rds.amazonaws.com:5432/cruddur"
```

## Bash scripting for common database actions

We then created a new folder in 'backend-flask' named 'bin' which stands for binary. In this folder, we can store bash scripts to execute commands on our database. We then made several new files: 'db-create', 'db-drop', 'db-schema-load'.

For each of the files add a shebang to instruct our app to treat the file as a bash script:

```
#! /user/bin/bash
```
From the 'Backend-flask' folder, make our new files executable by running 'chmod u+x bin/db-create', 'chmod u+x bin/db-drop', 'chmod u+x bin/db-schema-load'
We started off testing if we can drop our database. To do this, add the code below to 'db-drop'.

```
psql $CONNECTION_URL -c "drop database cruddur;'
```

This command should psql connect to our local Postgres database using our connection string url, then using '-c' it issues a SQL command of "drop database cruddur;"

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
'./bin/<file-name>' eg './bin/db-create'

We need a way to determine when we're running from our production environment (prod) or our local Postgres environment. To do this, we added an if statement to the code.
Below is the code for 'schema-load'.
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

The additional code under our shebang was to provide a different color through the CLI when viewing our Postgres logs, so that we can see it when ran. We went through and added it to our other bash scripts as well. 

Back on our main task of adding tables to our database, we go back to our schema.sql, and add SQL commands to create our tables and activities:

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
We then made a new bash script named 'db-connect' inside the bin folder './bin/db-connect', made it executable by running 'chmod u+x ./bin/db-connect' then ran the file.
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

We were able to successfully connect to our local Postgres database using this bash script. We then ran '\dt' from the Postgres database to view our tables.

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
**NB** '$(realpath .)' is used to get the actual path of a specified file.
- For example the code below reveals the path of 'schema.sql'
- To print colors in Bash we use codes fore example: ''\033[1;36m''
```
schema_path="$(realpath .)/db/schema.sql"
echo $schema_path
```

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
This db-seed script will run our 'seed.sql' file that we created in 'backend-flask/db' which contains: 

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
```
#! /usr/bin/bash

aws ec2 modify-security-group-rules \
    --group-id $DB_SG_ID \
    --security-group-rules "SecurityGroupRuleId=$DB_SG_RULE_ID,SecurityGroupRule={IpProtocol=tcp,FromPort=5432,ToPort=5432,CidrIpv4=$GITPOD_IP/32}"
```

To connect to 'PROD' environment, you can affix the command with PROD to our scripts eg. `./bin/db-connect prod`


## Install Postgres Driver in Backend Application
### db-sessions
We may need to see what connections are being used to our Postgres database. For this, we implement 'db-sessions' and make it executable.
create a file called 'db-sessions' under 'backend-flask/bin'

```
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
```
 chmod u+x ./db-sessions
```

When we run this, we're able to see the active connections to our database, and close unnecessary connections. 

We then create a script to run all of our commands, so that we don't have to run them individually. We create 'db-setup' and make it executable.

### db-setup
```
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
```
 chmod u+x ./db-setup
```
## Install the Postgres Driver
With that setup, now we could now install the Postgres driver in our Backend application. We're going to use an AWS Lambda to to insert users into our database. Since AWS lacks the required PostgreSQL libraries in the AMI image, we must run the Postgres driver, custom compliled Psycopg2 C library for Python. To implement this, we add to the following libraries to our requirements.txt file. 

```
psycopg[binary]
psycopg[pool]
```

We then do a 'pip install -r requirements.txt' to install the drivers. 

## Connect Gitpod to RDS Instance

We're going to have to use pooling as a way of dealing with connections to our database. There's a certain amount of connections your database can handle in relational databases. There's concurrent connections, where some are running, some aren't. These connection pools allow us to re-use connections with concurrent connections. Since we're running Lambda functions, if our app became widely popular, we'd need to use a proxy, as Lambda functions create new functions each time it's ran, which could become expensive.

To create our connection pool, we create a new file in 'backend-flask/lib' named 'db.py'

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

We open docker-compose.yml and add an environment variable for our CONNECTION_URL.

```yml
CONNECTION_URL: "postgresql://postgres:password@localhost:5432/cruddur"
```

Next we open **home_activities.py** to import our connection pool, remove our mock data, and add our query to establish our connection. 

```py
from lib.db import pool, query_wrap_array

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

```
psql $PROD_CONNECTION_URL
```

From the terminal, we run 'curl ifonfig.me' which outputs our Gitpod IP address. We next passed GITPOD_IP=$(curl ifconfig.me) as variable so we can grab GITPOD_IP for RDS whenever needed. This allowed us to store our current IP address as an environment variable. 

We again test the 'psql' command above, this time it works. Since our IP is going to update everytime we launch our workspace, we will need to manually update that IP stored by the inbound rule everytime as well.

There's several env variables we then set after this, passing our security group id and our security group rule id as variables: DB_SG_ID and DB_SG_RULE_ID

```sh
export DB_SG_ID="sg-12345"
gp env DB_SG_ID="sg-12345"
export DB_SG_RULE_ID="sgr-12345"
gp env DB_SG_RULE_ID="sgr-12345"
```
Since the ip address changes everytime, you need to change the ip on the security group of the rds instance here is the script to add to the file rds-update-sg-rule under bin:
```py
aws ec2 modify-security-group-rules \
    --group-id $DB_SG_ID \
    --security-group-rules "SecurityGroupRuleId=$DB_SG_RULE_ID,SecurityGroupRule={Description=GITPOD,IpProtocol=tcp,FromPort=5432,ToPort=5432,CidrIpv4=$GITPOD_IP/32}"
```
We also store our env var in '.gitpod.yml' as well as create a new bash script named 'rds-update-sg-rule' to run every time our environment launches:

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

```
#! /usr/bin/bash

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="rds-update-sg-rule"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"
```
* Command to update the security groups:
```
aws ec2 modify-security-group-rules \
    --group-id $DB_SG_ID \
    --security-group-rules "SecurityGroupRuleId=$DB_SG_RULE_ID,SecurityGroupRule={Description=GITPOD,IpProtocol=tcp,FromPort=5432,ToPort=5432,CidrIpv4=$GITPOD_IP/32}"
```

After confirming connection to RDS from Gitpod, modified docker-compose.yml to pass a different env var for CONNECTION_URL. 

```yml
CONNECTION_URL: "${PROD_CONNECTION_URL}"
```

# Create Lambda
Create a lambda in the region where are your services and create the same file under aws/lambdas calling the file cruddur-post-confirmation.py

```
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

the env var for the lambda will be **CONNECTION_URL** which has the variable of the **PROD_CONNECTION_URL** set on gitpod/codespace (example: PROD_CONNECTION_URL="postgresql://userofthedb:masterpassword@endpointofthedb:5432/cruddur)

Once you create the env var, create also the layer>add layers> select specify arn
```
arn:aws:lambda:your region:898466741470:layer:psycopg2-py38:1
```

now it is time to create the trigger for cognito.
from cognito,  select the user pool and go to the user pool properties to find the lambda triggers. follow the configuration according to the image below:

![lambda triggers](https://github.com/dontworryjohn/aws-bootcamp-cruddur-2023/blob/main/images/lambda%20triggers.png)

Make sure to attach the following policy **AWSLambdaVPCAccessExecutionRole** to the lambda role by going to configuration>permission> link under the Role name.

Once attached the policy, go to VPC and select the VPC where resides the RDS,
the subnet mask (i suggest selecting just 1 as you could have timeout error during the execution of the lambda) and select the same security group of the rds. In my case i took the default vpc for my region as i deployed there, the subnetmask in my case eu-west-2a (make sure to verify where reside your rds by going to EC2>Network Interface under network & security)
and security group please make sure to insert the new inbound rule.
