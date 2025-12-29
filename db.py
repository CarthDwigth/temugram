import psycopg2
from config import DATABASE_URL

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def inicializar_base_de_datos():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Crear tabla usuarios si no existe, con ultima_conexion
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol VARCHAR(20) DEFAULT 'Usuario',
            emoji_perfil VARCHAR(10) DEFAULT '👤',
            ultima_conexion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Aquí podrías crear otras tablas como posts, comentarios, roles, etc.
    
    conn.commit()
    cur.close()
    conn.close()
