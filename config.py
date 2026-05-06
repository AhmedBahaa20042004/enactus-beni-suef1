from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/enactus_db"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FIRST_ADMIN_EMAIL: str = "admin@enactus-bsu.com"
    FIRST_ADMIN_PASSWORD: str = "Admin@1234"
    FIRST_ADMIN_NAME: str = "Admin"

    # SendGrid
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@enactus-bsu.com"
    SENDGRID_FROM_NAME: str = "Enactus New Beni Suef"
    ADMIN_NOTIFY_EMAIL: str = "admin@enactus-bsu.com"  # where order alerts go

    # SendGrid
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@enactus-bsu.com"
    SENDGRID_FROM_NAME: str = "Enactus New Beni Suef"
    ADMIN_NOTIFY_EMAIL: str = "admin@enactus-bsu.com"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
