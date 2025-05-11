from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table, DateTime, Text, ARRAY, JSON, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Model representing a Discord user"""
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True)  # Discord user ID
    cash = Column(Integer, default=1000)
    experience = Column(Integer, default=0)
    level = Column(Integer, default=1)
    
    # Additional stats
    games_played = Column(Integer, default=0)
    commands_used = Column(Integer, default=0)
    join_date = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Bonuses and settings
    cash_multiplier = Column(Float, default=1.0)
    mining_level = Column(Integer, default=1)
    lottery_tickets = Column(Integer, default=0)
    
    # Relationships
    stats = relationship("GameStats", back_populates="user")
    mining_stats = relationship("MiningStats", uselist=False, back_populates="user")
    inventory = relationship("Inventory", uselist=False, back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    boosts = relationship("Boost", back_populates="user")

class Transaction(Base):
    """Model representing a cash transaction"""
    __tablename__ = "transaction"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    amount = Column(Integer, nullable=False)
    type = Column(String(16), nullable=False)  # credit or debit
    reason = Column(String(128))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")

class GameStats(Base):
    """Model representing a user's stats for a specific game"""
    __tablename__ = "game_stats"
    
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    game_name = Column(String(32), primary_key=True)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    total_bet = Column(Integer, default=0)
    total_won = Column(Integer, default=0)
    highest_win = Column(Integer, default=0)
    last_played = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="stats")
    
    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'game_name', name='pk_game_stats'),
    )

class MiningStats(Base):
    """Model representing a user's mining stats"""
    __tablename__ = "mining_stats"
    
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    mine_name = Column(String(64), default="My Mine")
    mining_level = Column(Integer, default=1)
    mine_depth = Column(Integer, default=1)
    gems_found = Column(Integer, default=0)
    ores_mined = Column(Integer, default=0)
    unprocessed_materials = Column(Integer, default=0)
    last_dig = Column(DateTime)
    last_process = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="mining_stats")
    mining_units = relationship("MiningUnit", back_populates="mining_stats")

class MiningUnit(Base):
    """Model representing a mining unit that generates resources"""
    __tablename__ = "mining_unit"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("mining_stats.user_id"))
    unit_type = Column(String(32), nullable=False)
    level = Column(Integer, default=1)
    quantity = Column(Integer, default=1)
    production_rate = Column(Float, default=1.0)
    last_collected = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mining_stats = relationship("MiningStats", back_populates="mining_units")

class Inventory(Base):
    """Model representing a user's inventory"""
    __tablename__ = "inventory"
    
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    
    # Mining resources
    coal = Column(Integer, default=0)
    iron = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    diamond = Column(Integer, default=0)
    emerald = Column(Integer, default=0)
    redstone = Column(Integer, default=0)
    lapis = Column(Integer, default=0)
    
    # Crafting materials
    tech_packs = Column(Integer, default=0)
    utility_packs = Column(Integer, default=0)
    production_packs = Column(Integer, default=0)
    
    # Boosts and items
    loot_boxes = Column(Integer, default=0)
    mining_boosts = Column(Integer, default=0)
    
    # Items JSON field for extensibility
    items = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="inventory")

class Boost(Base):
    """Model representing a temporary boost"""
    __tablename__ = "boost"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    boost_type = Column(String(32), nullable=False)
    multiplier = Column(Float, default=1.0)
    duration = Column(Integer, default=3600)  # In seconds
    start_time = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="boosts")

class GuildConfig(Base):
    """Model representing a Discord guild's configuration"""
    __tablename__ = "guild_config"
    
    guild_id = Column(Integer, primary_key=True)  # Discord guild ID
    prefix = Column(String(5), default="$")
    admin_ids = Column(JSON, default=list)  # List of admin user IDs
    channel_ids = Column(JSON, default=list)  # List of allowed channel IDs
    force_commands = Column(Boolean, default=False)
    
    # Premium features
    cash_name = Column(String(24))
    cashmoji = Column(String(32))
    crypto_name = Column(String(24))
    cryptomoji = Column(String(32))
    is_premium = Column(Boolean, default=False)
    
    # Last update timestamp
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Goal(Base):
    """Model representing a daily goal/challenge"""
    __tablename__ = "goal"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(128), nullable=False)
    type = Column(String(32), nullable=False)  # Type of goal (play_games, win_games, earn_cash, etc.)
    target = Column(Integer, nullable=False)  # Target value to reach
    reward_cash = Column(Integer, default=0)
    reward_xp = Column(Integer, default=0)
    reward_items = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)

class UserGoal(Base):
    """Model representing a user's progress on goals"""
    __tablename__ = "user_goal"
    
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    goal_id = Column(Integer, ForeignKey("goal.id"), primary_key=True)
    progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'goal_id', name='pk_user_goal'),
    )
