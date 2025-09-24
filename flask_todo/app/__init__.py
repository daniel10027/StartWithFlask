from flask import Flask
from dotenv import load_dotenv
from .extensions import db, migrate, jwt, api, mail
from .config import Config

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    api.init_app(app)

    from .blueprints.auth import blp as AuthBlp
    from .blueprints.users import blp as UsersBlp
    from .blueprints.categories import blp as CategoriesBlp
    from .blueprints.projects import blp as ProjectsBlp
    from .blueprints.tasks import blp as TasksBlp

    api.register_blueprint(AuthBlp)
    api.register_blueprint(UsersBlp)
    api.register_blueprint(CategoriesBlp)
    api.register_blueprint(ProjectsBlp)
    api.register_blueprint(TasksBlp)

    @app.get("/")
    def index():
        return {"message": "Bienvenue sur l'API Todo (Flask) ✔"}

    return app