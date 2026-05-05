from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

db_url = str(settings.database_url)
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
pool_kwargs = (
    {"pool_size": 20, "max_overflow": 10, "pool_recycle": 3600}
    if not db_url.startswith("sqlite")
    else {}
)
engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args, **pool_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
