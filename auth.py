import sqlite3

def registrar_usuario(username, password):
    try:
        with sqlite3.connect('temugram.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        print("❌ Error: Ese nombre de usuario ya existe.")
        return False

def login(username, password):
    with sqlite3.connect('temugram.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        return user[0] if user else None # Devuelve el ID si existe, o None