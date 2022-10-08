from flask_login import current_user

from .db import db


def calculate_score(before: str, after: str):
    for b, a in zip(before, after):
        if b != a:
            current_user.score += 1

    current_user.score += abs(len(before) - len(after))

    db.session.commit()
