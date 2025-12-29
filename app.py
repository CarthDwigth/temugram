from flask import Flask, session
from config import SECRET_KEY
from routes.auth_routes import auth_routes
from routes.main_routes import main_routes
from routes.post_routes import post_routes
from routes.admin_routes import admin_routes

app = Flask(__name__)
app.secret_key = SECRET_KEY

# actualizar última conexión antes de cada request
@app.before_request
def actualizar_ultima_conexion():
    from services.users import actualizar_ultima_conexion
    actualizar_ultima_conexion(session)

# registrar blueprints
app.register_blueprint(auth_routes)
app.register_blueprint(main_routes)
app.register_blueprint(post_routes)
app.register_blueprint(admin_routes)

if __name__ == '__main__':
    app.run(debug=True)
