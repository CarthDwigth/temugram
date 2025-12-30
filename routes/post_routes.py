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
    
    # IMPORTANTE: name="texto" debe ser igual en tu HTML
    texto = request.form.get("texto")
    
    if texto:
        conn = get_db()
        cur = conn.cursor()
        
        # 1. Buscamos el ID del que está comentando
        cur.execute("SELECT id FROM usuarios WHERE username = %s", (session['username'],))
        user_id = cur.fetchone()[0]
        
        # 2. Insertamos el comentario en la tabla
        cur.execute("""
            INSERT INTO comentarios (post_id, user_id, texto) 
            VALUES (%s, %s, %s)
        """, (post_id, user_id, texto))
        
        conn.commit()
        cur.close()
        conn.close()
    
    # 3. Volvemos al inicio para ver el comentario publicado
    return redirect(url_for('main_routes.index'))

@post_routes.route("/reaccionar/<int:post_id>", methods=["POST"])
def reaccionar(post_id):
    if 'user_id' not in session:
        return {"error": "no_auth"}, 401
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # 1. Verificar si ya existe el like
    cur.execute("SELECT id FROM reacciones WHERE user_id = %s AND post_id = %s", (user_id, post_id))
    existe = cur.fetchone()

    if existe:
        # Si existe, lo quitamos (Dislike)
        cur.execute("DELETE FROM reacciones WHERE id = %s", (existe[0],))
        accion = "removed"
    else:
        # Si no existe, lo ponemos
        cur.execute("INSERT INTO reacciones (user_id, post_id) VALUES (%s, %s)", (user_id, post_id))
        accion = "added"

    conn.commit()
    
    # 2. Obtener el conteo actualizado
    cur.execute("SELECT COUNT(*) FROM reacciones WHERE post_id = %s", (post_id,))
    nuevo_total = cur.fetchone()[0]
    
    cur.close()
    conn.close()

    # 3. RESPUESTA INTELIGENTE: Si es AJAX, mandamos JSON. Si no, redirigimos.
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "accion": accion, "total": nuevo_total}
    
    return redirect(request.referrer or url_for('main_routes.index'))

@post_routes.route('/reaccionar_comentario/<int:comentario_id>', methods=['POST'])
def reaccionar_comentario(comentario_id):
    if 'user_id' not in session:
        return redirect(url_for('auth_routes.login'))
    
    usuario_id = session['user_id']
    db = get_db()
    cur = db.cursor()

    # 1. Verificamos si el usuario ya le dio like a ese comentario
    cur.execute("SELECT id FROM likes_comentarios WHERE usuario_id = %s AND comentario_id = %s", 
                (usuario_id, comentario_id))
    like_existente = cur.fetchone()

    if like_existente:
        # Si ya existe, lo quitamos (Dislike)
        cur.execute("DELETE FROM likes_comentarios WHERE usuario_id = %s AND comentario_id = %s", 
                    (usuario_id, comentario_id))
    else:
        # Si no existe, lo agregamos (Like)
        cur.execute("INSERT INTO likes_comentarios (usuario_id, comentario_id) VALUES (%s, %s)", 
                    (usuario_id, comentario_id))

    db.commit()
    cur.close()
    
    # Regresamos a la página donde estábamos
    return redirect(url_for('main_routes.index'))