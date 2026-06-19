from typing import Generator
from pymongo import MongoClient
from .config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]


def get_db() -> Generator:
    try:
        yield db
    finally:
        pass
