import psycopg2
from config import DATABASE_URL  # Asegúrate de tener tu DATABASE_URL en .env o config.py

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

