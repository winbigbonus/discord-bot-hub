import discord
from datetime import datetime
import config

# Standard colors
SUCCESS_COLOR = 0x57F287  # Green
ERROR_COLOR = 0xED4245    # Red
INFO_COLOR = 0x3498DB     # Blue
WARNING_COLOR = 0xFEE75C  # Yellow
DEFAULT_COLOR = 0x5865F2  # Discord Blurple

class EmbedBuilder:
    """Utility class to create standardized embeds for the bot"""
    
    @staticmethod
    def build_basic_embed(title, description, color=DEFAULT_COLOR, footer=None, thumbnail=None):
        """Create a basic embed with the specified properties"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        if footer:
            embed.set_footer(text=footer)
        else:
            embed.set_footer(text=config.BOT_NAME)
            
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        return embed
    
    @staticmethod
    def success(title, description, footer=None, thumbnail=None):
        """Create a success-themed embed"""
        return EmbedBuilder.build_basic_embed(
            title=title,
            description=description,
            color=SUCCESS_COLOR,
            footer=footer,
            thumbnail=thumbnail
        )
    
    @staticmethod
    def error(title, description, footer=None, thumbnail=None):
        """Create an error-themed embed"""
        return EmbedBuilder.build_basic_embed(
            title=title,
            description=description,
            color=ERROR_COLOR,
            footer=footer,
            thumbnail=thumbnail
        )
    
    @staticmethod
    def info(title, description, footer=None, thumbnail=None):
        """Create an info-themed embed"""
        return EmbedBuilder.build_basic_embed(
            title=title,
            description=description,
            color=INFO_COLOR,
            footer=footer,
            thumbnail=thumbnail
        )
    
    @staticmethod
    def warning(title, description, footer=None, thumbnail=None):
        """Create a warning-themed embed"""
        return EmbedBuilder.build_basic_embed(
            title=title,
            description=description,
            color=WARNING_COLOR,
            footer=footer,
            thumbnail=thumbnail
        )
    
    @staticmethod
    def profile(user, cash, level, experience, stats=None):
        """Create a profile embed for a user"""
        embed = discord.Embed(
            title=f"{user.name}'s Profile",
            description=f"Level: {level} | XP: {experience}",
            color=DEFAULT_COLOR,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Cash", value=f"${cash:,}", inline=True)
        
        if stats:
            # Add game stats if provided
            for game, score in stats.items():
                embed.add_field(name=game.capitalize(), value=f"{score:,}", inline=True)
                
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")
        
        return embed
    
    @staticmethod
    def cooldowns(user, cooldowns_dict):
        """Create a cooldown status embed for a user"""
        embed = discord.Embed(
            title=f"{user.name}'s Cooldowns",
            description="Here are your current command cooldowns:",
            color=INFO_COLOR,
            timestamp=datetime.utcnow()
        )
        
        if not cooldowns_dict:
            embed.description = "You don't have any active cooldowns!"
        else:
            for command, time_left in cooldowns_dict.items():
                embed.add_field(name=command.capitalize(), value=time_left, inline=True)
                
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")
        
        return embed
    
    @staticmethod
    def help_command(command, description, usage, examples=None, aliases=None, cooldown=None):
        """Create a help embed for a specific command"""
        embed = discord.Embed(
            title=f"Help: {command}",
            description=description,
            color=INFO_COLOR,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Usage", value=usage, inline=False)
        
        if examples:
            embed.add_field(name="Examples", value=examples, inline=False)
            
        if aliases:
            embed.add_field(name="Aliases", value=", ".join(aliases), inline=True)
            
        if cooldown:
            embed.add_field(name="Cooldown", value=cooldown, inline=True)
            
        embed.set_footer(text=f"Use {config.DEFAULT_PREFIX}help [command] for more info on a command.")
        
        return embed
