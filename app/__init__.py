from flask import Flask
from app.extensions import db, migrate

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vagas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main_bp # pylint: disable=import-outside-toplevel
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
