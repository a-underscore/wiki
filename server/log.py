from flask import flash, redirect, render_template, url_for
from flask_login import login_required

from .administrator import app
from .get_navbar_items import get_navbar_items
from .models import Log


@app.route("/logs/<page_id>/", methods=["GET", "POST"])
@login_required
def logs(page_id: str):
    if page_id.isdigit():
        page_id = int(page_id)
    else:
        flash("Page id is not a number.")

        return redirect(url_for("home"))

    items_per_page = app.config.get("ITEMS_PER_PAGE")

    query = Log.query.order_by(Log.id.desc()).limit(items_per_page)

    logs = query.offset(items_per_page * page_id).all()

    not_first_page = page_id > 0
    not_last_page = query.offset(items_per_page * page_id + 1).all()

    return render_template(
        "logs.html",
        navbar_items=get_navbar_items(),
        logs=logs,
        not_first_page=not_first_page,
        not_last_page=not_last_page,
        page_id=page_id,
    )


@app.route("/log/<log_id>/")
@login_required
def log(log_id: str):
    if log_id.isdigit():
        log_id = int(log_id)
    else:
        flash("Page id is not a number.")

        return redirect(url_for("home"))

    log = Log.query.filter_by(id=log_id).first()

    if log is None:
        flash("Log does not exist.")

        return redirect(url_for("home"))

    return render_template("log.html", navbar_items=get_navbar_items(), log=log)
