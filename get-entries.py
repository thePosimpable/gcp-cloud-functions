import sqlalchemy
import os
import functions_framework
import json
from google.oauth2 import id_token
from google.auth.transport import requests

def verify_token(request):
    token = request.args.get('token')
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        return True

    except ValueError:
        return False

def get_db():
    connection_name = os.environ.get('CONNECTION_NAME')
    db_name = os.environ.get('DB')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    driver_name = 'postgres+pg8000'
    qstring =  dict({"unix_sock": "/cloudsql/{}/.s.PGSQL.5432".format(connection_name)})

    db = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL(
            drivername=driver_name,
            username=db_user,
            password=db_password,
            database=db_name,
            query=qstring,
        ), 
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800
    )

    return db

@functions_framework.http
def main(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }

    if not verify_token(request):
        return ('unauthenticated', 401, headers)

    db = get_db()

    query_string = """
      SELECT * FROM entries;
    """

    query = sqlalchemy.text(query_string) 

    try:
        with db.connect() as conn:
            result_set = conn.execute(query)
                
            return (json.dumps([dict(result) for result in result_set], default = str), 200, headers)
        
    except Exception as e:
        return ('Error: {}'.format(str(e)), 400, headers)