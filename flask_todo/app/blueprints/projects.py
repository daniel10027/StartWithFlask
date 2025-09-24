from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Project
from ..schemas import ProjectInSchema, ProjectOutSchema

blp = Blueprint("Projects", "projects", url_prefix="/projects", description="Projets")

@blp.route("/")
class ProjectListResource(MethodView):
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
class ProjectDetailResource(MethodView):
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