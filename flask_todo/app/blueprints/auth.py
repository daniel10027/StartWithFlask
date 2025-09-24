from flask_smorest import Blueprint, abort
from flask import url_for
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from flask.views import MethodView

from ..extensions import db
from ..models import User
from ..schemas import (RegisterSchema, LoginSchema, OTPVerifySchema, EmailOnlySchema, PasswordResetSchema, UserOutSchema)
from ..utils import (hash_password, verify_password, generate_token, verify_token,
                     send_email, create_and_send_otp, verify_otp, consume_latest_otp)

blp = Blueprint("Auth", "auth", url_prefix="/auth", description="Endpoints d'authentification")

@blp.route("/register")
class RegisterResource(MethodView):
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

        token = generate_token({"email": user.email}, salt="email-confirm")
        confirm_url = url_for("Auth.ConfirmEmailResource", token=token, _external=True)
        send_email("[TodoAPI] Confirmez votre email", [user.email], f"Bienvenue ! Confirmez votre email : {confirm_url}")
        return user

@blp.route("/confirm/<string:token>")
class ConfirmEmailResource(MethodView):
    @blp.response(200, UserOutSchema)
    def get(self, token):
        data = verify_token(token, salt="email-confirm", max_age_seconds=3600*24)
        user = User.query.filter_by(email=data["email"].lower()).first_or_404()
        user.email_confirmed = True
        db.session.commit()
        return user

@blp.route("/resend-confirmation")
class ResendConfirmResource(MethodView):
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
class LoginResource(MethodView):
    @blp.arguments(LoginSchema)
    @blp.response(200, description="OTP envoyé si credentials valides")
    def post(self, data):
        user = User.query.filter_by(email=data["email"].lower()).first()
        if not user or not verify_password(data["password"], user.password_hash):
            abort(401, message="Identifiants invalides")
        if not user.email_confirmed:
            abort(403, message="Email non confirmé. Veuillez confirmer votre email.")
        create_and_send_otp(user, purpose="login")
        return {"message": "OTP envoyé par email. Utilisez /auth/verify-otp."}

@blp.route("/verify-otp")
class VerifyOTPResource(MethodView):
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
class RefreshResource(MethodView):
    @jwt_required(refresh=True)
    @blp.response(200)
    def post(self):
        user_id = get_jwt_identity()
        access = create_access_token(identity=str(user_id))
        return {"access_token": access}

@blp.route("/request-password-reset")
class RequestPasswordResetResource(MethodView):
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
class PerformPasswordResetResource(MethodView):
    @blp.arguments(PasswordResetSchema)
    @blp.response(200)
    def post(self, data):
        payload = verify_token(data["token"], salt="password-reset", max_age_seconds=3600)
        user = User.query.filter_by(email=payload["email"].lower()).first_or_404()
        user.password_hash = hash_password(data["new_password"])
        db.session.commit()
        return {"message": "Mot de passe mis à jour."}
