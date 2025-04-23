import httpx
import uuid
from pprint import pprint
from app.db.interfaces import *
from app.models.auth import *
from app.schemas.auth import *
from app.services.utils import *

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse

from random import randint


async def register(db, user):
    user.password = await Hash.hash(user.password)

    code = randint(1000, 9999)
    data = user.model_dump()
    data["verification_code"] = code
    db_user = await DatabaseInterface.create(db, User, data)
    subject = "Email Verification on Netflix"
    body = f"This is your verification code: {code}"
    asyncio.create_task(send_email(user.email, subject, body))
    return db_user


async def login(db: AsyncSession, user: Login):
    db_user = await DatabaseInterface.get(db, User, 'email', user.email)

    if db_user:
        if await Hash.check(user.password, db_user.password):
            if db_user.is_active:
                return db_user
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='User is deactive')

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail='Wrong credentials')


async def get_or_create_token(db: AsyncSession, user: User, request):
    token = await DatabaseInterface.filter(db, Token, 'user_id', user.id)
    user_data = await _get_user_data(request)
    filtered_token = list(filter(lambda x: x.ip_address ==
                          user_data["ip_address"] and x.user_agent == user_data["user_agent"] and x.location == user_data["location"], token))
    if len(filtered_token) != 0:
        return filtered_token[0].token
    else:
        new_token = str(uuid.uuid4())
        data = {"token": new_token, "user_id": user.id}
        data.update(user_data)
        asyncio.create_task(DatabaseInterface.create(db, Token, data))
        return new_token


async def _get_user_data(request):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    parsed_ua = parse(user_agent)
    user_data = await fetch_user_data(f"http://ip-api.com/json/", '24.48.0.1')
    # user_data = await fetch_user_data(f"http://ip-api.com/json/", client_ip)
    return {"ip_address": client_ip, "user_agent": str(parsed_ua), "location": f"{user_data["country"]} {user_data["regionName"]} {user_data["city"]}", "proxy": user_data["proxy"]}


async def check_code(request, db, user):
    if user.verification_code == request.code:
        data = {"verification_code": None,
                "trycount": 0,
                "is_active": True}
        asyncio.create_task(DatabaseInterface.update(db, User, user.id, data))
        return True
    else:
        data = {"trycount": user.trycount + 1}
        asyncio.create_task(DatabaseInterface.update(db, User, user.id, data))
        return False


async def get_user_by_token(db: AsyncSession, token: str):
    token = await DatabaseInterface.get(db, Token, 'token', token)
    if token:
        return token.user
    return None


async def create_recover_url(user):
    uidb64 = await Hash.no_secure_url_safe_encrypt(user.id)
    site_url = "http://127.0.0.1:3000"
    token = await Hash.create_url_safe_token(user.email)
    return f"{site_url}/auth/password-reset-confirm/{uidb64}/{token}/"


async def validate_password_reset_token(uidb64: str, token: str, db: AsyncSession):
    user_id = await Hash.no_secure_url_safe_decrypt(uidb64)
    user = await DatabaseInterface.get(db, User, 'id', int(user_id))
    email = await Hash.decode_url_safe_token(token)
    if email == user.email:
        return user
    return False


async def set_user_password(request, user, db):
    hashed_password = await Hash.hash(request.password)
    user.password = hashed_password
    await db.commit()


async def get_or_create_user(db, payload, request):
    email = payload["email"]
    user_data = {
        'first_name': payload.get('given_name', ''),
        'last_name': payload.get('family_name', ''),
        # 'image': payload.get('picture', ''),
        'email': email,
        'is_active': True
    }
    user = await DatabaseInterface.get_or_create(db, User, "email", email, user_data)
    try:
        asyncio.create_task(DatabaseInterface.create(db, Token, {'user_id': user.id, 'token': payload["sub"]}))
    except:
        pass
    return user


async def fetch_user_data(url, ip):
    data = {"": ip, "fields": "country,regionName,city,proxy"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=data)
            return response.json()
    except Exception as e:
        return "Service is unavailable"


async def fetch_data(url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
    except Exception as e:
        return "Service is unavailable"
