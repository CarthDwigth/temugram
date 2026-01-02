import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, render_template_string
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
            api_key = os.environ.get("FREEIMAGE_API_KEY")
            url_api = "https://freeimage.host/api/1/upload"
            files = {"source": (foto.filename, foto.read())}
            data = {"key": api_key, "action": "upload", "format": "json"}
            
            response = requests.post(url_api, data=data, files=files)
            json_data = response.json()

            if response.status_code == 200:
                url_foto = json_data['image']['url']
                
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT id FROM usuarios WHERE username = %s", (session['username'],))
                user_id = cur.fetchone()[0]
                cur.execute("INSERT INTO posts (user_id, descripcion, url_foto) VALUES (%s, %s, %s)",
                            (user_id, descripcion, url_foto))
                conn.commit()
                cur.close()
                conn.close()
                
                return redirect(url_for('main_routes.index'))

    return render_template("publicar.html")

# ==================== COMENTARIOS ====================
@post_routes.route("/comentar/<int:post_id>", methods=["POST"])
def comentar(post_id):
    if 'user_id' not in session:
        return jsonify(status="error", message="No login"), 401

    texto = request.form.get("texto")
    if not texto:
        return jsonify(status="error", message="Texto vacío"), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE username = %s", (session['username'],))
    user_id = cur.fetchone()[0]

    cur.execute("INSERT INTO comentarios (post_id, user_id, texto) VALUES (%s, %s, %s) RETURNING id", (post_id, user_id, texto))
    comentario_id = cur.fetchone()[0]
    conn.commit()

    # Traemos username para renderizar
    cur.execute("""
        SELECT usuarios.username, comentarios.texto, comentarios.id
        FROM comentarios
        JOIN usuarios ON comentarios.user_id = usuarios.id
        WHERE comentarios.id = %s
    """, (comentario_id,))
    nuevo_comentario = cur.fetchone()
    cur.close()
    conn.close()

    html = render_template_string("""
    <div class="comentario-item">
        <p class="comentario-texto">
            <strong>@{{ c.username }}:</strong> {{ c.texto }}
        </p>
        <div class="comentario-stats">
            <form action="{{ url_for('post_routes.reaccionar_comentario', comentario_id=c.id) }}" method="POST" style="margin: 0;">
                <button type="submit" class="btn-like-mini">🤍</button>
            </form>
            <span class="comentario-likes-count">0</span>
        </div>
    </div>
    """, c={'username': nuevo_comentario[0], 'texto': nuevo_comentario[1], 'id': nuevo_comentario[2]})

    return jsonify(status="success", html=html)

# ==================== LIKES POSTS ====================
@post_routes.route("/reaccionar/<int:post_id>", methods=["POST"])
def reaccionar(post_id):
    if 'user_id' not in session:
        return jsonify(status="error", message="No login"), 401
    
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM reacciones WHERE usuario_id=%s AND post_id=%s", (user_id, post_id))
    existe = cur.fetchone()

    if existe:
        cur.execute("DELETE FROM reacciones WHERE id=%s", (existe[0],))
        accion = "removed"
    else:
        cur.execute("INSERT INTO reacciones (usuario_id, post_id) VALUES (%s, %s)", (user_id, post_id))
        accion = "added"

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM reacciones WHERE post_id=%s", (post_id,))
    total = cur.fetchone()[0]
    cur.close()
    conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(status="success", accion=accion, total=total)
    
    return redirect(request.referrer or url_for('main_routes.index'))

# ==================== LIKES COMENTARIOS ====================
@post_routes.route('/reaccionar_comentario/<int:comentario_id>', methods=['POST'])
def reaccionar_comentario(comentario_id):
    if 'user_id' not in session:
        return jsonify(status="error", message="No login"), 401
    
    usuario_id = session['user_id']
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT id FROM likes_comentarios WHERE usuario_id=%s AND comentario_id=%s", (usuario_id, comentario_id))
    like_existente = cur.fetchone()

    if like_existente:
        cur.execute("DELETE FROM likes_comentarios WHERE id=%s", (like_existente[0],))
        accion = "removed"
    else:
        cur.execute("INSERT INTO likes_comentarios (usuario_id, comentario_id) VALUES (%s, %s)", (usuario_id, comentario_id))
        accion = "added"

    db.commit()
    # Contar likes actualizados
    cur.execute("SELECT COUNT(*) FROM likes_comentarios WHERE comentario_id=%s", (comentario_id,))
    total = cur.fetchone()[0]
    cur.close()
    db.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(status="success", accion=accion, total=total)
    
    return redirect(request.referrer or url_for('main_routes.index'))

@post_routes.route('/borrar_comentario/<int:comentario_id>', methods=['POST'])
def borrar_comentario(comentario_id):
    if 'user_id' not in session:
        return jsonify(status="error", message="No login"), 401

    usuario_id = session['user_id']
    db = get_db()
    cur = db.cursor()

    # Verificar que el comentario pertenece al usuario
    cur.execute("SELECT user_id FROM comentarios WHERE id=%s", (comentario_id,))
    row = cur.fetchone()
    if not row or row[0] != usuario_id:
        cur.close()
        db.close()
        return jsonify(status="error", message="No puedes borrar este comentario"), 403

    # Borrar el comentario
    cur.execute("DELETE FROM comentarios WHERE id=%s", (comentario_id,))
    db.commit()
    cur.close()
    db.close()

    return jsonify(status="success", comentario_id=comentario_id)