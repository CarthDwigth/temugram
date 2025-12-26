from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import auth 
import os
import psycopg2
import requests
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = 'clave_secreta_muy_segura'

# --- 1. CONEXIÓN INTELIGENTE ---
def get_db_connection():
    url = os.getenv('DATABASE_URL') 
    if url: 
        result = urlparse(url)
        return psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
    else: 
        import sqlite3
        return sqlite3.connect('temugram.db')

# --- 2. SUBIDA DE FOTOS A LA NUBE ---
def subir_foto_nube(archivo):
    api_key = "6d207e02198a847aa98d0a2a901485a5" 
    url = "https://freeimage.host/api/1/upload"
    payload = {"key": api_key, "action": "upload", "format": "json"}
    archivo.seek(0)
    files = {"source": archivo.read()}
    try:
        response = requests.post(url, data=payload, files=files)
        data = response.json()
        return data['image']['url'] if response.status_code == 200 else None
    except Exception as e:
        print(f"Error enviando a FreeImage: {e}")
        return None

# --- 3. INICIALIZAR TABLAS ---
def inicializar_base_de_datos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS posts (id SERIAL PRIMARY KEY, user_id INTEGER, descripcion TEXT, url_foto TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS comentarios (id SERIAL PRIMARY KEY, post_id INTEGER, usuario TEXT, texto TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS reacciones (id SERIAL PRIMARY KEY, post_id INTEGER, user_id INTEGER, tipo TEXT)')
    conn.commit()
    cur.close()
    conn.close()

def obtener_posts():
    conn = get_db_connection()
    cur = conn.cursor()
    query = '''
        SELECT usuarios.username, posts.descripcion, posts.url_foto, posts.id 
        FROM posts 
        JOIN usuarios ON posts.user_id = usuarios.id
        ORDER BY posts.id DESC
    '''
    cur.execute(query)
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return posts

@app.route('/')
def home():
    posts_base = obtener_posts() 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT post_id, usuario, texto FROM comentarios')
    todos_los_comentarios = cur.fetchall()
    cur.execute('SELECT post_id, tipo FROM reacciones')
    todas_las_reacciones = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', posts=posts_base, comentarios=todos_los_comentarios, reacciones=todas_las_reacciones)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if auth.registrar_usuario(u, p):
            user_id = auth.login(u, p) 
            if user_id:
                session['user_id'], session['username'] = user_id, u
                return redirect(url_for('home'))
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        user_id = auth.login(u, p)
        if user_id:
            session['user_id'], session['username'] = user_id, u
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/publicar', methods=['GET', 'POST'])
def publicar():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        url_foto = subir_foto_nube(request.files['foto'])
        if url_foto:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("INSERT INTO posts (user_id, descripcion, url_foto) VALUES (%s, %s, %s)", 
                       (session['user_id'], request.form['descripcion'], url_foto))
            conn.commit(); cur.close(); conn.close()
            return redirect(url_for('home'))
    return render_template('publicar.html')

@app.route('/comentar/<int:post_id>', methods=['POST'])
def comentar(post_id):
    if 'username' not in session: return redirect(url_for('login'))
    texto = request.form.get('texto')
    if texto:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute('INSERT INTO comentarios (post_id, usuario, texto) VALUES (%s, %s, %s)', 
                   (post_id, session['username'], texto))
        conn.commit(); cur.close(); conn.close()
    return redirect(url_for('home'))

@app.route('/borrar/<int:post_id>')
def borrar_post(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor()
    try:
        # Borramos todo lo relacionado al post para evitar errores de integridad
        cur.execute("DELETE FROM reacciones WHERE post_id = %s", (post_id,))
        cur.execute("DELETE FROM comentarios WHERE post_id = %s", (post_id,))
        cur.execute("DELETE FROM posts WHERE id = %s AND user_id = %s", (post_id, session['user_id']))
        conn.commit()
    except Exception as e:
        print(f"Error al borrar: {e}")
    finally:
        cur.close(); conn.close()
    return redirect(url_for('home'))

@app.route('/reaccionar/<int:post_id>/<tipo>')
def reaccionar(post_id, tipo):
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM reacciones WHERE post_id = %s AND user_id = %s", (post_id, user_id))
        cur.execute("INSERT INTO reacciones (post_id, user_id, tipo) VALUES (%s, %s, %s)", (post_id, user_id, tipo))
        conn.commit()
    except Exception as e:
        print(f"Error al reaccionar: {e}")
    finally:
        cur.close(); conn.close()
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

inicializar_base_de_datos()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)