from flask import Flask
from routes.auth_routes import auth_routes
from routes.main_routes import main_routes
from routes.post_routes import post_routes
from routes.admin_routes import admin_routes

def create_app():
    app = Flask(__name__)
    app.secret_key = "TU_CLAVE_SECRETA"

    # Registrar blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(main_routes)
    app.register_blueprint(post_routes)
    app.register_blueprint(admin_routes)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
