from db import get_db_connection

# Obtener todos los usuarios (para panel admin)
def obtener_usuarios_admin():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, rol FROM usuarios ORDER BY id ASC")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return usuarios

# Actualizar rol de un usuario
def actualizar_rol(usuario_id, nuevo_rol):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, usuario_id))
    conn.commit()
    cur.close()
    conn.close()

# Borrar usuario
def borrar_usuario(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE username = %s", (username,))
    conn.commit()
    cur.close()
    conn.close()

# Obtener roles y permisos (para panel admin)
def obtener_roles_permisos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT rol, puede_borrar_fotos, puede_borrar_usuarios, puede_gestionar_roles FROM permisos_roles")
    roles = cur.fetchall()
    cur.close()
    conn.close()
    return roles

# Actualizar permisos de un rol
def actualizar_permisos(rol, puede_borrar_fotos=False, puede_borrar_usuarios=False, puede_gestionar_roles=False):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE permisos_roles 
        SET puede_borrar_fotos = %s, puede_borrar_usuarios = %s, puede_gestionar_roles = %s 
        WHERE rol = %s
    """, (puede_borrar_fotos, puede_borrar_usuarios, puede_gestionar_roles, rol))
    conn.commit()
    cur.close()
    conn.close()

# Crear nuevo rol
def crear_rol(nuevo_rol):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO permisos_roles (rol) VALUES (%s) ON CONFLICT DO NOTHING", (nuevo_rol,))
    conn.commit()
    cur.close()
    conn.close()
