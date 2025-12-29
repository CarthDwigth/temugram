from flask import Blueprint, render_template, request, redirect, url_for, session
from services.auth import registrar_usuario, login_usuario

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
        user = login_usuario(username, password)
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
