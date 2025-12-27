from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import auth 
import os
import psycopg2
import requests
from urllib.parse import urlparse

app = Flask(__name__, static_folder='static', static_url_path='/static')
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

def inicializar_base_de_datos():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS emoji_perfil TEXT DEFAULT '👤'")
        conn.commit()
    except:
        conn.rollback()
    
    # 1. Aseguramos las tablas base
    cur.execute('CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS posts (id SERIAL PRIMARY KEY, user_id INTEGER, descripcion TEXT, url_foto TEXT)')
    
    # 2. Forzamos la creación de columnas nuevas una por una
    columnas = [
        ("rol", "TEXT DEFAULT 'Usuario'"),
        ("fecha_registro", "TEXT DEFAULT '26/12/2025'")
    ]
    
    for nombre_col, definicion in columnas:
        try:
            # Intentamos añadir la columna
            cur.execute(f"ALTER TABLE usuarios ADD COLUMN {nombre_col} {definicion}")
            conn.commit() # Confirmamos después de cada columna
            print(f"Columna {nombre_col} añadida con éxito.")
        except Exception as e:
            conn.rollback() # Si falla (porque ya existe), limpiamos el error para seguir
            print(f"La columna {nombre_col} ya existía o saltó este error: {e}")

    # 3. Aseguramos el rango de Admin para ti
    cur.execute("UPDATE usuarios SET rol = 'Admin' WHERE username = 'Carth'")
    conn.commit()
    
    cur.close()
    conn.close()

def obtener_posts():
    conn = get_db_connection(); cur = conn.cursor()
    # Añadimos usuarios.emoji_perfil a la consulta (será el p[5])
    query = '''
        SELECT usuarios.username, posts.descripcion, posts.url_foto, posts.id, usuarios.rol, usuarios.emoji_perfil
        FROM posts 
        JOIN usuarios ON posts.user_id = usuarios.id
        ORDER BY posts.id DESC
    '''
    cur.execute(query)
    posts = cur.fetchall()
    cur.close(); conn.close()
    return posts

