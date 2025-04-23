import asyncio
import aiosmtplib
from email.message import EmailMessage
from app.core.config import settings
from passlib.context import CryptContext
import base64


async def send_email(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.START_TLS
        )
        return {"message": "Email sent successfully"}
    except Exception as e:
        return {"error": str(e)}


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @classmethod
    async def hash(cls, password: str) -> str:
        return await asyncio.to_thread(cls.pwd_context.hash, password)

    @classmethod
    async def check(cls, user_password: str, db_password: str) -> bool:
        return await asyncio.to_thread(cls.pwd_context.verify, user_password, db_password)

    @classmethod
    async def encrypt(cls, data: str | int) -> str:
        data_bytes = str(data).encode()
        encoded_data = base64.urlsafe_b64encode(data_bytes).decode()
        return encoded_data

    @classmethod
    async def decrypt(cls, encoded_data: str) -> str | int:
        return base64.urlsafe_b64decode(encoded_data).decode()
