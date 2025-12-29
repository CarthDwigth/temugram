import auth
import sqlite3

def muro_inicio():
    print("\n--- 📸 MURO DE INICIO (TemuGram) ---")
    with sqlite3.connect('temugram.db') as conn:
        cursor = conn.cursor()
        # Aquí usamos un JOIN para ver el nombre del usuario que subió la foto
        query = '''
            SELECT usuarios.username, posts.descripcion, posts.url_foto 
            FROM posts 
            JOIN usuarios ON posts.user_id = usuarios.id
        '''
        cursor.execute(query)
        posts = cursor.fetchall()
        
        if not posts:
            print("No hay publicaciones aún. ¡Sé el primero!")
        for p in posts:
            print(f"👤 {p[0]}: {p[1]} [Imagen: {p[2]}]")
    print("----------------------------------")

def menu_usuario(user_id, username):
    while True:
        print(f"\nHola @{username}!")
        print("1. Ver Muro")
        print("2. Publicar Foto")
        print("3. Cerrar Sesión")
        opcion = input("Selecciona: ")

        if opcion == "1":
            muro_inicio()
        elif opcion == "2":
            desc = input("Descripción de la foto: ")
            url = input("Nombre del archivo de imagen (ej: foto1.jpg): ")
            with sqlite3.connect('temugram.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO posts (user_id, descripcion, url_foto) VALUES (?, ?, ?)", 
                               (user_id, desc, url))
                conn.commit()
            print("✅ ¡Publicado en TemuGram!")
        elif opcion == "3":
            break

def main():
    while True:
        print("\n--- BIENVENIDO A TEMUGRAM ---")
        print("1. Registrarse")
        print("2. Iniciar Sesión")
        print("3. Salir")
        opcion = input("Selecciona una opción: ")

        if opcion == "1":
            u = input("Nuevo usuario: ")
            p = input("Contraseña: ")
            if auth.registrar_usuario(u, p):
                print("✅ Registro exitoso. Ahora inicia sesión.")
        
        elif opcion == "2":
            u = input("Usuario: ")
            p = input("Contraseña: ")
            user_id = auth.login(u, p)
            if user_id:
                menu_usuario(user_id, u)
            else:
                print("❌ Usuario o contraseña incorrectos.")
        
        elif opcion == "3":
            print("¡Nos vemos!")
            break

if __name__ == "__main__":
    main()