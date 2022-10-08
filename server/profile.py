from secrets import token_urlsafe

from bcrypt import checkpw, gensalt, hashpw
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .app import app
from .get_navbar_items import get_navbar_items
from .models import Log, Page, User, db
from .send_confirmation_email import send_confirmation_email
from .tasks import send_confirmation_email_task
from .verify_request import (
    verify_email_quiet,
    verify_password_quiet,
    verify_request,
    verify_username_quiet,
)


@app.route("/")
def home():
    return render_template("home.html", navbar_items=get_navbar_items())


@app.route("/search/", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search: str or None = request.form.get("search")

        if len(search) > app.config.get("LIMITS").get("TITLE"):
            flash("Search is too long.")

            return render_template("search.html", navbar_items=get_navbar_items())

        if search == "" or search is None:
            flash("Search left blank.")

            return render_template("search.html", navbar_items=get_navbar_items())

        return redirect(url_for("search_result", search=search, page_id="0"))

    return render_template("search.html", navbar_items=get_navbar_items())


@app.route("/search-result/<search>/<page_id>/", methods=["GET", "POST"])
def search_result(search: str, page_id: str):
    if page_id.isdigit():
        page_id = int(page_id)
    else:
        flash("Page id is not a number.")

        return redirect(url_for("home"))

    if len(search) > app.config.get("LIMITS").get("TITLE"):
        flash("Search is too long.")

        return render_template(
            "search-result.html",
            navbar_items=get_navbar_items(),
            search=search,
            pages=pages,
            not_first_page=not_first_page,
            not_last_page=not_last_page,
            page_id=page_id,
        )

    items_per_page = app.config.get("ITEMS_PER_PAGE")

    title_ilike = Page.title.ilike(f"{search}")

    query = Page.query.filter(title_ilike).limit(items_per_page)

    pages = query.offset(items_per_page * page_id).all()

    not_first_page = page_id > 0
    not_last_page = (query.offset(items_per_page * page_id + 1).count()) > 0

    return render_template(
        "search-result.html",
        navbar_items=get_navbar_items(),
        search=search,
        pages=pages,
        not_first_page=not_first_page,
        not_last_page=not_last_page,
        page_id=page_id,
    )


@app.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in.")

        return redirect(url_for("home"))

    if request.method == "POST":
        email: str or None = request.form.get("email")

        if len(email) > app.config.get("LIMITS").get("PASSWORD"):
            flash("Email is too long.")

            return render_template("login.html", navbar_items=get_navbar_items())

        if email == "" or email is None:
            flash("Email left blank.")

            return render_template("login.html", navbar_items=get_navbar_items())

        password: str or None = request.form.get("password")

        if len(password) > app.config.get("LIMITS").get("PASSWORD"):
            flash("Password is too long.")

            return render_template("login.html", navbar_items=get_navbar_items())

        if password == "" or password is None:
            flash("Password left blank.")

            return render_template("login.html", navbar_items=get_navbar_items())

        user = User.query.filter_by(email=email).first()

        if user is None:
            flash(f"User not found with email {email}.")

            return render_template("login.html", navbar_items=get_navbar_items())

        if checkpw(bytes(password, "utf-8"), bytes(user.password, "utf-8")):
            login_user(user)

            return redirect(url_for("home"))

        flash("Password incorrect")

    return render_template("login.html", navbar_items=get_navbar_items())


@app.route("/create-account/", methods=["GET", "POST"])
def create_account():
    if current_user.is_authenticated:
        flash("You are already logged in.")

        return redirect(url_for("home"))

    if request.method == "POST":
        return verify_request(request)

    return render_template("create-account.html", navbar_items=get_navbar_items())


@app.route("/logout/")
@login_required
def logout():
    logout_user()

    flash("You have been logged out.")

    return redirect(url_for("home"))


@app.route("/confirm-email/<token>/")
@login_required
def confirm_email(token: str):
    if current_user.verified:
        flash("User already verified.")

        return redirect(url_for("home"))

    if current_user.token == token:
        current_user.verified = True
        db.session.commit()

        flash("Your email has been confirmed.")

        return redirect(url_for("home"))

    flash("Tokens do not match.")

    return redirect(url_for("home"))


@app.route("/profile/<user_id>/<page_id>/")
def profile(user_id: str, page_id: str):
    if user_id.isdigit():
        user_id = int(user_id)
    else:
        flash("User id is not a number.")

        return redirect(url_for("home"))

    if page_id.isdigit():
        page_id = int(page_id)
    else:
        flash("Page id is not a number.")

        return redirect(url_for("home"))

    user = User.query.filter_by(id=user_id).first()

    if user is None:
        flash("User does not exist.")

        return redirect(url_for("home"))

    items_per_page = app.config.get("ITEMS_PER_PAGE")

    query = (
        Log.query.filter_by(user_id=user_id)
        .order_by(Log.id.desc())
        .limit(items_per_page)
    )

    logs = query.offset(items_per_page * page_id).all()

    not_first_page = page_id > 0
    not_last_page = (query.offset(items_per_page * page_id + 1).count()) > 0

    return render_template(
        "profile.html",
        navbar_items=get_navbar_items(),
        user=user,
        logs=logs,
        not_first_page=not_first_page,
        not_last_page=not_last_page,
        page_id=page_id,
    )


@app.route("/my-profile/<page_id>/", methods=["GET", "POST"])
@login_required
def my_profile(page_id: str):
    if page_id.isdigit():
        page_id = int(page_id)
    else:
        flash("Page id is not a number.")

        return redirect(url_for("home"))

    items_per_page = app.config.get("ITEMS_PER_PAGE")

    query = (
        Log.query.filter_by(user_id=current_user.id)
        .order_by(Log.id.desc())
        .limit(items_per_page)
    )

    logs = query.offset(items_per_page * page_id).all()

    not_first_page = page_id > 0
    not_last_page = (query.offset(items_per_page * page_id + 1).count()) > 0

    return render_template(
        "my-profile.html",
        navbar_items=get_navbar_items(),
        user=current_user,
        logs=logs,
        page_id=page_id,
        not_first_page=not_first_page,
        not_last_page=not_last_page,
    )


@app.route("/edit-my-profile/", methods=["GET", "POST"])
@login_required
def edit_my_profile():
    if request.method == "POST":
        current_password: str or None = request.form.get("current_password")

        if len(current_password) > app.config.get("LIMITS").get("PASSWORD"):
            flash("Current password is too long.")

            return render_template(
                "edit-my-profile.html",
                navbar_items=get_navbar_items(),
                user=current_user,
            )

        if current_password == "" or current_password is None:
            flash("Current password blank.")

            return render_template(
                "edit-my-profile.html",
                navbar_items=get_navbar_items(),
                user=current_user,
            )

        if checkpw(
            bytes(current_password, "utf-8"), bytes(current_user.password, "utf-8")
        ):
            email: str or None = request.form.get("email")

            if email != "" and email is not None:
                if verify_email_quiet(email):
                    current_user.email = email
                else:
                    return render_template(
                        "edit-my-profile.html",
                        navbar_items=get_navbar_items(),
                        user=current_user,
                    )

            username: str or None = request.form.get("username")

            if email != "" and email is not None:
                if verify_username_quiet(username):
                    current_user.email = email
                    current_user.token = token_urlsafe(
                        app.config.get("TOKEN_NUM_BYTES")
                    )
                    current_user.verified = False

                    send_confirmation_email_task.delay(
                        current_user.email, current_user.token
                    )

                    flash("Confirmation email is being sent.")
                else:
                    return render_template(
                        "edit-my-profile.html",
                        navbar_items=get_navbar_items(),
                        user=current_user,
                    )

            password: str or None = request.form.get("password")

            if password != "" and password is not None:
                confirm_password: str or None = request.form.get("confirm_password")

                if verify_password_quiet(password, confirm_password):
                    current_user.password = hashpw(
                        bytes(password, "utf-8"), gensalt()
                    ).decode("utf-8")
                else:
                    return render_template(
                        "edit-my-profile.html",
                        navbar_items=get_navbar_items(),
                        user=current_user,
                    )

            db.session.commit()

            return redirect(url_for("my_profile"))

        flash("Current password does not match.")

    return render_template(
        "edit-my-profile.html", navbar_items=get_navbar_items(), user=current_user
    )


@app.route("/verify-account/")
@login_required
def verify_account():
    if current_user.verified:
        flash("You are already verified")

        return redirect(url_for("home"))

    current_user.token = token_urlsafe(app.config.get("TOKEN_NUM_BYTES"))
    db.session.commit()

    send_confirmation_email(current_user.email, current_user.token)

    flash("Confirmation is being email sent.")

    return redirect(url_for("home"))


@app.route("/delete-account/", methods=["GET", "POST"])
@login_required
def delete_account():
    if request.method == "POST":
        password: str or None = request.form.get("password")

        if checkpw(bytes(password, "utf-8"), bytes(current_user.password, "utf-8")):
            User.query.filter_by(id=current_user.id).delete()

            for u in User.qeury.filter(User.id > current_user.id):
                u.id -= 1

            logout_user()

            db.session.commit()

            flash("Your account has been deleted.")

            return redirect(url_for("home"))

        flash("Incorrect password.")

    return render_template("delete-account.html", navbar_items=get_navbar_items())
