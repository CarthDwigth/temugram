import psycopg2
import os
from urllib.parse import urlparse

def get_connection():
    url = os.getenv('DATABASE_URL')
    if url:
        result = urlparse(url)
        return psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
    import sqlite3
    return sqlite3.connect('temugram.db')

def registrar_usuario(username, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO usuarios (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()

def login(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM usuarios WHERE username = %s AND password = %s', (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user[0] if user else None