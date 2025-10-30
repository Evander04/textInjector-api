import os
from app.config.base import BaseConfig

class ProdConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("PROD_DATABASE_URL") or os.getenv("DATABASE_URL")
