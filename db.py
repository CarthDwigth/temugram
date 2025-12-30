import psycopg2
import os

def get_db():
    # Render te da la URL completa en esta variable
    db_url = os.environ.get("DATABASE_URL")
    
    # Esto permite que se conecte tanto en local como en la nube
    conn = psycopg2.connect(db_url)
    return conn

def crear_tablas():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            usuario_id INTEGER,
            tipo TEXT DEFAULT 'like', -- Por si luego quieres añadir 🔥 o ❤️
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
            UNIQUE(post_id, usuario_id) -- Esto evita likes duplicados
        )
    ''')