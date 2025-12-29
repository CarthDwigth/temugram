from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

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

def login_usuario(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, password, rol FROM usuarios WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and check_password_hash(user[1], password):
        return {'id': user[0], 'rol': user[2]}
    return None

def actualizar_ultima_conexion(username):
    if not username:
        return
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE usuarios SET ultima_conexion = CURRENT_TIMESTAMP WHERE username = %s",
        (username,)
    )
    conn.commit()
    cur.close()
    conn.close()

def obtener_usuarios_online():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT username, emoji_perfil
        FROM usuarios
        WHERE ultima_conexion >= NOW() - INTERVAL '5 minutes'
        ORDER BY ultima_conexion DESC
    """)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def obtener_usuarios_sidebar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT username, rol, fecha_registro, emoji_perfil
        FROM usuarios
        ORDER BY fecha_registro DESC
    """)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result
