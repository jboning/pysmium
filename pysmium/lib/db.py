import psycopg2

from flask import g

from pysmium import app

db_conn = None

def init_db(config):
    global db_conn
    db_conn = psycopg2.connect(
        host=config.get('postgresql', 'host', 'localhost'),
        port=config.get('postgresql', 'port', '5432'),
        user=config.get('postgresql', 'user', 'osmium'),
        password=config.get('postgresql', 'password'),
        dbname=config.get('postgresql', 'dbname', 'osmium')
    )

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = db_conn.cursor()
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
