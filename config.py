import os

class Config:
    # Provide a default SQLite database URI for local development if DATABASE_URL is not set
    SQLALCHEMY_DATABASE_URI = (
        os.getenv('DATABASE_URL', 'sqlite:///local.db').replace('postgres://', 'postgresql://', 1)
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
