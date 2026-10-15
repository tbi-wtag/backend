from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.database.async_url,
    pool_pre_ping=True,
    pool_size=35,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,
)

local_session = async_sessionmaker(
    bind = engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db():
    db = local_session()
    try:
        yield db
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
    

