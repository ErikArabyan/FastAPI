import os
import shutil
from fastapi import HTTPException
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext
import base64
import aiosmtplib

import asyncio

from app.core.config import settings, BASE_DIR


async def send_email(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    
    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=settings.START_TLS
    )


async def upload_file(file):
    file_path = os.path.join(BASE_DIR / "media", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"file_path": file_path}


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    serializer = URLSafeTimedSerializer(
        secret_key="954j6g&=p37(40r$)0pt%t2xfh7a)h^0heyj9&_gs6w6brm_hq", salt="email-configuration"
    )

    @classmethod
    async def hash(cls, password: str) -> str:
        return await asyncio.to_thread(cls.pwd_context.hash, password)

    @classmethod
    async def check(cls, user_password: str, db_password: str) -> bool:
        return await asyncio.to_thread(cls.pwd_context.verify, user_password, db_password)

    @classmethod
    async def no_secure_url_safe_encrypt(cls, data: str | int) -> str:
        data_bytes = str(data).encode()
        encoded_data = base64.urlsafe_b64encode(data_bytes).decode()
        return encoded_data

    @classmethod
    async def no_secure_url_safe_decrypt(cls, encoded_data: str) -> str | int:
        return base64.urlsafe_b64decode(encoded_data).decode()

    @classmethod
    async def create_url_safe_token(cls, data: dict):
        token = cls.serializer.dumps(data)
        return token

    @classmethod
    async def decode_url_safe_token(cls, token: str):
        try:
            token_data = cls.serializer.loads(token, max_age=120)
            return token_data
        except:
            return HTTPException(status_code=408, detail="Token lifetime expired")
