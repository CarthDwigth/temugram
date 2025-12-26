import sqlite3

def inicializar():
    with sqlite3.connect('temugram.db') as conn:
        cursor = conn.cursor()
        # 1. Tabla de Usuarios con contraseña
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # 2. Tabla de Posts vinculada por id de usuario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                descripcion TEXT,
                url_foto TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios (id)
            )
        ''')
        conn.commit()
    print("🎯 Objetivo 1: Base de datos configurada.")

if __name__ == "__main__":
    inicializar()