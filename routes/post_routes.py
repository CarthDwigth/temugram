from flask import Blueprint, request, redirect, url_for, session
from db import get_db

post_routes = Blueprint("post_routes", __name__)

@post_routes.route("/publicar", methods=["POST"])
def publicar():
    if not session.get("user_id"):
        return redirect(url_for("auth_routes.login"))

    descripcion = request.form["descripcion"]
    url_foto = request.form["url_foto"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO posts (user_id, descripcion, url_foto)
        VALUES (%s, %s, %s)
    """, (session["user_id"], descripcion, url_foto))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("main_routes.index"))


@post_routes.route("/comentar/<int:post_id>", methods=["POST"])
def comentar(post_id):
    texto = request.form["texto"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO comentarios (post_id, user_id, texto)
        VALUES (%s, %s, %s)
    """, (post_id, session["user_id"], texto))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("main_routes.index"))
