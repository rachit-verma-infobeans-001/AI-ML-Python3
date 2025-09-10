import mysql.connector

db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'sportspundit_dev'
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn
