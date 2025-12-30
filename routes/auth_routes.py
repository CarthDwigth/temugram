from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from db import get_db

auth_routes = Blueprint("auth_routes", __name__)

@auth_routes.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Encriptamos la contraseña por seguridad
        hashed_password = generate_password_hash(password)
        
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            return redirect(url_for('auth_routes.login'))
        except Exception as e:
            conn.rollback()
            return f"Error: El usuario ya existe o hubo un fallo en la DB: {e}"
        finally:
            cur.close()
            conn.close()
            
    return render_template("registro.html")