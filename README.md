# Cours Complet Flask – De Zéro à API Todo Pro (JWT, OTP, Email, Swagger & ReDoc)

## Table des matières

1. [Introduction & Objectifs](#introduction--objectifs)
2. [Pré-requis & Installation](#pré-requis--installation)
3. [Créer le projet & l’architecture](#créer-le-projet--larchitecture)
4. [Configuration & Extensions Flask](#configuration--extensions-flask)
5. [Modèles (User, OTP, Category, Project, Task)](#modèles-user-otp-category-project-task)
6. [Schémas (Marshmallow) & Validation](#schémas-marshmallow--validation)
7. [Utilitaires : Hash, Emails, Tokens, OTP](#utilitaires--hash-emails-tokens-otp)
8. [Blueprint Auth : Register, Confirm Email, Login + OTP, JWT, Reset Password](#blueprint-auth--register-confirm-email-login--otp-jwt-reset-password)
9. [Blueprint Users : Profil](#blueprint-users--profil)
10. [Blueprints Category, Project, Task (CRUD protégés)](#blueprints-category-project-task-crud-protégés)
11. [Documentation OpenAPI : Swagger & ReDoc](#documentation-openapi--swagger--redoc)
12. [Migrations & Lancement](#migrations--lancement)
13. [Scénario de test (cURL/Postman)](#scénario-de-test-curlpostman)
14. [Aller plus loin (sécurité, déploiement, CI)](#aller-plus-loin-sécurité-déploiement-ci)

---

## Introduction & Objectifs

À la fin de ce cours, vous saurez :

* Installer et configurer **Flask** et ses extensions clés (SQLAlchemy, Migrate, JWT, Mail, Smorest/Marshmallow).
* Concevoir une **API REST propre** avec **Blueprints** et **App Factory**.
* Mettre en place un **authentification complète** : inscription, **confirmation par email**, **OTP**, **JWT (access/refresh)**, **réinitialisation de mot de passe**.
* Créer des **endpoints CRUD** protégés (profil, catégories, projets, tâches).
* Générer une **documentation OpenAPI** (Swagger UI & ReDoc) prête pour vos étudiants/consommateurs.

---

## Pré-requis & Installation

### Outils nécessaires

* Python 3.11+
* Git (facultatif)
* Un éditeur (VS Code conseillé)
* Un serveur SMTP de dev (au choix) :

  * **Console SMTP** (simple) : `python -m smtpd -c DebuggingServer -n localhost:1025` (ou MailHog/Mailtrap)
* (Facultatif) PostgreSQL pour prod — **on utilisera SQLite en dev**.

### Créer un environnement

```bash
# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### requirements.txt (copiez/collez)

```txt
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Flask-JWT-Extended==4.6.0
Flask-Smorest==0.44.0
marshmallow==3.21.3
marshmallow-sqlalchemy==1.0.0
python-dotenv==1.0.1
itsdangerous==2.2.0
Flask-Mail==0.9.1
email-validator==2.2.0
```

Installez :

```bash
pip install -r requirements.txt
```

---

## Créer le projet & l’architecture

Arborescence **simple & propre** :

```
flask_todo/
├─ app/
│  ├─ __init__.py
│  ├─ extensions.py
│  ├─ config.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ utils.py
│  └─ blueprints/
│     ├─ auth.py
│     ├─ users.py
│     ├─ categories.py
│     ├─ projects.py
│     └─ tasks.py
├─ migrations/           (créé par Flask-Migrate)
├─ .env
├─ requirements.txt
├─ wsgi.py
└─ README.md
```

---

## Configuration & Extensions Flask

### `.env` (dev)

```ini
FLASK_ENV=development
FLASK_APP=wsgi.py
SECRET_KEY=dev-secret-change-me
JWT_SECRET_KEY=dev-jwt-secret-change-me
SQLALCHEMY_DATABASE_URI=sqlite:///dev.db
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=false
MAIL_USE_SSL=false
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=no-reply@example.com
API_TITLE=Todo API
API_VERSION=1.0.0
```

> En prod : changez les secrets, utilisez PostgreSQL et un vrai SMTP.

### `app/extensions.py`

```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_smorest import Api
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
api = Api()
mail = Mail()
```

### `app/config.py`

```python
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-too")
    PROPAGATE_EXCEPTIONS = True

    # Flask-Smorest / OpenAPI
    API_TITLE = os.getenv("API_TITLE", "Todo API")
    API_VERSION = os.getenv("API_VERSION", "1.0.0")
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    OPENAPI_REDOC_PATH = "/redoc"
    OPENAPI_REDOC_URL = "https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 1025))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@example.com")
```

### `app/__init__.py` (App Factory + Blueprints)

```python
from flask import Flask
from dotenv import load_dotenv
from .extensions import db, migrate, jwt, api, mail
from .config import Config

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    api.init_app(app)

    # Register blueprints (Smorest)
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
```

### `wsgi.py`

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
```

---

## Modèles (User, OTP, Category, Project, Task)

### `app/models.py`

```python
from datetime import datetime, timedelta
from .extensions import db

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class User(BaseModel):
    __tablename__ = "users"
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    username = db.Column(db.String(80), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    email_confirmed = db.Column(db.Boolean, default=False)

    tasks = db.relationship("Task", backref="owner", lazy="dynamic")
    projects = db.relationship("Project", backref="owner", lazy="dynamic")

class OTPCode(BaseModel):
    __tablename__ = "otp_codes"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)  # "login" | "email_confirm" | "password_reset"
    code_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    consumed_at = db.Column(db.DateTime)

    user = db.relationship("User")

class Category(BaseModel):
    __tablename__ = "categories"
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

class Project(BaseModel):
    __tablename__ = "projects"
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    tasks = db.relationship("Task", backref="project", lazy="dynamic")

class Task(BaseModel):
    __tablename__ = "tasks"
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_done = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)       # propriétaire
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
```

---

## Schémas (Marshmallow) & Validation

### `app/schemas.py`

```python
from marshmallow import Schema, fields, validates, ValidationError
from email_validator import validate_email, EmailNotValidError

# --- Auth ---
class RegisterSchema(Schema):
    email = fields.Str(required=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

    @validates("email")
    def validate_email(self, value):
        try:
            validate_email(value)
        except EmailNotValidError as e:
            raise ValidationError(str(e))

class LoginSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

class OTPVerifySchema(Schema):
    email = fields.Str(required=True)
    code = fields.Str(required=True)

class EmailOnlySchema(Schema):
    email = fields.Str(required=True)

class PasswordResetSchema(Schema):
    token = fields.Str(required=True)
    new_password = fields.Str(required=True)

# --- Users ---
class UserOutSchema(Schema):
    id = fields.Int()
    email = fields.Str()
    username = fields.Str()
    full_name = fields.Str()
    email_confirmed = fields.Bool()

class UserUpdateSchema(Schema):
    full_name = fields.Str()
    username = fields.Str()

# --- Category/Project/Task ---
class CategoryInSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str()

class CategoryOutSchema(CategoryInSchema):
    id = fields.Int()

class ProjectInSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str()

class ProjectOutSchema(ProjectInSchema):
    id = fields.Int()

class TaskInSchema(Schema):
    title = fields.Str(required=True)
    description = fields.Str()
    is_done = fields.Bool()
    due_date = fields.DateTime(allow_none=True)
    category_id = fields.Int(allow_none=True)
    project_id = fields.Int(allow_none=True)

class TaskOutSchema(TaskInSchema):
    id = fields.Int()
```

---

## Utilitaires : Hash, Emails, Tokens, OTP

### `app/utils.py`

```python
import secrets
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import mail, db
from .models import OTPCode, User

# --- Password Hashing ---
def hash_password(pwd: str) -> str:
    return generate_password_hash(pwd)

def verify_password(pwd: str, pwd_hash: str) -> bool:
    return check_password_hash(pwd_hash, pwd)

# --- Timed Tokens (email confirm / reset password) ---
def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

def generate_token(data: dict, salt: str) -> str:
    return _serializer().dumps(data, salt=salt)

def verify_token(token: str, salt: str, max_age_seconds: int = 3600) -> dict:
    try:
        return _serializer().loads(token, salt=salt, max_age=max_age_seconds)
    except SignatureExpired:
        raise ValueError("Token expiré")
    except BadSignature:
        raise ValueError("Token invalide")

# --- Email ---
def send_email(subject: str, recipients: list[str], body: str, html: str | None = None):
    msg = Message(subject=subject, recipients=recipients, body=body, html=html)
    mail.send(msg)

# --- OTP ---
def create_and_send_otp(user: User, purpose: str = "login") -> None:
    # 6 chiffres
    code = f"{secrets.randbelow(10**6):06d}"
    code_hash = hash_password(code)
    otp = OTPCode(user_id=user.id, purpose=purpose, code_hash=code_hash,
                  expires_at=datetime.utcnow() + timedelta(minutes=10))
    db.session.add(otp)
    db.session.commit()

    send_email(
        subject="[TodoAPI] Votre code OTP",
        recipients=[user.email],
        body=f"Votre code OTP est : {code} (valide 10 minutes).",
    )

def verify_otp(user: User, code: str, purpose: str = "login") -> bool:
    otp = (OTPCode.query
           .filter_by(user_id=user.id, purpose=purpose, consumed_at=None)
           .order_by(OTPCode.created_at.desc())
           .first())
    if not otp:
        return False
    if otp.expires_at < datetime.utcnow():
        return False
    return verify_password(code, otp.code_hash)

def consume_latest_otp(user: User, purpose: str = "login") -> None:
    otp = (OTPCode.query
           .filter_by(user_id=user.id, purpose=purpose, consumed_at=None)
           .order_by(OTPCode.created_at.desc())
           .first())
    if otp:
        otp.consumed_at = datetime.utcnow()
        db.session.commit()
```

---

## Blueprint Auth : Register, Confirm Email, Login + OTP, JWT, Reset Password

### Concepts

* **Inscription** → on enregistre l’utilisateur **non confirmé**, puis on **envoie un email de confirmation** avec un **token** (itsdangerous).
* **Confirmation** → l’utilisateur clique (ou envoie le token) pour activer `email_confirmed=True`.
* **Login** → vérifie email & mot de passe, **envoie un OTP par email** (2FA), puis l’utilisateur appelle **/verify-otp** → on renvoie **access & refresh JWT**.
* **Refresh** → renvoie un nouvel **access token**.
* **Reset password** → 2 étapes : demander un lien (token), puis soumettre le nouveau mot de passe avec ce token.

### `app/blueprints/auth.py`

```python
from flask_smorest import Blueprint, abort
from flask import url_for, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User
from ..schemas import (RegisterSchema, LoginSchema, OTPVerifySchema, EmailOnlySchema, PasswordResetSchema, UserOutSchema)
from ..utils import (hash_password, verify_password, generate_token, verify_token,
                     send_email, create_and_send_otp, verify_otp, consume_latest_otp)

blp = Blueprint("Auth", "auth", url_prefix="/auth", description="Endpoints d'authentification")

@blp.route("/register")
class RegisterResource:
    @blp.arguments(RegisterSchema)
    @blp.response(201, UserOutSchema)
    def post(self, data):
        user = User(email=data["email"].lower(),
                    username=data["username"],
                    password_hash=hash_password(data["password"]))
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(409, message="Email ou username déjà utilisé")

        # Générer token de confirmation
        token = generate_token({"email": user.email}, salt="email-confirm")
        confirm_url = url_for("Auth.ConfirmEmailResource", token=token, _external=True)
        send_email(
            subject="[TodoAPI] Confirmez votre email",
            recipients=[user.email],
            body=f"Bienvenue ! Confirmez votre email : {confirm_url}"
        )
        return user

@blp.route("/confirm/<string:token>")
class ConfirmEmailResource:
    @blp.response(200, UserOutSchema)
    def get(self, token):
        data = verify_token(token, salt="email-confirm", max_age_seconds=3600*24)
        user = User.query.filter_by(email=data["email"].lower()).first_or_404()
        user.email_confirmed = True
        db.session.commit()
        return user

@blp.route("/resend-confirmation")
class ResendConfirmResource:
    @blp.arguments(EmailOnlySchema)
    @blp.response(200, UserOutSchema)
    def post(self, data):
        user = User.query.filter_by(email=data["email"].lower()).first()
        if not user:
            abort(404, message="Utilisateur introuvable")
        token = generate_token({"email": user.email}, salt="email-confirm")
        confirm_url = url_for("Auth.ConfirmEmailResource", token=token, _external=True)
        send_email("[TodoAPI] Confirmation", [user.email], f"Confirmez votre email : {confirm_url}")
        return user

@blp.route("/login")
class LoginResource:
    @blp.arguments(LoginSchema)
    @blp.response(200, description="OTP envoyé si credentials valides")
    def post(self, data):
        user = User.query.filter_by(email=data["email"].lower()).first()
        if not user or not verify_password(data["password"], user.password_hash):
            abort(401, message="Identifiants invalides")
        if not user.email_confirmed:
            abort(403, message="Email non confirmé. Veuillez confirmer votre email.")

        # Envoi OTP pour 2FA
        create_and_send_otp(user, purpose="login")
        return {"message": "OTP envoyé par email. Utilisez /auth/verify-otp."}

@blp.route("/verify-otp")
class VerifyOTPResource:
    @blp.arguments(OTPVerifySchema)
    @blp.response(200, description="Retourne access/refresh JWT")
    def post(self, data):
        user = User.query.filter_by(email=data["email"].lower()).first()
        if not user:
            abort(404, message="Utilisateur introuvable")
        if not verify_otp(user, data["code"], purpose="login"):
            abort(400, message="OTP invalide ou expiré")
        consume_latest_otp(user, purpose="login")

        access = create_access_token(identity=user.id, additional_claims={"username": user.username})
        refresh = create_refresh_token(identity=user.id)
        return {"access_token": access, "refresh_token": refresh}

@blp.route("/refresh")
class RefreshResource:
    @jwt_required(refresh=True)
    @blp.response(200)
    def post(self):
        user_id = get_jwt_identity()
        access = create_access_token(identity=user_id)
        return {"access_token": access}

@blp.route("/request-password-reset")
class RequestPasswordResetResource:
    @blp.arguments(EmailOnlySchema)
    @blp.response(200)
    def post(self, data):
        user = User.query.filter_by(email=data["email"].lower()).first()
        if not user:
            abort(404, message="Utilisateur introuvable")
        token = generate_token({"email": user.email}, salt="password-reset")
        reset_url = url_for("Auth.PerformPasswordResetResource", _external=True) + f"?token={token}"
        send_email("[TodoAPI] Réinitialisation de mot de passe", [user.email],
                   f"Réinitialisez votre mot de passe ici : {reset_url}")
        return {"message": "Email de réinitialisation envoyé."}

@blp.route("/reset-password")
class PerformPasswordResetResource:
    @blp.arguments(PasswordResetSchema)
    @blp.response(200)
    def post(self, data):
        # token & new_password dans le corps
        payload = verify_token(data["token"], salt="password-reset", max_age_seconds=3600)
        user = User.query.filter_by(email=payload["email"].lower()).first_or_404()
        user.password_hash = hash_password(data["new_password"])
        db.session.commit()
        return {"message": "Mot de passe mis à jour."}
```

---

## Blueprint Users : Profil

### `app/blueprints/users.py`

```python
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import User
from ..schemas import UserOutSchema, UserUpdateSchema

blp = Blueprint("Users", "users", url_prefix="/users", description="Profil utilisateur")

@blp.route("/me")
class MeResource:
    @jwt_required()
    @blp.response(200, UserOutSchema)
    def get(self):
        user = User.query.get_or_404(get_jwt_identity())
        return user

    @jwt_required()
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserOutSchema)
    def patch(self, data):
        user = User.query.get_or_404(get_jwt_identity())
        if "full_name" in data:
            user.full_name = data["full_name"]
        if "username" in data:
            # Option simple : vérifier collision
            existing = User.query.filter(User.username == data["username"], User.id != user.id).first()
            if existing:
                abort(409, message="Username déjà utilisé")
            user.username = data["username"]
        db.session.commit()
        return user
```

---

## Blueprints Category, Project, Task (CRUD protégés)

### Notes

* **Toutes** ces routes exigent **JWT access**.
* Chaque entité est **scopée par user** (les objets d’un user ne sont pas visibles par un autre).

### `app/blueprints/categories.py`

```python
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Category
from ..schemas import CategoryInSchema, CategoryOutSchema

blp = Blueprint("Categories", "categories", url_prefix="/categories", description="Catégories de tâches")

@blp.route("/")
class CategoryListResource:
    @jwt_required()
    @blp.response(200, CategoryOutSchema(many=True))
    def get(self):
        uid = get_jwt_identity()
        return Category.query.filter_by(user_id=uid).order_by(Category.name).all()

    @jwt_required()
    @blp.arguments(CategoryInSchema)
    @blp.response(201, CategoryOutSchema)
    def post(self, data):
        uid = get_jwt_identity()
        cat = Category(user_id=uid, **data)
        db.session.add(cat)
        db.session.commit()
        return cat

@blp.route("/<int:cat_id>")
class CategoryDetailResource:
    @jwt_required()
    @blp.response(200, CategoryOutSchema)
    def get(self, cat_id):
        uid = get_jwt_identity()
        cat = Category.query.filter_by(id=cat_id, user_id=uid).first()
        if not cat:
            abort(404, message="Catégorie introuvable")
        return cat

    @jwt_required()
    @blp.arguments(CategoryInSchema)
    @blp.response(200, CategoryOutSchema)
    def put(self, data, cat_id):
        uid = get_jwt_identity()
        cat = Category.query.filter_by(id=cat_id, user_id=uid).first()
        if not cat:
            abort(404, message="Catégorie introuvable")
        cat.name = data["name"]
        cat.description = data.get("description")
        db.session.commit()
        return cat

    @jwt_required()
    @blp.response(204)
    def delete(self, cat_id):
        uid = get_jwt_identity()
        cat = Category.query.filter_by(id=cat_id, user_id=uid).first()
        if not cat:
            abort(404, message="Catégorie introuvable")
        db.session.delete(cat)
        db.session.commit()
        return ""
```

### `app/blueprints/projects.py`

```python
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Project
from ..schemas import ProjectInSchema, ProjectOutSchema

blp = Blueprint("Projects", "projects", url_prefix="/projects", description="Projets")

@blp.route("/")
class ProjectListResource:
    @jwt_required()
    @blp.response(200, ProjectOutSchema(many=True))
    def get(self):
        uid = get_jwt_identity()
        return Project.query.filter_by(user_id=uid).order_by(Project.created_at.desc()).all()

    @jwt_required()
    @blp.arguments(ProjectInSchema)
    @blp.response(201, ProjectOutSchema)
    def post(self, data):
        uid = get_jwt_identity()
        proj = Project(user_id=uid, **data)
        db.session.add(proj)
        db.session.commit()
        return proj

@blp.route("/<int:proj_id>")
class ProjectDetailResource:
    @jwt_required()
    @blp.response(200, ProjectOutSchema)
    def get(self, proj_id):
        uid = get_jwt_identity()
        proj = Project.query.filter_by(id=proj_id, user_id=uid).first()
        if not proj:
            abort(404, message="Projet introuvable")
        return proj

    @jwt_required()
    @blp.arguments(ProjectInSchema)
    @blp.response(200, ProjectOutSchema)
    def put(self, data, proj_id):
        uid = get_jwt_identity()
        proj = Project.query.filter_by(id=proj_id, user_id=uid).first()
        if not proj:
            abort(404, message="Projet introuvable")
        proj.name = data["name"]
        proj.description = data.get("description")
        db.session.commit()
        return proj

    @jwt_required()
    @blp.response(204)
    def delete(self, proj_id):
        uid = get_jwt_identity()
        proj = Project.query.filter_by(id=proj_id, user_id=uid).first()
        if not proj:
            abort(404, message="Projet introuvable")
        db.session.delete(proj)
        db.session.commit()
        return ""
```

### `app/blueprints/tasks.py`

```python
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Task, Category, Project
from ..schemas import TaskInSchema, TaskOutSchema

blp = Blueprint("Tasks", "tasks", url_prefix="/tasks", description="Tâches (Todo)")

@blp.route("/")
class TaskListResource:
    @jwt_required()
    @blp.response(200, TaskOutSchema(many=True))
    def get(self):
        uid = get_jwt_identity()
        return Task.query.filter_by(user_id=uid).order_by(Task.created_at.desc()).all()

    @jwt_required()
    @blp.arguments(TaskInSchema)
    @blp.response(201, TaskOutSchema)
    def post(self, data):
        uid = get_jwt_identity()

        # Vérifications simples (ownership)
        if data.get("category_id"):
            if not Category.query.filter_by(id=data["category_id"], user_id=uid).first():
                abort(400, message="Catégorie invalide")
        if data.get("project_id"):
            if not Project.query.filter_by(id=data["project_id"], user_id=uid).first():
                abort(400, message="Projet invalide")

        task = Task(user_id=uid, **data)
        db.session.add(task)
        db.session.commit()
        return task

@blp.route("/<int:task_id>")
class TaskDetailResource:
    @jwt_required()
    @blp.response(200, TaskOutSchema)
    def get(self, task_id):
        uid = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=uid).first()
        if not task:
            abort(404, message="Tâche introuvable")
        return task

    @jwt_required()
    @blp.arguments(TaskInSchema)
    @blp.response(200, TaskOutSchema)
    def put(self, data, task_id):
        uid = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=uid).first()
        if not task:
            abort(404, message="Tâche introuvable")

        # Re-valider category/project
        if data.get("category_id"):
            if not Category.query.filter_by(id=data["category_id"], user_id=uid).first():
                abort(400, message="Catégorie invalide")
        if data.get("project_id"):
            if not Project.query.filter_by(id=data["project_id"], user_id=uid).first():
                abort(400, message="Projet invalide")

        for k, v in data.items():
            setattr(task, k, v)
        db.session.commit()
        return task

    @jwt_required()
    @blp.response(204)
    def delete(self, task_id):
        uid = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=uid).first()
        if not task:
            abort(404, message="Tâche introuvable")
        db.session.delete(task)
        db.session.commit()
        return ""
```

---

## Documentation OpenAPI : Swagger & ReDoc

Grâce à **Flask-Smorest**, la doc est générée automatiquement à partir des schémas & responses.

* **Swagger UI** : `http://127.0.0.1:5000/docs`
* **ReDoc** : `http://127.0.0.1:5000/redoc`

> Les descriptions/summary s’appuient sur les décorateurs `@blp.response`, `@blp.arguments`, etc., et le texte `description` fourni au Blueprint.

---

## Migrations & Lancement

Initialisez la base et lancez le serveur :

```bash
# 1) Initialiser les migrations
flask db init

# 2) Générer le script de migration (tables User, OTP, Category, Project, Task)
flask db migrate -m "init models"

# 3) Appliquer
flask db upgrade

# 4) Lancer l'app
flask run
```

Démarrez un **SMTP de debug** (si besoin) dans un autre terminal :

```bash
python -m smtpd -c DebuggingServer -n localhost:1025
```

> Chaque email envoyé s’affichera dans la console.

---

## Scénario de test (cURL/Postman)

1. **Register**

```bash
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","username":"alice","password":"Secret123!"}'
```

→ consultez la console SMTP pour le lien de **confirmation**.

2. **Confirmer l’email** (ouvrez l’URL reçue, ex: `/auth/confirm/<token>`).

3. **Login** (déclenche envoi OTP)

```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Secret123!"}'
```

→ vérifiez la console SMTP pour le **code OTP** (6 chiffres).

4. **Vérifier OTP & recevoir JWT**

```bash
curl -X POST http://127.0.0.1:5000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","code":"123456"}'
```

→ récupérez `access_token` et `refresh_token`.

5. **Créer une catégorie**

```bash
curl -X POST http://127.0.0.1:5000/categories/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Perso","description":"Tâches personnelles"}'
```

6. **Créer un projet**

```bash
curl -X POST http://127.0.0.1:5000/projects/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Projet YouTube","description":"Demo Flask cours"}'
```

7. **Créer une tâche liée au projet & à la catégorie**

```bash
curl -X POST http://127.0.0.1:5000/tasks/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Préparer miniatures","project_id":1,"category_id":1}'
```

8. **Voir le profil**

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" http://127.0.0.1:5000/users/me
```

9. **Réinitialiser le mot de passe (demande)**

```bash
curl -X POST http://127.0.0.1:5000/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com"}'
```

→ récupérez le `token` de la console SMTP, puis :

```bash
curl -X POST http://127.0.0.1:5000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token":"<TOKEN>","new_password":"NewPass123!"}'
```

10. **Docs**

* Swagger: `http://127.0.0.1:5000/docs`
* ReDoc: `http://127.0.0.1:5000/redoc`

---

## Aller plus loin (sécurité, déploiement, CI)

* **Sécurité**

  * Utilisez **HTTPS** en prod.
  * Stockez les secrets via variables d’environnement (pas dans le repo).
  * Hash OTP (fait) & **expiration courte** (10 min).
  * Limiter la fréquence de `/login` & `/verify-otp` (rate limiting).
* **Base de données**

  * Passez à PostgreSQL (SQLALCHEMY\_DATABASE\_URI comme `postgresql+psycopg2://user:pwd@host:5432/db`).
* **Emails**

  * Utilisez Mailtrap, SendGrid ou tout SMTP fiable.
* **Déploiement**

  * Gunicorn + Nginx (Docker conseillé).
* **Tests & CI**

  * Ajoutez des tests `pytest` ou `unittest`, GitHub Actions, etc.

---

## Conclusion

Vous avez une **API Flask professionnelle**, claire et pédagogique : **inscription, confirmation email, OTP, JWT, reset password, profil, catégories, projets, tâches**, avec une **documentation Swagger & ReDoc** prête pour vos étudiants.
