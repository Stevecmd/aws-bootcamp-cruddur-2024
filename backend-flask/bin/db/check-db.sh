# Check if database already exists
RUN /backend-flask/bin/db/check-db.sh

DB_NAME="cruddur"

# Check if database already exists
if aws rds describe-db-instances --db-instance-identifier "cruddur-db-instance" --query "DBInstances[].DBInstanceIdentifier" --output text | grep -q "cruddur-db-instance"; then
  echo "Database instance already exists. Aborting."
  exit 1
fi