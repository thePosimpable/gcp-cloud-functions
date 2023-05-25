import sqlalchemy
import os
from flask import jsonify
from datetime import datetime

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

def main(request):
    request_json = request.get_json()
    print(request_json)

    db = get_db()

    query_string = """
      SELECT * FROM entries;
    """

    query = sqlalchemy.text(query_string)
    
    try:
        with db.connect() as conn:
            conn.execute(query)
            result_set = db.execute(query)  
            return jsonify([dict(result) for result in result_set])
        
    except Exception as e:
        return 'Error: {}'.format(str(e))