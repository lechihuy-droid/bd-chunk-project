from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import load_settings

@lru_cache
def get_engine(database_url: str | None = None):
    return create_engine(database_url or load_settings().database_url)


@lru_cache
def get_sessionmaker(database_url: str | None = None):
    return sessionmaker(
        bind=get_engine(database_url), class_=Session, autoflush=False, autocommit=False
    )


def get_session():
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()
