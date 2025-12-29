from flask import Blueprint, render_template, session
from services.users import obtener_usuarios_online, obtener_usuarios_sidebar, actualizar_ultima_conexion

main_routes = Blueprint('main_routes', __name__)

@main_routes.route('/')
def home():
    if 'username' in session:
        actualizar_ultima_conexion(session['username'])
    usuarios_online = obtener_usuarios_online()
    usuarios_sidebar = obtener_usuarios_sidebar()
    return render_template('index.html',
                           usuarios_online=usuarios_online,
                           usuarios_sidebar=usuarios_sidebar)
