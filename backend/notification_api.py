
import os
import smtplib
from email.message import EmailMessage
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


class NotificationRequest(BaseModel):
    channel: Literal["email", "whatsapp"]
    title: str = Field(default="GridGuard Alert", max_length=160)
    message: str = Field(min_length=1, max_length=4000)


def send_email(title: str, message: str):
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_APP_PASSWORD")
    recipient = os.getenv("ALERT_EMAIL_TO")

    if not all([username, password, recipient]):
        raise RuntimeError(
            "Configure SMTP_USERNAME, SMTP_APP_PASSWORD, "
            "and ALERT_EMAIL_TO in .env"
        )

    email = EmailMessage()
    email["Subject"] = title
    email["From"] = username
    email["To"] = recipient
    email.set_content(message)

    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))

    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(email)


def send_whatsapp(message: str):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    sender = os.getenv("TWILIO_WHATSAPP_FROM")
    recipient = os.getenv("ALERT_WHATSAPP_TO")

    if not all([sid, token, sender, recipient]):
        raise RuntimeError(
            "Configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
            "TWILIO_WHATSAPP_FROM, and ALERT_WHATSAPP_TO in .env"
        )

    try:
        from twilio.rest import Client
    except ImportError as exc:
        raise RuntimeError(
            "Twilio is not installed. Run: pip install twilio"
        ) from exc

    client = Client(sid, token)
    client.messages.create(
        body=message,
        from_=sender,
        to=recipient,
    )


@router.post("/send")
def send_notification(payload: NotificationRequest):
    try:
        if payload.channel == "email":
            send_email(payload.title, payload.message)
        else:
            send_whatsapp(
                f"{payload.title}\n\n{payload.message}"
            )

        return {
            "success": True,
            "channel": payload.channel,
            "message": "Notification submitted successfully.",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
