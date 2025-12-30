import os
import requests
import base64
from flask import Blueprint, render_template, request, redirect, url_for, session
from db import get_db

post_routes = Blueprint("post_routes", __name__)

@post_routes.route("/publicar", methods=["GET", "POST"])
def crear_post():
    if 'username' not in session:
        return redirect(url_for('auth_routes.login'))

    if request.method == "POST":
        foto = request.files.get("foto")
        descripcion = request.form.get("descripcion")

        if foto:
            # 1. Subir a Freeimage.host
            api_key = os.environ.get("FREEIMAGE_API_KEY")
            url_api = "https://freeimage.host/api/1/upload"
            
            files = {"source": (foto.filename, foto.read())}
            data = {"key": api_key, "action": "upload", "format": "json"}
            
            response = requests.post(url_api, data=data, files=files)
            json_data = response.json()

            if response.status_code == 200:
                url_foto = json_data['image']['url']
                
                # 2. Guardar en la Base de Datos
                conn = get_db()
                cur = conn.cursor()
                
                # Buscamos el ID del usuario logueado
                cur.execute("SELECT id FROM usuarios WHERE username = %s", (session['username'],))
                user_id = cur.fetchone()[0]
                
                # Insertamos el post
                cur.execute("INSERT INTO posts (user_id, descripcion, url_foto) VALUES (%s, %s, %s)",
                            (user_id, descripcion, url_foto))
                
                conn.commit()
                cur.close()
                conn.close()
                
                return redirect(url_for('main_routes.index'))

    return render_template("publicar.html")

@post_routes.route("/comentar/<int:post_id>", methods=["POST"])
def comentar(post_id):
    if 'username' not in session:
        return redirect(url_for('auth_routes.login'))
    
    contenido = request.form.get("contenido")
    if contenido:
        conn = get_db()
        cur = conn.cursor()
        
        # Obtenemos el ID del usuario actual
        cur.execute("SELECT id FROM usuarios WHERE username = %s", (session['username'],))
        user_id = cur.fetchone()[0]
        
        # Insertamos el comentario
        cur.execute("INSERT INTO comentarios (post_id, user_id, contenido) VALUES (%s, %s, %s)",
                    (post_id, user_id, contenido))
        
        conn.commit()
        cur.close()
        conn.close()
    
    return redirect(url_for('main_routes.index'))