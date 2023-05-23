import sqlalchemy
import os
from flask import jsonify

connection_name = os.environ.get('CONNECTION_NAME')
db_name = os.environ.get('DB')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
table_name = os.environ.get('TABLE_NAME')

driver_name = 'postgres+pg8000'
query_string =  dict({"unix_sock": "/cloudsql/{}/.s.PGSQL.5432".format(connection_name)})

def main(request):
    request_json = request.get_json()
    stmt = sqlalchemy.text('SELECT * FROM {};'.format(table_name))
    
    db = sqlalchemy.create_engine(
      sqlalchemy.engine.url.URL(
        drivername=driver_name,
        username=db_user,
        password=db_password,
        database=db_name,
        query=query_string,
      ), 
      pool_size=5,
      max_overflow=2,
      pool_timeout=30,
      pool_recycle=1800
    )
    try:
        with db.connect() as conn:
            conn.execute(stmt)

            result_set = db.execute(stmt)  
            return jsonify([dict(result) for result in result_set])
        
    except Exception as e:
        return 'Error: {}'.format(str(e))