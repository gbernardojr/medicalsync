import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


load_dotenv()

try:
    DB_PORT = int(os.getenv("DB_PORT"))  # Converte para inteiro
except (TypeError, ValueError):
    raise ValueError("DB_PORT deve ser um número inteiro no arquivo .env")

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{DB_PORT}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL, connect_args={'sslmode':'disable','client_encoding': 'utf8',
        'options': '-c client_encoding=utf8'}, pool_size=10, max_overflow=20)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()