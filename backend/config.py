import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://crawler_user:strong_password@localhost:5432/web_crawler"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
