from datetime import datetime, timezone
from os import path
from uuid import uuid4

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from .app import app
from .calculate_score import calculate_score
from .get_navbar_items import get_navbar_items
from .log_edit import log_edit
from .models import Page, db
from .profile import app


def upload_fail(message: str):
    return {"uploaded": False, "reason": message}


def upload_success(location: str):
    return {"uploaded": True, "url": path.join(url_for("home"), location)}


def upload_file():
    f = request.files.get("upload")

    split = f.filename.split(".")

    if len(split) != 2:
        return upload_fail("The file name is not formatted properly.")

    extension = split[1].lower()

    if extension not in ["jpg", "gif", "png", "jpeg"]:
        return upload_fail("The file extension is not supported.")

    unique_filename = str(uuid4())

    f.filename = unique_filename + "." + extension
    location = path.join("static", f.filename)

    f.save(location)

    session["LAST_UPLOAD_TIME"] = datetime.now()

    return upload_success(location)


@app.route("/upload/", methods=["POST"])
def upload():
    current_upload_time = datetime.now()
    last_upload_time = session.get("LAST_UPLOAD_TIME")

    if last_upload_time is None:
        return upload_file()
    elif (
        current_upload_time.replace(tzinfo=timezone.utc) - last_upload_time
    ).total_seconds() >= app.config.get("TIME_BETWEEN_UPLOADS"):
        return upload_file()
    else:
        return upload_fail("You are uploading too quickly.")


@app.route("/page/<page_id>/")
def page(page_id: str):
    if page_id.isdigit():
        page_id = int(page_id)
    else:
        flash("Page id is not a number.")

        return redirect(url_for("home"))

    page = Page.query.filter_by(id=page_id).first()

    if page is None:
        flash("Page does not exist.")

        return redirect(url_for("home"))

    return render_template(
        "page.html",
        navbar_items=get_navbar_items(),
        page=page,
    )


@app.route("/create-page/", methods=["GET", "POST"])
@login_required
def create_page():
    if current_user.verified:
        if current_user.score < app.config.get("SCORE_NEEDED").get("CREATE"):
            flash("You aren't at a high enough score to create a page.")

            return redirect(url_for("home"))

        if request.method == "POST":
            title: str or None = request.form.get("title")

            if len(title) > app.config.get("LIMITS").get("TITLE"):
                flash("Title is too long.")

                return render_template(
                    "create-page.html", navbar_items=get_navbar_items()
                )

            if title == "" or title is None:
                flash("Title is blank.")

                return render_template(
                    "create-page.html", navbar_items=get_navbar_items()
                )

            if Page.query.filter_by(title=title).count() > 0:
                flash(f"Page with name {title} already exists.")

                return render_template(
                    "create-page.html", navbar_items=get_navbar_items()
                )

            content: str or None = request.form.get("content")

            if len(content) > app.config.get("LIMITS").get("CONTENT"):
                flash("Content is too long")

                return render_template(
                    "create-page.html", navbar_items=get_navbar_items()
                )

            if content == "" or content is None:
                flash("Content is blank.")

                return render_template(
                    "create-page.html", navbar_items=get_navbar_items()
                )

            content = content.replace("<script>", "").replace("</script>", "")

            score_needed: str or None = request.form.get("score_needed")

            if score_needed == "" or score_needed is None:
                flash("Score needed left blank.")

                return render_template(
                    "create-page.html", navbar_items=get_navbar_items()
                )

            if score_needed.isdigit():
                if len(score_needed) > app.config.get("LIMITS").get("SCORE_NEEDED"):
                    flash("Score needed is too long.")

                    return render_template(
                        "create-page.html", navbar_items=get_navbar_items()
                    )

                score_needed = int(score_needed)

                if current_user.score < score_needed:
                    flash(
                        "That score is too large. Use a score less than or equal to yours."
                    )

                    return render_template(
                        "create-page.html", navbar_items=get_navbar_items()
                    )

                current_user.score += len(content)

                page = Page(
                    Page.query.count(),
                    title,
                    content,
                    score_needed,
                )
                db.session.add(page)
                db.session.commit()

                return redirect(url_for("page", page_id=page.id))

            flash("Score needed is not a number.")

        return render_template("create-page.html", navbar_items=get_navbar_items())

    flash("You need to verify your account first.")

    return redirect(url_for("home"))


