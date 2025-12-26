from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import auth 
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_muy_segura' # Esto es vital para las sesiones

def obtener_posts():
    with sqlite3.connect('temugram.db') as conn:
        cursor = conn.cursor()
        # IMPORTANTE: Añade posts.id al final
        query = '''
            SELECT usuarios.username, posts.descripcion, posts.url_foto, posts.id 
            FROM posts 
            JOIN usuarios ON posts.user_id = usuarios.id
            ORDER BY posts.id DESC
        '''
        cursor.execute(query)
        return cursor.fetchall()

def init_db():
    with sqlite3.connect('temugram.db') as conn:
        cursor = conn.cursor()
        # Tabla de usuarios (aseguramos que exista)
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
        # Tabla de posts (aseguramos que exista)
        cursor.execute('''CREATE TABLE IF NOT EXISTS posts 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, descripcion TEXT, url_foto TEXT)''')
        # NUEVA: Tabla de comentarios
        cursor.execute('''CREATE TABLE IF NOT EXISTS comentarios (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            post_id INTEGER,
                            usuario TEXT,
                            texto TEXT,
                            FOREIGN KEY (post_id) REFERENCES posts (id))''')
        conn.commit()

# Ejecutamos la creación de tablas al abrir el archivo
init_db()

app.route('/')
def home():
    # Usamos la función que ya tienes arriba que hace el JOIN correctamente
    posts = obtener_posts() 
    
    with sqlite3.connect('temugram.db') as conn:
        cursor = conn.cursor()
        # Obtenemos todos los comentarios
        cursor.execute('SELECT post_id, usuario, texto FROM comentarios')
        todos_los_comentarios = cursor.fetchall()
    
    return render_template('index.html', posts=posts, comentarios=todos_los_comentarios)

# RUTA 2: El Registro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if auth.registrar_usuario(u, p):
            return redirect(url_for('home'))
        else:
            return "Error: El usuario ya existe."
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        user_id = auth.login(u, p) # Usa tu función de auth.py
        
        if user_id:
            session['user_id'] = user_id # Guardamos el ID en la "mochila" de la sesión
            session['username'] = u
            return redirect(url_for('home'))
        else:
            return "❌ Usuario o contraseña incorrectos."
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() # Esto borra toda la información del usuario actual
    return redirect(url_for('home'))

# Configuración de subida
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/publicar', methods=['GET', 'POST'])
def publicar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        file = request.files['foto']
        desc = request.form['descripcion']
        
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Guardamos en la DB
            with sqlite3.connect('temugram.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO posts (user_id, descripcion, url_foto) VALUES (?, ?, ?)", 
                               (session['user_id'], desc, filename))
                conn.commit()
            return redirect(url_for('home'))
            
    return render_template('publicar.html')

@app.route('/borrar/<int:post_id>')
def borrar_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect('temugram.db') as conn:
        cursor = conn.cursor()
        # Verificamos que el post pertenezca al usuario logueado
        cursor.execute("DELETE FROM posts WHERE id = ? AND user_id = ?", (post_id, session['user_id']))
        conn.commit()
        
    return redirect(url_for('home'))

@app.route('/comentar/<int:post_id>', methods=['POST'])
def comentar(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    texto = request.form.get('texto')
    usuario = session['username']
    
    if texto:
        conn = sqlite3.connect('temugram.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO comentarios (post_id, usuario, texto) VALUES (?, ?, ?)', 
                       (post_id, usuario, texto))
        conn.commit()
        conn.close()
    
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)