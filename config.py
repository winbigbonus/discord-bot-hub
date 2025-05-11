import os

# Bot Configuration
DEFAULT_PREFIX = "/help slots"
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
BOT_NAME = "Rocket Gambling Bot"
BOT_DESCRIPTION = "A feature-rich Discord gambling bot with mini-games, economy, and mining!"

# Economy Configuration
STARTING_CASH = 1000
DAILY_MIN = 1000
DAILY_MAX = 5000
WEEKLY_MIN = 5000
WEEKLY_MAX = 10000
MONTHLY_MIN = 100000
MONTHLY_MAX = 500000
YEARLY_MIN = 10000000
YEARLY_MAX = 50000000
WORK_MIN = 100
WORK_MAX = 500
OVERTIME_MIN = 500
OVERTIME_MAX = 1000

# Cooldowns (in seconds)
DAILY_COOLDOWN = 86400  # 24 hours
WEEKLY_COOLDOWN = 604800  # 1 week
MONTHLY_COOLDOWN = 2592000  # 30 days
YEARLY_COOLDOWN = 31536000  # 365 days
WORK_COOLDOWN = 3600  # 1 hour
OVERTIME_COOLDOWN = 7200  # 2 hours
VOTE_COOLDOWN = 43200  # 12 hours
SPIN_COOLDOWN = 7200  # 2 hours
GIFT_COOLDOWN = 43200  # 12 hours
DIG_COOLDOWN = 300  # 5 minutes
PROCESS_COOLDOWN = 1800  # 30 minutes

# Mining Configuration
MINING_BASE_COST = 500
MINING_COST_MULTIPLIER = 1.5

# Game Configuration
MAX_BET = 1000000
MIN_BET = 10

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/rocketbot.db")

# Discord Configuration
ACTIVITY_TYPE = "playing"
ACTIVITY_NAME = "Gambling Games | $help"
STATUS = "online"
