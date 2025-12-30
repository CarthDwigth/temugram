import psycopg2
from psycopg2.extras import RealDictCursor
import os

def get_db():
    # Render te da la URL completa en esta variable
    db_url = os.environ.get("DATABASE_URL")
    crear_tablas(conn)
    
    # Esto permite que se conecte tanto en local como en la nube
    conn = psycopg2.connect(db_url)
    return conn

def crear_tablas(conn):
    # Creamos el cursor a partir de la conexión
    cur = conn.cursor()
    
    # TABLA DE REACCIONES (Versión PostgreSQL)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reacciones (
            id SERIAL PRIMARY KEY,
            post_id INTEGER REFERENCES posts(id),
            usuario_id INTEGER REFERENCES usuarios(id),
            tipo TEXT DEFAULT 'like',
            UNIQUE(post_id, usuario_id)
        )
    ''')
    
    # TABLA DE SEGUIDORES (Versión PostgreSQL)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS seguidores (
            id SERIAL PRIMARY KEY,
            seguidor_id INTEGER REFERENCES usuarios(id),
            seguido_id INTEGER REFERENCES usuarios(id),
            fecha_follow TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(seguidor_id, seguido_id)
        )
    ''')
    
    conn.commit()
    cur.close()