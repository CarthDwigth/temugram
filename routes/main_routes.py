from flask import Blueprint, render_template
from db import get_db

main_routes = Blueprint("main_routes", __name__)

@main_routes.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, descripcion, url_foto, posts.id, rol, emoji
        FROM posts
        JOIN usuarios ON posts.user_id = usuarios.id
        ORDER BY posts.id DESC
    """)
    posts = cur.fetchall()

    cur.execute("""
        SELECT post_id, username, texto, emoji
        FROM comentarios
        JOIN usuarios ON comentarios.user_id = usuarios.id
    """)
    comentarios = cur.fetchall()

    cur.execute("""
        SELECT id, username, rol, emoji, fecha_registro
        FROM usuarios
    """)
    usuarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        posts=posts,
        comentarios=comentarios,
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