import json
from urllib.request import Request, urlopen

from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend


class ResendBackend(BaseEmailBackend):
    """Deliver Homeward's plain-text password-reset messages over HTTPS."""

    def __init__(self, *, api_key, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key

    def send_messages(self, messages):
        if not self.api_key:
            raise ImproperlyConfigured("Set RESEND_API_KEY before sending email.")
        sent = 0
        for message in messages:
            if not message.to:
                continue
            request = Request(
                "https://api.resend.com/emails",
                data=json.dumps({
                    "from": message.from_email,
                    "to": message.to,
                    "subject": message.subject,
                    "text": message.body,
                }).encode(),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Homeward/1.0",
                },
                method="POST",
            )
            with urlopen(request, timeout=10):
                sent += 1
        return sent
