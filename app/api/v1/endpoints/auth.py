from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import *
from app.services.auth import *
from app.db.session import get_db


router = APIRouter()


@router.post("/register/", response_model=Register, description="Login", status_code=201)
async def create_user_endpoint(request: Register, db: AsyncSession = Depends(get_db)):
    try:
        db_user = await register(db, request)
        return db_user
    except Exception as e:
        if "unique constraint" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User with this Email already exists")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@router.post("/login/")
async def login_endpoint(request: Login, db: AsyncSession = Depends(get_db)):
    db_user = await login(db, request)
    token = await get_or_create_token(db, db_user)
    return {"data": token.token}


@router.post("/verify_email/", status_code=202)
async def verify_email(request: EmailVerify, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, email=request.email)
    if check_code(request, db, user):
        return "Your email has been verified successfully!"
    else:
        if user.trycount == 4:
            await db.delete(user)
            await db.commit()
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="You have reached the attempt limit")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid verification code")


@router.post("/password-reset/")
async def password_reset(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    recover_url = await create_recover_url(user)

    subject = "Password reset on Netflix"
    message = f"Для сброса пароля перейдите по ссылке: {recover_url} Сбросить пароль"

    await send_email(request.email, subject, message)

    return {"message": "Password reset email sent"}


@router.post("/password-reset-confirm/{uidb64}/{token}/")
async def password_reset_confirm(uidb64: str, token: str, request: Password_validator, db: AsyncSession = Depends(get_db)):
    user = await validate_password_reset_token(uidb64, token, db)

    if not user:
        raise HTTPException(
            status_code=401, detail="Invalid token or user not found")

    hashed_password = await Hash.hash(request.password)
    user.password = hashed_password
    await db.commit()

    auth_token = await get_or_create_token(db, user)

    return {"message": "Password reset successful", "token": auth_token}


@router.post("/password-reset-confirm/{uidb64}/{token}/")
async def password_reset_confirm(uidb64: str, token: str, request: Password_validator, db: AsyncSession = Depends(get_db)):
    user = await validate_password_reset_token(uidb64, token, db)

    if not user:
        raise HTTPException(
            status_code=401, detail="Invalid token or user not found")

    hashed_password = await Hash.hash(request.password)
    user.password = hashed_password
    await db.commit()

    auth_token = await get_or_create_token(db, user)

    return {"message": "Password reset successful", "token": auth_token}

    # path("logout/", logout, name="logout"),
    # path('getuser/', get_user, name="get_user"),
    # path('gtoken_actions/', GoogleLoginApi.as_view(), name="token_actions")
