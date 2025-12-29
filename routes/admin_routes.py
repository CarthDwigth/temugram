from flask import Blueprint, render_template, request, redirect, url_for, session
from services.admin import obtener_usuarios_admin, actualizar_rol, borrar_usuario

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/admin/panel')
def panel():
    if session.get('rol') != 'Admin':
        return redirect(url_for('main_routes.home'))
    usuarios = obtener_usuarios_admin()
    return render_template('admin_panel.html', usuarios=usuarios)

@admin_routes.route('/admin/cambiar_rol', methods=['POST'])
def cambiar_rol():
    if session.get('rol') != 'Admin':
        return "No autorizado", 403
    usuario_id = request.form.get('usuario_id')
    nuevo_rol = request.form.get('rol')
    actualizar_rol(usuario_id, nuevo_rol)
    return redirect(url_for('admin_routes.panel'))

@admin_routes.route('/admin/borrar_usuario/<username>')
def borrar_usuario_route(username):
    if session.get('rol') != 'Admin':
        return redirect(url_for('main_routes.home'))
    borrar_usuario(username)
    return redirect(url_for('admin_routes.panel'))
