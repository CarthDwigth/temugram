from db import get_db_connection

# Obtener todos los posts con info del usuario
def obtener_posts():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.username, p.descripcion, p.url_foto, p.id, u.rol, u.emoji_perfil
        FROM posts p
        JOIN usuarios u ON p.user_id = u.id
        ORDER BY p.id DESC
    """)
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return posts

# Obtener posts de un usuario
def obtener_posts_usuario(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.username, p.descripcion, p.url_foto, p.id, u.rol
        FROM posts p
        JOIN usuarios u ON p.user_id = u.id
        WHERE user_id = %s
        ORDER BY p.id DESC
    """, (user_id,))
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return posts

# Publicar post
def publicar_post(user_id, descripcion, url_foto):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO posts (user_id, descripcion, url_foto) VALUES (%s, %s, %s)", (user_id, descripcion, url_foto))
    conn.commit()
    cur.close()
    conn.close()

# Comentar post
def comentar_post(post_id, usuario, texto):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO comentarios (post_id, usuario, texto) VALUES (%s, %s, %s)", (post_id, usuario, texto))
    conn.commit()
    cur.close()
    conn.close()

# Reaccionar post
def reaccionar_post(post_id, user_id, tipo):
    conn = get_db_connection()
    cur = conn.cursor()
    # Eliminar reacción previa del mismo usuario
    cur.execute("DELETE FROM reacciones WHERE post_id = %s AND user_id = %s", (post_id, user_id))
    # Insertar nueva reacción
    cur.execute("INSERT INTO reacciones (post_id, user_id, tipo) VALUES (%s, %s, %s)", (post_id, user_id, tipo))
    conn.commit()
    cur.close()
    conn.close()
