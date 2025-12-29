from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

# Registro seguro
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

# Login seguro
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

# Usuarios online (últimos 5 minutos)
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

# Obtener datos de un usuario
def obtener_datos_usuario(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, emoji_perfil, rol FROM usuarios WHERE username = %s", (username,))
    data = cur.fetchone()
    cur.close()
    conn.close()
    if data:
        return {'id': data[0], 'emoji': data[1], 'rol': data[2]}
    return None

# Actualizar última conexión
def actualizar_ultima_conexion(session):
    if 'username' not in session:
        return
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET ultima_conexion = CURRENT_TIMESTAMP WHERE username = %s", (session['username'],))
    conn.commit()
    cur.close()
    conn.close()

def obtener_usuarios_sidebar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, rol, emoji, fecha_registro FROM usuarios ORDER BY fecha_registro DESC;")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return usuarios


