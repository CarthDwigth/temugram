from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

auth_routes = Blueprint("auth_routes", __name__)

@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE username=%s", (username,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["rol"] = user[3]
            return redirect(url_for("main_routes.index"))

        return "Credenciales incorrectas"

    return render_template("login.html")


@auth_routes.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (username, password) VALUES (%s, %s)",
            (username, password)
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("auth_routes.login"))

    return render_template("registro.html")


@auth_routes.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main_routes.index"))
