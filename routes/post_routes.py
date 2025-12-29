from flask import Blueprint, request, redirect, url_for, session
from services.posts import publicar_post, comentar_post, reaccionar_post
from services.uploads import subir_foto_nube

post_routes = Blueprint('post_routes', __name__)

@post_routes.route('/publicar', methods=['GET', 'POST'])
def publicar():
    if 'user_id' not in session:
        return redirect(url_for('auth_routes.login'))
    if request.method == 'POST':
        archivo = request.files['foto']
        url_foto = subir_foto_nube(archivo)
        descripcion = request.form['descripcion']
        publicar_post(session['user_id'], descripcion, url_foto)
        return redirect(url_for('main_routes.home'))
    return render_template('publicar.html')

@post_routes.route('/comentar/<int:post_id>', methods=['POST'])
def comentar(post_id):
    if 'username' not in session:
        return redirect(url_for('auth_routes.login'))
    texto = request.form.get('texto')
    if texto:
        comentar_post(post_id, session['username'], texto)
    return redirect(url_for('main_routes.home'))

@post_routes.route('/reaccionar/<int:post_id>/<tipo>')
def reaccionar(post_id, tipo):
    if 'user_id' not in session:
        return redirect(url_for('auth_routes.login'))
    reaccionar_post(post_id, session['user_id'], tipo)
    return redirect(url_for('main_routes.home'))
