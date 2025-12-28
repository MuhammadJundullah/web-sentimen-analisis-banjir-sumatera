import os
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

Base = declarative_base()


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, unique=True)
    author_id = Column(String)
    created_at = Column(DateTime(timezone=True))
    text = Column(Text, nullable=False)
    query = Column(String)
    source = Column(String, nullable=False)
    inserted_at = Column(DateTime(timezone=True), server_default=func.now())


def init_db() -> None:
    Base.metadata.create_all(engine)


def insert_tweets(rows: list[dict]) -> int:
    if not rows:
        return 0

    with engine.begin() as conn:
        stmt = insert(Tweet.__table__).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["tweet_id"])
        result = conn.execute(stmt)
        return result.rowcount
