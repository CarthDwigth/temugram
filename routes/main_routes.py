from flask import Blueprint, render_template, session, redirect, url_for, request
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
        SELECT comentarios.id, username, texto, emoji, comentarios.user_id, post_id,
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

    # 1. Obtener datos del usuario del perfil
    # Cambia el SELECT * por columnas específicas
    cur.execute("SELECT id, username, rol, emoji, fecha_registro FROM usuarios WHERE username=%s", (username,))
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

@main_routes.route("/cambiar_emoji", methods=["POST"])
def cambiar_emoji():
    # ... tu código ...
    if 'user_id' not in session:
        return redirect(url_for('main_routes.index'))
    
    nuevo_emoji = request.form.get("emoji")
    user_id = session.get('user_id')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET emoji = %s WHERE id = %s", (nuevo_emoji, user_id))
    conn.commit()
    cur.close()
    conn.close()
    
    # Obtenemos el username para redirigir de vuelta al perfil
    username = session.get('username')
    return redirect(url_for('main_routes.perfil', username=username))

@main_routes.route("/post/<int:post_id>")
def ver_post(post_id):
    conn = get_db()
    cur = conn.cursor()

    # 1. Obtener el post con los datos del autor
    cur.execute("""
        SELECT 
            usuarios.username, 
            posts.descripcion, 
            posts.url_foto, 
            posts.id, 
            usuarios.rol, 
            usuarios.emoji, 
            posts.user_id,
            (SELECT COUNT(*) FROM reacciones WHERE post_id = posts.id) AS total_likes
        FROM posts
        JOIN usuarios ON posts.user_id = usuarios.id
        WHERE posts.id = %s
    """, (post_id,))
    post = cur.fetchone()

    if not post:
        cur.close()
        conn.close()
        return "Post no encontrado", 404

    # 2. Obtener TODOS los comentarios de este post
    cur.execute("""
        SELECT comentarios.id, username, texto, emoji,
        (SELECT COUNT(*) FROM likes_comentarios WHERE comentario_id = comentarios.id) AS likes_count
        FROM comentarios
        JOIN usuarios ON comentarios.user_id = usuarios.id
        WHERE post_id = %s
        ORDER BY comentarios.id ASC
    """, (post_id,))
    comentarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("post_detalle.html", post=post, comentarios=comentarios)