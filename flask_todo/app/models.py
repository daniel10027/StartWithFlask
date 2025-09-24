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

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))