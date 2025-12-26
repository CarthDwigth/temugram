import psycopg2
import os
from urllib.parse import urlparse

def get_connection():
    # Buscamos la URL en el panel de Render
    url = os.getenv('DATABASE_URL')
    
    if url:
        # CONEXIÓN A POSTGRES (Para Render)
        result = urlparse(url)
        return psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
    else:
        # CONEXIÓN A SQLITE (Solo para tu PC local)
        import sqlite3
        return sqlite3.connect('temugram.db')

def registrar_usuario(username, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Usamos %s porque en Render MANDARÁ Postgres
        cur.execute('INSERT INTO usuarios (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error en registro: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def login(username, password):
    conn = get_connection()
    cur = conn.cursor()
    # Aquí es donde fallaba antes. Ahora funcionará con Postgres.
    cur.execute('SELECT id FROM usuarios WHERE username = %s AND password = %s', (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user[0] if user else None