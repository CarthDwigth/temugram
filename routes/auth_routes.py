from flask import Blueprint, render_template, request, redirect, url_for, session
from services.users import registrar_usuario, login_usuario

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        emoji = request.form.get('emoji', '👤')
        try:
            registrar_usuario(username, password, emoji)
            return redirect(url_for('auth_routes.login'))
        except Exception as e:
            return f"Error: {e}"
    return render_template('registro.html')

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = login_usuario(username, password)  # << aquí llama al service
        if user:
            session['user_id'] = user['id']
            session['username'] = username
            session['rol'] = user['rol']
            return redirect(url_for('main_routes.home'))
        else:
            return "Usuario o contraseña incorrectos"
    return render_template('login.html')

@auth_routes.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main_routes.home'))

@auth_routes.route('/fix-password', methods=['GET'])
def fix_password():
    from werkzeug.security import generate_password_hash
    from db import get_db_connection

    username = "Carth"
    password_plano = "123123123"

    password_hash = generate_password_hash(password_plano)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE usuarios SET password = %s WHERE username = %s",
        (password_hash, username)
    )
    conn.commit()
    cur.close()
    conn.close()

    return "Contraseña reparada"
