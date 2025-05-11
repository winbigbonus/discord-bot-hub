import asyncio
import os
import discord
from discord.ext import commands
import config
from database.database import init_db
import logging

# Setup intents for the bot
intents = discord.Intents.default()
intents.message_content = True  # Needed to read message content
intents.members = True  # Needed for user-related commands

async def setup_bot():
    """Set up and configure the bot with all cogs"""
    
    # Initialize database
    await init_db()
    
    # Create bot instance
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or(config.DEFAULT_PREFIX),
        description=config.BOT_DESCRIPTION,
        intents=intents,
        help_command=None,  # We'll implement our own help command
        case_insensitive=True
    )
    
    # Cog loading function
    async def load_cogs():
        """Load all cogs from the cogs directory"""
        cogs = [
            'cogs.player_commands',
            'cogs.mining_commands',
            'cogs.guild_commands',
            'cogs.help_commands',
            'cogs.gambling_commands'
        ]
        
        for cog in cogs:
            try:
                await bot.load_extension(cog)
                logging.info(f"Loaded cog: {cog}")
            except Exception as e:
                logging.error(f"Failed to load cog {cog}: {e}")
    
    # Bot events
    @bot.event
    async def on_ready():
        activity = discord.Activity(
            type=getattr(discord.ActivityType, config.ACTIVITY_TYPE.lower()), 
            name=config.ACTIVITY_NAME
        )
        await bot.change_presence(status=getattr(discord.Status, config.STATUS.lower()), activity=activity)
    
    @bot.event
    async def on_guild_join(guild):
        """Called when the bot joins a new server"""
        logging.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
    
    @bot.event
    async def on_command_error(ctx, error):
        """Global error handler for command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param}")
            return
            
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Bad argument: {error}")
            return
            
        # Log unexpected errors
        logging.error(f"Command error in {ctx.command}: {error}")
        await ctx.send("An error occurred while processing this command.")
    
    @bot.event
    async def on_application_command_error(ctx, error):
        """Global error handler for slash command errors"""
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await ctx.response.send_message(
                f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )
            return
            
        # Log unexpected errors
        logging.error(f"Slash command error in {ctx.command}: {error}")
        
        # If the interaction has already been responded to
        try:
            await ctx.response.send_message("An error occurred while processing this command.", ephemeral=True)
        except:
            await ctx.followup.send("An error occurred while processing this command.", ephemeral=True)
    
    # Load all cogs
    await load_cogs()
    
    return bot
