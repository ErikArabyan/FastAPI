# from models import Token, User
import secrets
from fastapi import HTTPException, status
from random import randint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# from models import *
from app.models.auth import *
from app.schemas.auth import *
from app.services.utils import *


async def register(db: AsyncSession, user: Register):
    code = randint(1000, 9999)
    db_user = await add_user(db, user, code)
    subject = "Email Verification on Netflix"
    body = f"This is your verification code: {code}"
    await send_email(user.email, subject, body)
    return db_user


async def login(db: AsyncSession, user: Login):
    db_user = await get_user(db, email=user.email)

    if db_user:
        if db_user.is_active:
            if await Hash.check(user.password, db_user.password):
                return db_user
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Wrong password')
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='User is deactive')
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't found")


async def get_user(db: AsyncSession, *args, id: int = False, email: str = False):
    if id:
        result = await db.execute(select(User).filter((User.id == id)))
    elif email:
        result = await db.execute(select(User).filter((User.email == email)))

    db_user = result.scalars().first()
    if db_user:
        return db_user
    else:
        raise HTTPException(
            status_code=status.HTTP_417_EXPECTATION_FAILED, detail='User Not Found')


async def add_user(db, user, code=None):
    hashed_password = await Hash.hash(user.password)
    db_user = User(email=user.email, first_name=user.first_name,
                   last_name=user.last_name, password=hashed_password, verification_code=code)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)


async def check_code(request, db, user):
    if user.verification_code == request.code:
        user.verification_code = None
        user.trycount = 0
        user.is_active = True
        await db.commit()
        return True
    else:
        user.trycount += 1
        await db.commit()
        return False


async def get_or_create_token(db: AsyncSession, user: User):
    query = select(Token).filter(Token.user_id == user.id)
    result = await db.execute(query)
    token = result.scalars().first()
    if not token:
        new_token = secrets.token_hex(16)
        await save_token(new_token, db, user)
        return new_token
    else: 
        return token


async def get_user_by_token(db: AsyncSession, token: str):
    query = select(Token).filter(Token.token == token)
    result = await db.execute(query)
    token = result.scalars().first()
    if token:
        return token.user
    return None


async def save_token(new_token, db, user):
        token_obj = Token(token=new_token, user_id=user.id)
        db.add(token_obj)
        await db.commit()
        await db.refresh(token_obj)


async def create_recover_url(user):
    uidb64 = await Hash.encrypt(user.id)
    token = await Hash.encrypt(await Hash.hash(user.email))
    site_url = "http://127.0.0.1:8000"
    return f"{site_url}/auth/password-reset-confirm/{uidb64}/{token}/"


async def validate_password_reset_token(uidb64: str, token: str, db: AsyncSession):
    user_id = await Hash.decrypt(uidb64)
    user = await get_user(db, id=int(user_id))
    print(user.id)
    email = await Hash.decrypt(token)
    print(2)
    if await Hash.check(email, user.email):
        print(3)
        return user
    print(4)
    return False