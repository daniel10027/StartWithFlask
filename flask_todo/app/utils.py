import secrets
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import mail, db
from .models import OTPCode, User

# Password Hash
def hash_password(pwd: str) -> str:
    return generate_password_hash(pwd)

def verify_password(pwd: str, pwd_hash: str) -> bool:
    return check_password_hash(pwd_hash, pwd)

# Tokens signés
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

# Email
def send_email(subject: str, recipients: list[str], body: str, html: str | None = None):
    msg = Message(subject=subject, recipients=recipients, body=body, html=html)
    mail.send(msg)

# OTP
def create_and_send_otp(user: User, purpose: str = "login") -> None:
    code = f"{secrets.randbelow(10**6):06d}"   # 6 chiffres
    code_hash = hash_password(code)
    otp = OTPCode(user_id=user.id, purpose=purpose, code_hash=code_hash,
                  expires_at=datetime.utcnow() + timedelta(minutes=10))
    db.session.add(otp)
    db.session.commit()
    send_email("[TodoAPI] Votre code OTP", [user.email], f"Votre code OTP est : {code} (valide 10 minutes).")

def verify_otp(user: User, code: str, purpose: str = "login") -> bool:
    otp = (OTPCode.query
           .filter_by(user_id=user.id, purpose=purpose, consumed_at=None)
           .order_by(OTPCode.created_at.desc())
           .first())
    if not otp or otp.expires_at < datetime.utcnow():
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