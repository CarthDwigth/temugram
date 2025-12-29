from flask import Blueprint, render_template, session
from services.posts import obtener_posts
from services.users import obtener_usuarios_online

main_routes = Blueprint('main_routes', __name__)

@main_routes.route('/')
def home():
    posts = obtener_posts()
    usuarios_online = obtener_usuarios_online()
    return render_template('index.html', posts=posts, usuarios_online=usuarios_online)

@main_routes.route('/perfil/<username>')
def perfil(username):
    from services.users import obtener_datos_usuario, obtener_posts_usuario
    user_data = obtener_datos_usuario(username)
    if not user_data:
        return "Usuario no encontrado", 404
    posts = obtener_posts_usuario(user_data['id'])
    return render_template('perfil.html', username=username, emoji=user_data['emoji'], rol=user_data['rol'], posts=posts)
