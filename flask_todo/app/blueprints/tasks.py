from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Task, Category, Project
from ..schemas import TaskInSchema, TaskOutSchema

blp = Blueprint("Tasks", "tasks", url_prefix="/tasks", description="Tâches (Todo)")

@blp.route("/")
class TaskListResource(MethodView):
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
class TaskDetailResource(MethodView):
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