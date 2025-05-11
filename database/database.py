import os
import asyncio
import logging
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import config
from database.models import Base

# Get database URL from config
DATABASE_URL = config.DATABASE_URL

# SQLite needs special handling for async
if DATABASE_URL.startswith("sqlite"):
    # Convert to async format
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    
    # Create parent directories if needed
    db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session factory
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

@asynccontextmanager
async def get_session():
    """Context manager for database sessions"""
    session = async_session()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        await session.close()

async def init_db():
    """Initialize the database and create tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Check connection
        try:
            # Simple test query
            result = await conn.execute(text("SELECT 1"))
            logging.info("Database connection successful")
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            raise
    
    logging.info("Database initialized")

async def verify_db():
    """Verify database structure matches models"""
    async with engine.begin() as conn:
        # Check if tables exist
        for table in Base.metadata.sorted_tables:
            exists = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.has_table(sync_conn, table.name)
            )
            if not exists:
                logging.warning(f"Table {table.name} does not exist, creating...")
                await conn.run_sync(lambda sync_conn: table.create(sync_conn))
    
    logging.info("Database verification complete")

async def add_sample_data():
    """Add sample data for testing"""
    from database.models import User, MiningStats, Inventory
    
    # Only used for development - never in production
    if os.getenv("ENV") != "development":
        return
    
    async with get_session() as session:
        # Add sample user if doesn't exist
        user = await session.execute(select(User).where(User.id == config.OWNER_ID))
        user = user.scalar_one_or_none()
        
        if not user:
            user = User(
                id=config.OWNER_ID,
                cash=10000,
                experience=100,
                level=2,
                cash_multiplier=1.0
            )
            session.add(user)
            
            # Add mining stats
            mining_stats = MiningStats(
                user_id=config.OWNER_ID,
                mine_name="Dev Mine",
                mining_level=1,
                mine_depth=1
            )
            session.add(mining_stats)
            
            # Add inventory
            inventory = Inventory(
                user_id=config.OWNER_ID
            )
            session.add(inventory)
            
            await session.commit()
            logging.info("Added sample data for development")
