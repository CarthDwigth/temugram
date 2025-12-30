import os
import requests
import base64
from flask import Blueprint, request, redirect, url_for, session
from db import get_db

post_routes = Blueprint("post_routes", __name__)

@post_routes.route("/crear_post", methods=["POST"])
def crear_post():
    if "user_id" not in session:
        return redirect(url_for("auth_routes.login"))

    descripcion = request.form.get("descripcion")
    file = request.files.get("foto")
    api_key = os.environ.get("FREEIMAGE_API_KEY")

    if file and api_key:
        # 1. Leer la imagen y convertirla a base64 (como pide la mayoría de APIs)
        image_data = base64.b64encode(file.read())
        
        # 2. Enviar a Freeimage (ajusta la URL según su documentación, usualmente es /upload)
        response = requests.post(
            "https://freeimage.host/api/1/upload",
            data={
                "key": api_key,
                "action": "upload",
                "source": image_data,
                "format": "json"
            }
        )
        
        datos_json = response.json()
        
        if response.status_code == 200:
            # 3. Obtener la URL directa de la imagen
            url_foto = datos_json['image']['url']

            # 4. Guardar en PostgreSQL
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO posts (user_id, descripcion, url_foto) VALUES (%s, %s, %s)",
                (session["user_id"], descripcion, url_foto)
            )
            conn.commit()
            cur.close()
            conn.close()

    return redirect(url_for("main_routes.index"))