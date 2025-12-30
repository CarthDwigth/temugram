import psycopg2
import os

def get_db():
    # 1. Obtener la URL de la base de datos de las variables de entorno de Render
    db_url = os.environ.get("DATABASE_URL")
    
    # 2. PRIMERO conectamos a la base de datos (Creamos 'conn')
    conn = psycopg2.connect(db_url)
    
    # 3. DESPUÉS llamamos a crear_tablas pasando la conexión ya existente
    crear_tablas(conn)
    
    return conn

def crear_tablas(conn):
    # Creamos el cursor a partir de la conexión recibida
    cur = conn.cursor()
    
    # Tabla de Reacciones (PostgreSQL usa SERIAL para IDs autoincrementales)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reacciones (
            id SERIAL PRIMARY KEY,
            post_id INTEGER REFERENCES posts(id),
            usuario_id INTEGER REFERENCES usuarios(id),
            tipo TEXT DEFAULT 'like',
            UNIQUE(post_id, usuario_id)
        )
    ''')
    
    # Tabla de Seguidores
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
    print("Tablas verificadas exitosamente.")