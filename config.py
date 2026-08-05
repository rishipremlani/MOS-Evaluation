import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:

    SECRET_KEY = "Change_This_To_A_Random_String"

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        "sqlite:///" + os.path.join(BASE_DIR, "database", "mos.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False