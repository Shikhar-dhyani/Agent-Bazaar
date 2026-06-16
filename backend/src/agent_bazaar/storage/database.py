from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON
from agent_bazaar.config import settings

Base = declarative_base()


class TaskRecord(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)
    raw_request = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")
    final_answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class SubtaskRecord(Base):
    __tablename__ = "subtasks"
    id = Column(String, primary_key=True)
    parent_task_id = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_capability = Column(String, nullable=False)
    dependency_ids = Column(JSON, default=list)
    status = Column(String, nullable=False, default="pending")
    result = Column(Text)
    assigned_agent_id = Column(String)
    quality_score = Column(Float)
    order = Column(Integer, default=0)


class BidRecord(Base):
    __tablename__ = "bids"
    id = Column(String, primary_key=True)
    subtask_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    estimated_latency = Column(Float, nullable=False)
    rationale = Column(Text)
    auction_score = Column(Float)
    is_winner = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReputationRecord(Base):
    __tablename__ = "reputation_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False)
    capability = Column(String, nullable=False)
    old_reputation = Column(Float, nullable=False)
    new_reputation = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    task_id = Column(String)
    recorded_at = Column(DateTime, default=datetime.utcnow)


_engine = None
_session_factory = None


def _get_engine():
    global _engine
    if _engine is None and settings.database_url:
        _engine = create_async_engine(settings.database_url, echo=False)
    return _engine


async def create_tables() -> None:
    engine = _get_engine()
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
