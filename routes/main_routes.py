from flask import Blueprint, render_template, session
from db import get_db

main_routes = Blueprint("main_routes", __name__)

@main_routes.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios")
    usuarios = cur.fetchall()

    cur.execute("""
        SELECT 
            usuarios.username,
            posts.descripcion,
            posts.url_foto,
            posts.id,
            usuarios.rol,
            usuarios.emoji
        FROM posts
        JOIN usuarios ON posts.user_id = usuarios.id
        ORDER BY posts.id DESC
    """)
    posts = cur.fetchall()

    cur.execute("""
        SELECT 
            comentarios.post_id,
            usuarios.username,
            comentarios.texto,
            usuarios.emoji
        FROM comentarios
        JOIN usuarios ON comentarios.user_id = usuarios.id
    """)
    comentarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        usuarios=usuarios,
        posts=posts,
        comentarios=comentarios
    )