def obtener_metricas():
    conn = get_db_connection()
    cur = conn.cursor()
    # Contamos el total de registros en todas tus tablas
    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM usuarios) + 
            (SELECT COUNT(*) FROM posts) + 
            (SELECT COUNT(*) FROM comentarios) + 
            (SELECT COUNT(*) FROM reacciones)
    """)
    total_filas = cur.fetchone()[0]
    cur.close()
    conn.close()

    # Estimación para Render Free (Límite 1GB es inmenso para texto, 
    # pero podemos simular un límite de 10,000 filas para el dashboard)
    limite_filas = 10000 
    porcentaje_db = min((total_filas / limite_filas) * 100, 100)
    
    return {
        'db_porcentaje': round(porcentaje_db, 1),
        'total_filas': total_filas,
        'limite_filas': limite_filas
    }

@app.route('/')
def home():
    metricas = obtener_metricas()
    posts_base = obtener_posts()
    
    conn = get_db_connection(); cur = conn.cursor()
    
    # 1. Traemos usuarios para la sidebar incluyendo su emoji (u[3])
    cur.execute("SELECT username, rol, fecha_registro, emoji_perfil FROM usuarios ORDER BY rol DESC")
    lista_usuarios = cur.fetchall()
    
    # 2. Traemos comentarios UNIDOS con la tabla usuarios para sacar el emoji del comentador
    cur.execute('''
        SELECT comentarios.post_id, comentarios.usuario, comentarios.texto, usuarios.emoji_perfil
        FROM comentarios
        JOIN usuarios ON comentarios.usuario = usuarios.username
    ''')
    todos_los_comentarios = cur.fetchall() # El emoji será c[3]
    
    cur.execute('SELECT post_id, tipo FROM reacciones')
    todas_las_reacciones = cur.fetchall()
    cur.close(); conn.close()

    return render_template('index.html', 
                           posts=posts_base, 
                           usuarios_sidebar=lista_usuarios, 
                           comentarios=todos_los_comentarios, 
                           reacciones=todas_las_reacciones, 
                           metricas=metricas)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        emoji = request.form.get('emoji', '👤') 

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # CAMBIAMOS 'emoji' por 'emoji_perfil' para que coincida con tu ALTER TABLE
            cur.execute("INSERT INTO usuarios (username, password, rol, emoji_perfil) VALUES (%s, %s, %s, %s)",
                        (username, password, 'Usuario', emoji))
            conn.commit()
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            return f"Error: {e}"
        finally:
            cur.close(); conn.close()
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        # Buscamos al usuario en la base de datos de la nube
        cur.execute("SELECT id, username FROM usuarios WHERE username = %s AND password = %s", (u, p))
        user = cur.fetchone()
        cur.close(); conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('home'))
        else:
            return "❌ Error: Usuario o contraseña no encontrados en la base de datos."
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

@app.route('/borrar_post/<int:post_id>')
def borrar_post(post_id):
    # Seguridad de nivel Admin
    if session.get('username') != 'Carth':
        return "No tienes permisos para hacer esto", 403

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Borramos comentarios y reacciones vinculados al post
        cur.execute("DELETE FROM comentarios WHERE post_id = %s", (post_id,))
        cur.execute("DELETE FROM reacciones WHERE post_id = %s", (post_id,))
        
        # 2. Borramos el post
        cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        
        conn.commit()
    except Exception as e:
        print(f"Error al borrar: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        
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

@app.route('/perfil/<username>')
def perfil(username):
    conn = get_db_connection(); cur = conn.cursor()
    # Traemos el emoji_perfil y el rol también
    cur.execute("SELECT id, emoji_perfil, rol FROM usuarios WHERE username = %s", (username,))
    user_data = cur.fetchone()
    
    if not user_data:
        cur.close(); conn.close()
        return "Usuario no encontrado", 404
        
    user_id, emoji, rol = user_data[0], user_data[1], user_data[2]
    
    cur.execute('''
        SELECT usuarios.username, posts.descripcion, posts.url_foto, posts.id, usuarios.rol
        FROM posts 
        JOIN usuarios ON posts.user_id = usuarios.id
        WHERE user_id = %s ORDER BY posts.id DESC
    ''', (user_id,))
    user_posts = cur.fetchall()
    cur.close(); conn.close()
    
    return render_template('perfil.html', username=username, emoji=emoji, rol=rol, posts=user_posts)

@app.route('/admin/panel')
def admin_panel():
    # Solo permitimos la entrada si el usuario logueado es Admin
    if 'username' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verificamos el rol del usuario actual
    cur.execute("SELECT rol FROM usuarios WHERE username = %s", (session['username'],))
    user_rol = cur.fetchone()[0]
    
    if user_rol != 'Admin':
        cur.close(); conn.close()
        return "Acceso Denegado: No tienes permisos de Administrador", 403

    # Traemos todos los usuarios para mostrar en la lista
    cur.execute("SELECT id, username, rol FROM usuarios ORDER BY username ASC")
    usuarios_lista = cur.fetchall()
    cur.close(); conn.close()
    
    return render_template('admin_panel.html', usuarios=usuarios_lista)

@app.route('/admin/cambiar_rol', methods=['POST'])
def cambiar_rol():
    if 'username' not in session: return redirect(url_for('login'))
    
    # Verificación de seguridad (doble check de Admin)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT rol FROM usuarios WHERE username = %s", (session['username'],))
    if cur.fetchone()[0] != 'Admin':
        return "No autorizado", 403

    nuevo_rol = request.form.get('rol')
    usuario_id = request.form.get('usuario_id')
    
    cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, usuario_id))
    conn.commit(); cur.close(); conn.close()
    
    return redirect(url_for('admin_panel'))

@app.route('/cambiar_emoji', methods=['POST'])
def cambiar_emoji():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    nuevo_emoji = request.form.get('emoji')
    if nuevo_emoji:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET emoji_perfil = %s WHERE id = %s", (nuevo_emoji, session['user_id']))
        conn.commit()
        cur.close(); conn.close()
        
    return redirect(url_for('perfil', username=session['username']))

@app.route('/reset_secreto', methods=['GET', 'POST'])
def reset_secreto():
    if request.method == 'POST':
        user = request.form.get('username')
        nueva_p = request.form.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()
        # Actualizamos la clave y nos aseguramos de que seas Admin
        cur.execute("UPDATE usuarios SET password = %s, rol = 'Admin' WHERE username = %s", (nueva_p, user))
        conn.commit()
        cur.close(); conn.close()
        return f"✅ Contraseña de {user} actualizada. Ya puedes intentar el login normal."
        
    return '''
        <form method="post" style="background:#15191c; color:white; padding:20px; border-radius:10px; font-family:sans-serif;">
            <h2>🔑 Reset Maestro de TemuGram</h2>
            <input type="text" name="username" placeholder="Usuario (Carth)" required style="display:block; margin:10px 0; padding:10px;">
            <input type="password" name="password" placeholder="Nueva Contraseña" required style="display:block; margin:10px 0; padding:10px;">
            <button type="submit" style="background:#0095f6; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer;">Actualizar Ahora</button>
        </form>
    '''

inicializar_base_de_datos()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)