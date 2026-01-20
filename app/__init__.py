from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis

db = SQLAlchemy()
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vagas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
