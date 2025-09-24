from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import User
from ..schemas import UserOutSchema, UserUpdateSchema

blp = Blueprint("Users", "users", url_prefix="/users", description="Profil utilisateur")

@blp.route("/me")
class MeResource(MethodView):
    @jwt_required()
    @blp.response(200, UserOutSchema)
    def get(self):
        user_id = int(get_jwt_identity())
        user = User.query.get_or_404(user_id)
        return user

    @jwt_required()
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserOutSchema)
    def patch(self, data):
        user_id = int(get_jwt_identity())
        user = User.query.get_or_404(user_id)
        if "full_name" in data:
            user.full_name = data["full_name"]
        if "username" in data:
            existing = User.query.filter(User.username == data["username"], User.id != user.id).first()
            if existing:
                abort(409, message="Username déjà utilisé")
            user.username = data["username"]
        db.session.commit()
        return user