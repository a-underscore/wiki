from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .get_navbar_items import get_navbar_items
from .models import Message, User, db
from .page import app


@app.route("/apply-for-administrator/", methods=["GET", "POST"])
@login_required
def apply_for_administrator():
    if current_user.score < app.config.get("SCORE_NEEDED").get("REQUEST_ADMINISTRATOR"):
        flash("You aren't at a high enough score to apply for administrator.")

        return redirect(url_for("home"))

    if request.method == "POST":
        if current_user.request_pending:
            flash("You already have a request pending.")
        else:
            content = url_for
            message = Message(
                Message.query.count(),
                current_user.id,
                app.config.get("REQUEST_TYPES").get("ADMINISTRATOR_APPLICATION"),
                f"{current_user.username}:{current_user.id} is requesting admin.",
                f"No content.",
            )
            db.session.add(message)
            current_user.request_pending = True
            db.session.commit()

            flash("Application has been sent.")

            return redirect(url_for("home"))

    return render_template(
        "apply-for-administrator.html", navbar_items=get_navbar_items()
    )


@app.route("/message/<message_id>/", methods=["GET", "POST"])
@login_required
def message(message_id: str):
    if current_user.administrator:
        if message_id.isdigit():
            message_id = int(message_id)
        else:
            flash("Message id is not a number.")

            return redirect(url_for("home"))

        query = Message.query.filter_by(id=message_id)
        message = query.first()

        if request.method == "POST":
            user = User.query.filter_by(id=message.user_id).first()

            if user is None:
                flash("User does not exist.")
            else:
                query.delete()
                user.request_pending = False

                if message.request_type == 0:
                    user.administrator = True

                messages = Message.query.filter(Message.id > message.id)

                for m in messages:
                    m.id -= 1

                db.session.commit()

            return redirect(url_for("administrator_dashboard", page_id="0"))

        return render_template(
            "message.html", navbar_items=get_navbar_items(), message=message
        )

    flash("You are not an administrator.")

    return redirect(url_for("home"))


@app.route("/administrator-dashboard/<page_id>/", methods=["GET", "POST"])
@login_required
def administrator_dashboard(page_id: str):
    if page_id.isdigit():
        page_id = int(page_id)
    else:
        flash("Page id is not a number.")

        return redirect(url_for("home"))

    if current_user.administrator:
        items_per_page = app.config.get("ITEMS_PER_PAGE")

        query = Message.query.order_by(Message.id.desc()).limit(items_per_page)

        messages = query.offset(items_per_page * page_id).all()

        not_first_page = page_id > 0
        not_last_page = query.offset(items_per_page * page_id + 1).all()

        return render_template(
            "administrator-dashboard.html",
            navbar_items=get_navbar_items(),
            messages=messages,
            not_first_page=not_first_page,
            not_last_page=not_last_page,
            page_id=page_id,
        )

    flash("You are not an administrator.")

    return redirect(url_for("home"))


@app.route("/delete-user/<user_id>/")
@login_required
def delete_user(user_id: str):
    if user_id.isdigit():
        user_id = int(user_id)
    else:
        flash("User id is not a number.")

        return redirect(url_for("home"))

    if current_user.administrator:
        user = User.query.filter_by(id=user_id).first()

        if user is None:
            flash("User does not exist.")

            return redirect(url_for("home"))

        return render_template(
            "delete-user.html", navbar_items=get_navbar_items(), user=user
        )

    flash("You are not an administrator.")

    return redirect(url_for("home"))
