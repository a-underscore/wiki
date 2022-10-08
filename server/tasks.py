from .send_confirmation_email import send_confirmation_email
from .worker import worker


@worker.task
def send_confirmation_email_task(email: str, token: str):
    send_confirmation_email(email, token)
