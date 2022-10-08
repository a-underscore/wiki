from flask_login import LoginManager, UserMixin

from .app import app
from .db import db

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    email = db.Column("email", db.Text, unique=True)
    username = db.Column("username", db.Text, nullable=False)
    password = db.Column("password", db.Text, nullable=False)
    verified = db.Column("verified", db.Boolean, nullable=False)
    administrator = db.Column("administrator", db.Boolean, nullable=False)
    token = db.Column("token", db.Text, nullable=False)
    score = db.Column("score", db.Integer, nullable=False)
    request_pending = db.Column("request_pending", db.Boolean, nullable=False)

    def __init__(
        self,
        id: int,
        email: str,
        username: str,
        password: str,
        token: str,
    ):
        self.id = id
        self.email = email
        self.username = username
        self.password = password
        self.verified = False
        self.administrator = False
        self.token = token
        self.score = 0
        self.request_pending = False


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Page(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column("title", db.String(), unique=True, nullable=False)
    content = db.Column("content", db.Text, nullable=False)
    score_needed = db.Column("points_needed", db.Integer, nullable=False)

    def __init__(self, id: int, title: str, content: str, score_needed: int):
        self.id = id
        self.title = title
        self.content = content
        self.score_needed = score_needed


class Message(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    user_id = db.Column("user_id", db.Integer, nullable=False)
    request_type = db.Column("request_type", db.Integer, nullable=False)
    title = db.Column("title", db.Integer, nullable=False)
    content = db.Column("content", db.Integer, nullable=False)

    def __init__(
        self, id: int, user_id: int, request_type: int, title: str, content: str
    ):
        self.id = id
        self.user_id = user_id
        self.request_type = request_type
        self.title = title
        self.content = content


class Log(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    user_id = db.Column("user_id", db.Integer, nullable=False)
    page_id = db.Column("post_id", db.Integer, nullable=False)
    old_content = db.Column("old_content", db.Text, nullable=False)
    old_score_needed = db.Column("old_score_needed", db.Text, nullable=False)
    new_content = db.Column("new_content", db.Text, nullable=False)
    new_score_needed = db.Column("new_score_needed", db.Text, nullable=False)

    def __init__(
        self,
        id: int,
        user_id: int,
        page_id: int,
        old_content: str,
        old_score_needed: int,
        new_content: str,
        new_score_needed: int,
    ):
        self.id = id
        self.user_id = user_id
        self.page_id = page_id
        self.old_content = old_content
        self.old_score_needed = old_score_needed
        self.new_content = new_content
        self.new_score_needed = new_score_needed
