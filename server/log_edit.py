from flask_login import current_user

from .models import Log, Page, db


def log_edit(old_page: Page, new_page: Page):
    log = Log(
        Log.query.count(),
        current_user.id,
        new_page.id,
        old_page.content,
        old_page.score_needed,
        new_page.content,
        new_page.score_needed,
    )
    db.session.add(log)
    db.session.commit()
