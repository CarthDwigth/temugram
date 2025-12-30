import psycopg2
import os

def get_db():
    # Render te da la URL completa en esta variable
    db_url = os.environ.get("DATABASE_URL")
    
    # Esto permite que se conecte tanto en local como en la nube
    conn = psycopg2.connect(db_url)
    return conn
