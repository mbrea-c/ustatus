import logging
from gi.repository import Notify
from typing import Optional


def notify_error(summary: Optional[str] = None, body: Optional[str] = None):
    if summary is None:
        summary = "ustatus error"
    if body is None:
        body = "An error has ocurred"

    logging.error(f"{summary}: {body}")

    notification = Notify.Notification.new(summary, body, "dialog-error")
    notification.set_urgency(2)
    notification.show()
