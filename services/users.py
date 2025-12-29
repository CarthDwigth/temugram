from db import get_db_connection
from werkzeug.security import generate_password_hash

def registrar_usuario(username, password, emoji='👤'):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO usuarios (username, password, rol, emoji_perfil) VALUES (%s, %s, %s, %s)",
            (username, password_hash, 'Usuario', emoji)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
