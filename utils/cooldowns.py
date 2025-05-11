import time
import asyncio
from datetime import datetime, timedelta
import discord
from discord.ext import commands
import config

class Cooldowns:
    """Utility class to handle cooldowns for various commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        
    def get_cooldown_remaining(self, user_id, command_name):
        """Get the remaining cooldown time for a user and command"""
        key = f"{user_id}:{command_name}"
        if key not in self.cooldowns:
            return 0
            
        expiry_time = self.cooldowns[key]
        now = time.time()
        
        if now >= expiry_time:
            del self.cooldowns[key]
            return 0
            
        return int(expiry_time - now)
    
    def set_cooldown(self, user_id, command_name, duration):
        """Set a cooldown for a user and command"""
        key = f"{user_id}:{command_name}"
        self.cooldowns[key] = time.time() + duration
        
    def is_on_cooldown(self, user_id, command_name):
        """Check if a command is on cooldown for a user"""
        return self.get_cooldown_remaining(user_id, command_name) > 0
        
    def format_cooldown_time(self, seconds):
        """Format cooldown time into a human-readable string"""
        if seconds <= 0:
            return "Ready"
            
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 and not days and not hours:
            parts.append(f"{seconds}s")
            
        return " ".join(parts)
    
    def get_all_cooldowns(self, user_id, detailed=False):
        """Get all active cooldowns for a user"""
        now = time.time()
        user_cooldowns = {}
        
        # Check all commands with potential cooldowns
        commands = {
            "daily": config.DAILY_COOLDOWN,
            "weekly": config.WEEKLY_COOLDOWN,
            "monthly": config.MONTHLY_COOLDOWN,
            "yearly": config.YEARLY_COOLDOWN,
            "work": config.WORK_COOLDOWN,
            "overtime": config.OVERTIME_COOLDOWN,
            "vote": config.VOTE_COOLDOWN,
            "spin": config.SPIN_COOLDOWN, 
            "gift": config.GIFT_COOLDOWN,
            "dig": config.DIG_COOLDOWN,
            "process": config.PROCESS_COOLDOWN
        }
        
        for cmd_name, cooldown_duration in commands.items():
            key = f"{user_id}:{cmd_name}"
            if key in self.cooldowns:
                expiry_time = self.cooldowns[key]
                if now < expiry_time:
                    if detailed:
                        # Format as timestamp
                        dt = datetime.fromtimestamp(expiry_time)
                        user_cooldowns[cmd_name] = discord.utils.format_dt(dt, style='R')
                    else:
                        # Format as relative time
                        remaining = int(expiry_time - now)
                        user_cooldowns[cmd_name] = self.format_cooldown_time(remaining)
        
        return user_cooldowns

# Discord command check for cooldowns
def cooldown(cooldown_type):
    """Custom cooldown check for commands"""
    async def predicate(ctx):
        user_id = ctx.author.id
        command_name = ctx.command.name.lower()
        
        # Get the appropriate cooldown duration from config
        cooldown_duration = getattr(config, f"{cooldown_type.upper()}_COOLDOWN", 0)
        if cooldown_duration <= 0:
            return True
            
        # Get bot instance
        bot = ctx.bot
        if not hasattr(bot, "cooldowns"):
            bot.cooldowns = Cooldowns(bot)
            
        # Check if command is on cooldown
        remaining = bot.cooldowns.get_cooldown_remaining(user_id, command_name)
        if remaining > 0:
            raise commands.CommandOnCooldown(
                cooldown=commands.Cooldown(1, cooldown_duration),
                retry_after=remaining,
                type=commands.BucketType.user
            )
            
        # Set cooldown
        bot.cooldowns.set_cooldown(user_id, command_name, cooldown_duration)
        return True
        
    return commands.check(predicate)
