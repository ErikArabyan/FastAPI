import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from jwt import get_unverified_header, decode, get_unverified_header
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


from app.db.session import get_db
from app.services.auth import *
from app.schemas.auth import *


router = APIRouter()


@router.post("/register/", description="Login", status_code=201)
async def create_user_endpoint(request: Register, db=Depends(get_db)):
    try:
        asyncio.create_task(register(db, request))
        return "Check your email."
    except Exception as e:
        if "unique constraint" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail={"User with this Email already exists"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@router.post("/verify-email/", status_code=202)
async def verify_email_endpoint(request: EmailVerify, db: AsyncSession = Depends(get_db)):
    user = await DatabaseInterface.get(db, User, 'email', request.email)
    if user.trycount == 3:
        asyncio.create_task(DatabaseInterface.delete(db, User, "id", user.id))
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="You have reached the attempt limit")
    elif await check_code(request, db, user):
        return "Your email has been verified successfully!"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid verification code")


@router.post("/login/")
async def login_endpoint(data: Login, request: Request, db: AsyncSession = Depends(get_db)):
    db_user = await login(db, data)
    token = await get_or_create_token(db, db_user, request)
    return token


@router.post("/logout/")
async def logout_endpoint(Authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    print(Authorization)
    asyncio.create_task(DatabaseInterface.delete(
        db, Token, "token", Authorization))


@router.post("/password-change/")
async def password_reset_endpoint(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    user = await DatabaseInterface.get(db, User, 'email', request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    recover_url = await create_recover_url(user)

    subject = "Password reset on Netflix"
    message = f"Для сброса пароля перейдите по ссылке: \n{recover_url}\n\n Сбросить пароль"

    asyncio.create_task(send_email(request.email, subject, message))

    return {"message": "Password reset email sent"}


@router.post("/reset/{uidb64}/{token}/")
async def password_reset_confirm_endpoint(uidb64: str, request: Request, token: str, data: Password_validator, db: AsyncSession = Depends(get_db)):
    user = await validate_password_reset_token(uidb64, token, db)

    if not user:
        raise HTTPException(
            status_code=401, detail="Invalid token or user not found")

    asyncio.create_task(set_user_password(data, user, db))
    auth_token = await get_or_create_token(db, user, request)

    return {"message": "Password reset successful", "token": auth_token}


@router.get("/getuser/", response_model=GetUserResponse, status_code=status.HTTP_202_ACCEPTED, description="Get User")
async def get_user(Authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    if not Authorization:
        raise HTTPException(detail='Token not provided', status_code=status.HTTP_400_BAD_REQUEST)
    try:
        user = await DatabaseInterface.get_merged(db, User, Token, 'token', Authorization)
        user.username = user.first_name
        return {"user": user}
    except Exception as e:
        raise HTTPException(
            detail={'error': 'User does not exist'}, status_code=status.HTTP_404_NOT_FOUND)


@router.post("/gtoken-actions/", status_code=status.HTTP_200_OK, description="Google Authorization")
async def decode_and_verify_token(request: Request, credential: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
    try:
        unverified_header = get_unverified_header(credential)
        if not credential:
            raise HTTPException(
                detail={"error": "Token is required"}, status_code=status.HTTP_400_BAD_REQUEST)

        response = await fetch_data("https://www.googleapis.com/oauth2/v3/certs")
        kid = unverified_header.get('kid')
        rsa_key = next(
            (key for key in response['keys'] if key['kid'] == kid), None)

        decoded_token = decode(
            credential,
            key=RSAAlgorithm.from_jwk(rsa_key),
            algorithms=[unverified_header['alg']],
            audience="97173424287-mr88917mp74110bl0so2a4un1gmorq0h.apps.googleusercontent.com",
            issuer="https://accounts.google.com"
        )
        asyncio.create_task(get_or_create_user(db, decoded_token, request))
        return {"decoded_token": decoded_token}
    except ExpiredSignatureError:
        return HTTPException(detail={"error": "Token has expired"}, status_code=401)
    except InvalidTokenError:
        return HTTPException(detail={"error": "Invalid token"}, status_code=400)
