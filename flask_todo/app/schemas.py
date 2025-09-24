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