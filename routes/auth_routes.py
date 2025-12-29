from flask import Blueprint, render_template, request, redirect, url_for
from services.users import registrar_usuario

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        emoji = request.form.get('emoji', '👤')
        try:
            registrar_usuario(username, password, emoji)
            return "Usuario registrado correctamente ✅"
        except Exception as e:
            return f"Error: {e}"
    return render_template('registro.html')

