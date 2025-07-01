from flask import Flask
from datetime import timedelta
from .routes import main

def create_app():
    app = Flask(__name__)
    app.permanent_session_lifetime = timedelta(minutes=30)
    app.config['ALLOW_REGISTRATION'] = True  # Toggle to False to disable
    app.secret_key = 'supersecurekey'
    app.permanent_session_lifetime = timedelta(minutes=30)
    app.register_blueprint(main)
    return app
