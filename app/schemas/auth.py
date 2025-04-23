from pydantic import BaseModel, EmailStr, field_validator


class Password_validator(BaseModel):
    password: str

    @field_validator('password', mode='after')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')

        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v


class Login(Password_validator):
    email: EmailStr


class Register(Login):
    first_name: str
    last_name: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class EmailVerify(PasswordResetRequest):
    code: int


class UserResponse(PasswordResetRequest):
    username: str
    first_name: str
    last_name: str
    image: str


class GetUserResponse(BaseModel):
    user: UserResponse