@app.route("/edit-page/<page_id>/", methods=["GET", "POST"])
@login_required
def edit_page(page_id: str):
    if current_user.verified:
        if page_id.isdigit():
            page_id = int(page_id)
        else:
            flash("Page id is not a number.")

            return redirect(url_for("home"))

        page = Page.query.filter_by(id=page_id).first()

        if page is None:
            flash("Page does not exist.")

            return redirect(url_for("home"))

        if current_user.score >= page.score_needed or current_user.administrator:
            if request.method == "POST":
                score_needed: str or None = request.form.get("score_needed")

                old_page = page

                if score_needed != page.score_needed:
                    if score_needed != "" and score_needed is not None:
                        if score_needed.isdigit():
                            if len(score_needed) > app.config.get("LIMITS").get(
                                "SCORE_NEEDED"
                            ):
                                flash("Score needed is too long.")

                                return render_template(
                                    "edit-page.html",
                                    navbar_items=get_navbar_items(),
                                    page=page,
                                )

                            score_needed = int(score_needed)

                            if score_needed <= current_user.score:
                                page.score_needed = score_needed
                            else:
                                flash(
                                    "You aren't at a high enough score to change this page's score."
                                )

                                return render_template(
                                    "edit-page.html",
                                    navbar_items=get_navbar_items(),
                                    page=page,
                                )
                        else:
                            flash("Score needed is not a number.")

                            return render_template(
                                "edit-page.html",
                                navbar_items=get_navbar_items(),
                                page=page,
                            )
                else:
                    flash("Score needed is the same.")

                    return render_template(
                        "edit-page.html", navbar_items=get_navbar_items(), page=page
                    )

                content: str or None = request.form.get("content")

                if content != page.content:
                    if content != "" and content is not None:
                        if len(content) > app.config.get("LIMITS").get("CONTENT"):
                            flash("Content is too long")

                            return render_template(
                                "edit-page.html",
                                navbar_items=get_navbar_items(),
                                page=page,
                            )

                        content = content.replace("<script>", "").replace(
                            "</script>", ""
                        )

                        calculate_score(page.content, content)

                        page.content = content

                        log_edit(old_page, page)

                        db.session.commit()
                else:
                    flash("Inputs are the same.")

                return redirect(url_for("page", page_id=page_id))

            return render_template(
                "edit-page.html", navbar_items=get_navbar_items(), page=page
            )

        flash("You aren't at high enough score to edit that page.")

        return redirect(url_for("page", page_id=page_id))

    flash("You need to verify your account first.")

    return redirect(url_for("home"))


@app.route("/delete-page/<page_id>/", methods=["GET", "POST"])
@login_required
def delete_page(page_id: str):
    if page_id.isdigit():
        page_id = int(page_id)
    else:
        flash("Page id is not a number.")

        return redirect(url_for("home"))

    query = Page.query.filter_by(id=page_id)
    page = query.first()

    if page is None:
        flash("Page does not exist.")

        return redirect(url_for("home"))

    if current_user.score >= page.score_needed or current_user.administrator:
        if request.method == "POST":
            title: str or None = request.form.get("title")

            if title is None:
                flash("Title left blank.")

                return render_template(
                    "delete-page.html", navbar_items=get_navbar_items(), page=page
                )

            if title > app.config.get("LIMITS").get("TITLE"):
                flash("Title is too long.")

                return render_template(
                    "delete-page.html", navbar_items=get_navbar_items(), page=page
                )

            if page.title == title:
                query.delete()
                pages = Page.query.filter(Page.id > page.id).all()

                for p in pages:
                    p.id -= 1

                db.session.commit()

                flash("Page has been deleted")

                return redirect(url_for("home"))

            flash("Titles do not match.")

        return render_template(
            "delete-page.html", navbar_items=get_navbar_items(), page=page
        )

    flash("Your score is not high enough to delete that page.")

    return redirect(url_for("home"))
