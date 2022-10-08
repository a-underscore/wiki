from flask_login import current_user

from .app import app


def get_navbar_items() -> dict[str, str]:
    if current_user.is_authenticated:
        items = {
            "search": "search",
            "logout": "logout",
            "my profile": "my-profile/0/",
            "logs": "logs/0/",
        }

        if current_user.score >= app.config.get("SCORE_NEEDED").get("CREATE"):
            items["create page"] = "create-page"

        if current_user.administrator:
            items["administrator dashboard"] = "administrator-dashboard/0/"
        elif current_user.score >= app.config.get("SCORE_NEEDED").get(
            "REQUEST_ADMINISTRATOR"
        ):
            items["apply for administrator"] = "apply-for-administrator"

        if not current_user.verified:
            items["verify account"] = "verify-account"

        return items

    return {"create account": "create-account", "login": "login", "logs": "logs/0/"}
