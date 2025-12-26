import psycopg2
import os
from urllib.parse import urlparse

def get_connection():
    url = os.getenv('postgresql://temugram_db_user:5gEUWXA2Lv890abWdyrRY6gUZbx01M1V@dpg-d572oe6uk2gs73cpnli0-a.oregon-postgres.render.com/temugram_db')
    if url:
        # Si encuentra la URL, usa Postgres
        result = urlparse(url)
        return psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
    else:
        # ESTO ES LO QUE ESTÁ PASANDO: No encuentra la variable
        # Vamos a forzar el error para saber qué pasa
        raise Exception("ERROR CRÍTICO: No se encontró la variable DATABASE_URL en Render")

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