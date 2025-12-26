import os
import psycopg2
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash

def get_connection():
    url = os.getenv('DATABASE_URL')
    if url and url.startswith('postgres'):
        result = urlparse(url)
        return psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
    else:
        import sqlite3
        return sqlite3.connect('temugram.db')

def registrar_usuario(username, password):
    conn = get_connection()
    cur = conn.cursor()
    # Encriptamos la contraseña antes de guardarla
    password_segura = generate_password_hash(password)
    try:
        cur.execute('INSERT INTO usuarios (username, password) VALUES (%s, %s)', 
                   (username, password_segura))
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
    # Buscamos al usuario por nombre para obtener su hash
    cur.execute('SELECT id, password FROM usuarios WHERE username = %s', (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        user_id, hashed_password = user
        # Comparamos la clave ingresada con el hash guardado
        if check_password_hash(hashed_password, password):
            return user_id
    return None