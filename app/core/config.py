from pydantic_settings import BaseSettings

class EmailSettings(BaseSettings):
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "arabyanerik12@gmail.com"
    SMTP_PASSWORD: str = "ksqx mnpl wkwe konk"
    START_TLS: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"


settings = EmailSettings()