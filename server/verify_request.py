import re
from secrets import token_urlsafe

from bcrypt import gensalt, hashpw
from flask import Request, Response, flash, redirect, render_template, url_for
from flask_login import login_user

from .app import app
from .get_navbar_items import get_navbar_items
from .models import User, db
from .tasks import send_confirmation_email_task

EMAIL_RE = re.compile(
    """(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
)
USERNAME_RE = re.compile("^[a-z0-9_-]{3,15}$")
PASSWORD_RE = re.compile("^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,15}$")


def verify_email_quiet(email: str) -> bool:
    if User.query.filter_by(email=email).count() > 0:
        flash("Email already in use.")

        return False

    if EMAIL_RE.match(email):
        return True

    flash("Email does not pass regex.")

    return False


def verify_email(email: str or None) -> bool:
    if email == "" or email is None:
        flash("Email left blank.")

        return False

    return verify_email_quiet(email)


def verify_username_quiet(username: str) -> bool:
    if USERNAME_RE.match(username):
        return True

    flash("Username does not pass regex.")

    return False


def verify_username(username: str or None) -> bool:
    if username == "" or username is None:
        flash("Username left blank")

        return False

    return verify_username_quiet(username)


def verify_password_quiet(password: str, confirm_password: str) -> bool:
    if password != confirm_password:
        flash("Passwords do not match.")

        return False

    if PASSWORD_RE.match(password):
        return True

    flash("Password does not pass regex.")

    return False


def verify_password(password: str or None, confirm_password: str or None) -> bool:
    if password == "" or password is None:
        flash("Password left blank.")

        return False

    if confirm_password == "" or confirm_password is None:
        flash("Confirm password left blank.")

        return False

    return verify_password_quiet(password, confirm_password)


def verify_request(request: Request) -> Response or str:
    email: str or None = request.form.get("email")

    if verify_email(email):
        username: str or None = request.form.get("username")

        if verify_username(username):
            password: str or None = request.form.get("password")

            if verify_password(password, request.form.get("confirm_password")):
                token = token_urlsafe(app.config.get("TOKEN_NUM_BYTES"))

                user = User(
                    User.query.count(),
                    email,
                    username,
                    hashpw(bytes(password, "utf-8"), gensalt()).decode("utf-8"),
                    token,
                )
                db.session.add(user)
                db.session.commit()

                send_confirmation_email_task.delay(email, token)

                flash("Confirmation email is being sent.")

                login_user(user)

                flash("You are now logged in.")

                return redirect(url_for("home"))

    return render_template("create-account.html", navbar_items=get_navbar_items())
