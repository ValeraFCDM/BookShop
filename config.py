from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL : str
    SECRET_KEY : str

    class Config:
        env_file = '.venv'

settings = Settings()
