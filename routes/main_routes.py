from flask import Blueprint, render_template
from db import get_db

main_routes = Blueprint("main_routes", __name__)

@main_routes.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()

    # 1. Obtener Posts (CON CONTEO DE LIKES)
    # Añadimos la subconsulta al final para obtener el total de reacciones
    cur.execute("""
        SELECT username, descripcion, url_foto, posts.id, rol, emoji,
        (SELECT COUNT(*) FROM reacciones WHERE post_id = posts.id) AS total_likes
        FROM posts
        JOIN usuarios ON posts.user_id = usuarios.id
        ORDER BY posts.id DESC
    """)
    posts = cur.fetchall() 
    # Ahora: p[0]=user, p[1]=desc, p[2]=url, p[3]=id, p[4]=rol, p[5]=emoji, p[6]=likes

    # 2. Obtener Comentarios
    cur.execute("""
        SELECT comentarios.id, username, texto, emoji, post_id,
        (SELECT COUNT(*) FROM likes_comentarios WHERE comentario_id = comentarios.id) AS likes_count
        FROM comentarios
        JOIN usuarios ON comentarios.user_id = usuarios.id
    """)
    comentarios_raw = cur.fetchall()

    comentarios_por_post = {}
    for c in comentarios_raw:
        pid = c[4] # El post_id ahora es el índice 4
        if pid not in comentarios_por_post:
            comentarios_por_post[pid] = []
        
        # AQUÍ ESTÁ LA SOLUCIÓN: Añadimos 'id' y 'likes_count'
        comentarios_por_post[pid].append({
            'id': c[0],           # <--- El c.id que buscaba el HTML
            'username': c[1],
            'texto': c[2],
            'emoji': c[3],
            'likes_count': c[5]   # <--- El numerito de likes
        })

    # 3. Obtener Usuarios para la barra lateral
    cur.execute("SELECT id, username, rol, emoji, fecha_registro FROM usuarios")
    usuarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        posts=posts,
        comentarios_dic=comentarios_por_post,
        usuarios=usuarios,
        usuarios_online=[]
    )


@main_routes.route("/perfil/<username>")
def perfil(username):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios WHERE username=%s", (username,))
    user = cur.fetchone()

    cur.execute("""
        SELECT descripcion, url_foto, id
        FROM posts
        WHERE user_id = %s
        ORDER BY id DESC
    """, (user[0],))
    posts = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("perfil.html", user=user, posts=posts)

@main_routes.route("/perfil/<username>")
def perfil(username):
    conn = get_db()
    cur = conn.cursor()

    # 1. Obtener datos del usuario del perfil
    cur.execute("SELECT * FROM usuarios WHERE username=%s", (username,))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        return "Usuario no encontrado", 404

    # 2. Obtener los posts de ese usuario
    cur.execute("""
        SELECT descripcion, url_foto, id
        FROM posts
        WHERE user_id = %s
        ORDER BY id DESC
    """, (user[0],))
    posts = cur.fetchall()

    # 3. ¡ESTO ES LO QUE FALTA! Obtener usuarios para el sidebar de Comunidad
    # Si el HTML del perfil tiene la sección de comunidad, necesita esta variable
    cur.execute("SELECT id, username, rol, emoji FROM usuarios LIMIT 10")
    lista_comunidad = cur.fetchall()

    cur.close()
    conn.close()

    # 4. Pasar todo al template (fíjate en 'usuarios=lista_comunidad')
    return render_template(
        "perfil.html", 
        user=user, 
        posts=posts, 
        usuarios=lista_comunidad
    )