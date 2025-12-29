import psycopg2
from config import DATABASE_URL

def get_db_connection():
    """Devuelve una conexión a la base de datos."""
    return psycopg2.connect(DATABASE_URL)

def inicializar_base_de_datos():
    """Crea las tablas si no existen."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password TEXT NOT NULL,
        rol VARCHAR(20) DEFAULT 'Usuario',
        emoji_perfil VARCHAR(10) DEFAULT '👤',
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ultima_conexion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        id_usuario INT REFERENCES usuarios(id),
        descripcion TEXT,
        foto TEXT,
        fecha_publicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
