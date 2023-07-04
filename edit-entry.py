import sqlalchemy
import os
import random
import functions_framework
import json
from datetime import datetime
from google.oauth2 import id_token
from google.auth.transport import requests


def verify_token(request):
    source = request.args.get('source')
    token = request.args.get('token')

    if not source or not token:
        return False
    
    if source == "google":
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request())
            return True

        except ValueError:
            return False
        
    elif source == "firebase":
        try:
            idinfo = id_token.verify_firebase_token(token, requests.Request())
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

def generate_random_color() -> str:
    r = lambda: random.randint(0,255)
    return '#%02X%02X%02X' % (r(),r(),r())

@functions_framework.http
def main(request):
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }

    if not verify_token(request):
        return ('unauthenticated', 401, headers)
    
    db = get_db()

    request_json = request.get_json()

    entryId = request.args.get('entryId')

    if entryId:
        query_string = """
            INSERT INTO entries ("entryId", title, description, "startDate", "endDate", color, icon, "createdAt", "updatedAt")
            VALUES ({entryId}, '{title}', '{description}', '{startDate}', '{endDate}', '{color}', '{icon}', '{createdAt}', '{updatedAt}')
            ON CONFLICT ("entryId")
            DO UPDATE SET
                title = '{title}', 
                description = '{description}',
                "startDate" = '{startDate}',
                "endDate" = '{endDate}',
                color = '{color}',
                icon = '{icon}',
                "createdAt" = '{createdAt}',
                "updatedAt" = '{updatedAt}'
            ;
        """.format(
            entryId = entryId,
            title = request_json['title'],
            description = request_json['description'],
            startDate = request_json['startDate'],
            endDate = request_json['endDate'],
            color = request_json['color'] if "color" in request_json and request_json['color'] else generate_random_color(),
            icon = request_json['icon'],
            createdAt = request_json['createdAt'],
            updatedAt = datetime.now()
        )

        query = sqlalchemy.text(query_string)
        
        try:
            with db.connect() as conn:
                db.execute(query)  
                return (f"successfully updated entry {entryId}", 200, headers)
            
        except Exception as e:
            return 'Error: {}'.format(str(e))
        
    return ('Record not found'.format(str(e)), 400, headers)