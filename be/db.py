import os
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine, func, select, delete, text as sql_text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.dialects.postgresql import JSONB
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


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    sentiment_label = Column(String)
    sentiment_score = Column(Float)
    categories = Column(JSONB, nullable=False, server_default=sql_text("'[]'::jsonb"))
    all_predictions = Column(JSONB, nullable=False, server_default=sql_text("'{}'::jsonb"))
    source = Column(String, nullable=False, server_default=sql_text("'manual'"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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


def insert_analysis_history(payload: dict) -> dict | None:
    with engine.begin() as conn:
        stmt = AnalysisHistory.__table__.insert().values(**payload).returning(
            AnalysisHistory.id,
            AnalysisHistory.created_at,
        )
        result = conn.execute(stmt).first()
        if not result:
            return None
        mapping = result._mapping
        return {"id": mapping["id"], "created_at": mapping["created_at"]}


def fetch_analysis_history(limit: int = 50, offset: int = 0) -> list[dict]:
    with engine.begin() as conn:
        stmt = (
            select(AnalysisHistory.__table__)
            .order_by(AnalysisHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = conn.execute(stmt).mappings().all()
        return [dict(row) for row in rows]


def delete_analysis_history(item_id: int) -> int:
    with engine.begin() as conn:
        stmt = delete(AnalysisHistory).where(AnalysisHistory.id == item_id)
        result = conn.execute(stmt)
        return result.rowcount


def clear_analysis_history() -> int:
    with engine.begin() as conn:
        stmt = delete(AnalysisHistory)
        result = conn.execute(stmt)
        return result.rowcount
