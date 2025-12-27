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

    # 1. Aseguramos las tablas base y columnas de usuarios
    cur.execute('CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    
    # Añadimos columnas dinámicas a la tabla usuarios
    columnas_usuarios = [
        ("emoji_perfil", "TEXT DEFAULT '👤'"),
        ("rol", "TEXT DEFAULT 'Usuario'"),
        ("fecha_registro", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]
    
    for nombre_col, definicion in columnas_usuarios:
        try:
            cur.execute(f"ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS {nombre_col} {definicion}")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error o ya existe columna {nombre_col}: {e}")

    # 2. NUEVA TABLA: Gestión de Permisos por Rol
    cur.execute('''CREATE TABLE IF NOT EXISTS permisos_roles (
        rol TEXT PRIMARY KEY,
        puede_borrar_fotos BOOLEAN DEFAULT FALSE,
        puede_subir_fotos BOOLEAN DEFAULT TRUE,
        puede_comentar BOOLEAN DEFAULT TRUE,
        puede_borrar_usuarios BOOLEAN DEFAULT FALSE,
        puede_gestionar_roles BOOLEAN DEFAULT FALSE
    )''')

    # Insertamos permisos para los roles predeterminados
    permisos_base = [
        ('Admin', True, True, True, True, True),
        ('Usuario', False, True, True, False, False),
        ('Verificado', False, True, True, False, False)
    ]

    for p in permisos_base:
        cur.execute('''INSERT INTO permisos_roles 
                       (rol, puede_borrar_fotos, puede_subir_fotos, puede_comentar, puede_borrar_usuarios, puede_gestionar_roles) 
                       VALUES (%s, %s, %s, %s, %s, %s) 
                       ON CONFLICT (rol) DO NOTHING''', p)

    # 3. Otras tablas (Posts, Reacciones, etc.)
    cur.execute('CREATE TABLE IF NOT EXISTS posts (id SERIAL PRIMARY KEY, user_id INTEGER, descripcion TEXT, url_foto TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS reacciones (id SERIAL PRIMARY KEY, post_id INTEGER, user_id INTEGER, tipo TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS comentarios (id SERIAL PRIMARY KEY, post_id INTEGER, user_id INTEGER, comentario TEXT)')

    # 4. Aseguramos tu rango Admin
    conn.commit()
    
    print("✅ Base de datos sincronizada con Sistema de Permisos.")
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
    if session.get('username') != 'Carth':
        return redirect(url_for('home'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    # IMPORTANTE: Seleccionamos ID, USERNAME y ROL en ese orden
    cur.execute("SELECT id, username, rol FROM usuarios ORDER BY id ASC")
    usuarios_db = cur.fetchall()
    
    # Obtenemos los roles para la sección de permisos
    cur.execute("SELECT rol, puede_borrar_fotos, puede_borrar_usuarios, puede_gestionar_roles FROM permisos_roles")
    roles_db = cur.fetchall()
    
    cur.close(); conn.close()
    
    # Pasamos las variables con los nombres que usa tu HTML (usuarios y lista_roles)
    return render_template('admin_panel.html', usuarios=usuarios_db, lista_roles=roles_db)

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

@app.route('/admin/actualizar_permisos', methods=['POST'])
def actualizar_permisos():
    if session.get('username') != 'Carth':
        return redirect(url_for('home'))

    rol = request.form.get('rol')
    borrar_f = 'puede_borrar_fotos' in request.form
    borrar_u = 'puede_borrar_usuarios' in request.form
    crear_r = 'puede_gestionar_roles' in request.form

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''UPDATE permisos_roles 
                   SET puede_borrar_fotos = %s, puede_borrar_usuarios = %s, puede_gestionar_roles = %s 
                   WHERE rol = %s''', (borrar_f, borrar_u, crear_r, rol))
    conn.commit()
    cur.close(); conn.close()
    return redirect(url_for('admin_panel'))

# RUTA PARA BORRAR USUARIOS
@app.route('/admin/borrar_usuario/<username_borrar>')
def borrar_usuario(username_borrar):
    if session.get('username') != 'Carth':
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE username = %s", (username_borrar,))
    conn.commit()
    cur.close(); conn.close()
    return redirect(url_for('admin_panel'))

# RUTA PARA CREAR NUEVOS ROLES
@app.route('/admin/crear_nuevo_rol', methods=['POST'])
def crear_nuevo_rol():
    if session.get('username') != 'Carth':
        return redirect(url_for('home'))
    
    nuevo_rol = request.form.get('nombre_rol')
    if nuevo_rol:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO permisos_roles (rol) VALUES (%s) ON CONFLICT DO NOTHING", (nuevo_rol,))
        conn.commit()
        cur.close(); conn.close()
    return redirect(url_for('admin_panel'))

inicializar_base_de_datos()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)