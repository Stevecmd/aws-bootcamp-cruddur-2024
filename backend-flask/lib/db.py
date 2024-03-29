from psycopg_pool import ConnectionPool, PoolTimeout
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
      # Print the SQL query with parameters
      self.print_sql('array',sql,params)

      # Wrap the SQL query
      wrapped_sql = self.query_wrap_array(sql)
      # Establish a connection and execute the query
      with self.pool.connection() as conn:
        with conn.cursor() as cur:  
          cur.execute(wrapped_sql,params)
          json = cur.fetchone()
          # Check if json_result is not None before accessing its elements
          if json is not None:
              return json[0]
          else:
              # Handle the case when the query result is None
              return None
    # When we want to return an array of json objects
# XXXXXXXXXXXXXXXXXXXXXXXXXX

    # def query_object_json(self,sql,uuid, params={}):
    #   """
    #   Run a query and return a single JSON object.

    #   :param sql: SQL template string
    #   :param uuid: UUID parameter for the query
    #   :param params: Additional parameters
    #   :return: JSON object
    #   """
    #   self.print_sql('json', sql, params)
    #   self.print_params(params)

    #   # Add the 'uuid' key to the params dictionary
    #   params['uuid'] = uuid

    #   wrapped_sql = self.query_wrap_object(sql)

    #   with self.pool.connection() as conn:
    #     with conn.cursor() as cur:
    #       cur.execute(wrapped_sql, params)
    #       json = cur.fetchone()
    #       if json == None:
    #         return "{}"
    #       else:
    #         return json[0]
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def query_object_json(self,sql,params={}):
        """
        Run a query and return a single JSON object.

        :param sql: SQL template string
        :param params: Additional parameters
        :return: JSON object
        """
        try:
            self.print_sql('json', sql, params)
            self.print_params(params)

            # No need to add 'uuid' to params as it's already included

            wrapped_sql = self.query_wrap_object(sql)

            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(wrapped_sql, params)
                    json = cur.fetchone()
                    if json is None:
                        return "{}"
                    else:
                        return json[0]
        except Exception as ex:
            # Log database query errors
            print(f"Error in query_object_json: {ex}")
            raise ex

    def query_value(self,sql,params=None):
      if params is None:
          params = {}
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

    def print_sql_err(self, err):
      # get details about the exception
      err_type, _, traceback = sys.exc_info()

      # get the line number when the exception occurred
      line_num = traceback.tb_lineno

      # print the connect() error
      print("\npsycopg ERROR:", err, "on line number:", line_num)
      print("psycopg traceback:", traceback, "-- type:", err_type)

      # check if the error is related to a connection timeout
      if "timeout expired" in str(err):
          print("Connection timeout expired. Please check your database connection.")
      else:
          # print other types of errors
          print("pgerror:", getattr(err, 'pgerror', None))
          print("pgcode:", getattr(err, 'pgcode', None), "\n")

db = Db()