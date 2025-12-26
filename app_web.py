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

# RUTA 1: El Muro de Inicio
@app.route('/')
def home():
    posts = obtener_posts()
    return render_template('index.html', posts=posts)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)