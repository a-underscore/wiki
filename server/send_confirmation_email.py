from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

from .app import app


def send_confirmation_email(email: str, token: str):
    server_transport_protocol = app.config.get("SERVER_TRANSFER_PROTOCOL")
    server_address = app.config.get("SERVER_ADDRESS")
    server_port = app.config.get("SERVER_PORT")

    content_plain = f"{server_transport_protocol}://{server_address}:{server_port}/confirm-email/{token}/"
    content_html = f"<p>{server_transport_protocol}://{server_address}:{server_port}/confirm-email/{token}/</p>"

    server = SMTP_SSL("smtp.gmail.com")
    server.login(app.config.get("EMAIL_ADDRESS"), app.config.get("EMAIL_PASSWORD"))

    content = MIMEMultipart("alternative")

    content["From"] = app.config.get("EMAIL_ADDRESS")
    content["To"] = email
    content[
        "Subject"
    ] = f'{app.config.get("PROJECT_NAME")}: Confirm your email address.'

    content.attach(MIMEText(content_plain, "plain"))
    content.attach(MIMEText(content_html, "html"))

    server.sendmail(app.config.get("EMAIL_ADDRESS"), email, content.as_string())

    server.quit()
