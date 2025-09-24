from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Category
from ..schemas import CategoryInSchema, CategoryOutSchema
from flask.views import MethodView

blp = Blueprint("Categories", "categories", url_prefix="/categories", description="Catégories de tâches")

@blp.route("/")
class CategoryListResource(MethodView):
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
class CategoryDetailResource(MethodView):
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