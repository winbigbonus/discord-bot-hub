import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.embeds import EmbedBuilder
from database.models import GuildConfig
from database.database import get_session

class GuildCommands(commands.Cog):
    """Commands related to guild configuration and management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="config")
    @app_commands.describe(show="Show the current guild configuration")
    async def config_show(self, ctx, show: str = "show"):
        """Setup the config for your guild. You must be the guild owner or an admin added to a guild."""
        # Check if command is used in a guild
        if not ctx.guild:
            return await ctx.send("This command can only be used in a server!")
            
        # Check if user has appropriate permissions
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("You need to be a server administrator to use this command!")
            
        # Get guild config
        async with get_session() as session:
            guild_config = await session.get(GuildConfig, ctx.guild.id)
            
            if not guild_config:
                # Create default config
                guild_config = GuildConfig(
                    guild_id=ctx.guild.id,
                    prefix="$",
                    admin_ids=[ctx.guild.owner_id],
                    force_commands=False
                )
                session.add(guild_config)
                await session.commit()
                
            # Create config embed
            embed = EmbedBuilder.info(
                title=f"Configuration for {ctx.guild.name}",
                description="Current server settings:"
            )
            
            # Add config values
            embed.add_field(name="Prefix", value=guild_config.prefix, inline=True)
            
            # Add channel restrictions
            if guild_config.channel_ids:
                channel_mentions = []
                for channel_id in guild_config.channel_ids:
                    channel = ctx.guild.get_channel(channel_id)
                    if channel:
                        channel_mentions.append(channel.mention)
                    else:
                        channel_mentions.append(f"Unknown ({channel_id})")
                embed.add_field(name="Restricted Channels", value=", ".join(channel_mentions), inline=False)
            else:
                embed.add_field(name="Restricted Channels", value="None (Bot responds in all channels)", inline=False)
                
            # Add admin IDs
            admin_mentions = []
            for admin_id in guild_config.admin_ids:
                member = ctx.guild.get_member(admin_id)
                if member:
                    admin_mentions.append(member.mention)
                else:
                    admin_mentions.append(f"Unknown ({admin_id})")
            embed.add_field(name="Config Admins", value=", ".join(admin_mentions), inline=False)
            
            # Add other settings
            embed.add_field(name="Force Commands", value=str(guild_config.force_commands), inline=True)
            
            if guild_config.cash_name:
                embed.add_field(name="Cash Name", value=guild_config.cash_name, inline=True)
                
            if guild_config.cashmoji:
                embed.add_field(name="Cash Emoji", value=guild_config.cashmoji, inline=True)
                
            if guild_config.crypto_name:
                embed.add_field(name="Crypto Name", value=guild_config.crypto_name, inline=True)
                
            if guild_config.cryptomoji:
                embed.add_field(name="Crypto Emoji", value=guild_config.cryptomoji, inline=True)
                
            # Add help text
            embed.add_field(
                name="How to Configure",
                value=(
                    f"Use `/config channel` to set channel restrictions\n"
                    f"Use `/config admin_ids add @user` to add config admins\n"
                    f"Use `/config admin_ids delete @user` to remove config admins\n"
                    f"Use `/config cashmoji emoji` to set cash emoji (donators only)\n"
                    f"Use `/config cash_name name` to set cash name (donators only)\n"
                ),
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="config_channel")
    @app_commands.describe(
        channel1="A channel to use. Leave blank to allow in all channels",
        channel2="An additional channel to use (optional)",
        channel3="An additional channel to use (optional)",
        channel4="An additional channel to use (optional)",
        channel5="An additional channel to use (optional)"
    )
    async def config_channel(self, ctx,
                          channel1: discord.TextChannel = None,
                          channel2: discord.TextChannel = None,
                          channel3: discord.TextChannel = None,
                          channel4: discord.TextChannel = None,
                          channel5: discord.TextChannel = None):
        """Set the channels where the bot can respond"""
        # Check if command is used in a guild
        if not ctx.guild:
            return await ctx.send("This command can only be used in a server!")
            
        # Check if user has appropriate permissions
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("You need to be a server administrator to use this command!")
            
        # Get guild config
        async with get_session() as session:
            guild_config = await session.get(GuildConfig, ctx.guild.id)
            
            if not guild_config:
                # Create default config
                guild_config = GuildConfig(
                    guild_id=ctx.guild.id,
                    prefix="$",
                    admin_ids=[ctx.guild.owner_id],
                    force_commands=False
                )
                session.add(guild_config)
            
            # Collect channel IDs
            channels = [channel1, channel2, channel3, channel4, channel5]
            channel_ids = [channel.id for channel in channels if channel is not None]
            
            # Update config
            if not channel_ids:
                guild_config.channel_ids = []
                await session.commit()
                
                embed = EmbedBuilder.success(
                    title="Channels Updated",
                    description="The bot will now respond in all channels."
                )
                
                return await ctx.send(embed=embed)
                
            guild_config.channel_ids = channel_ids
            await session.commit()
            
            # Create success embed
            embed = EmbedBuilder.success(
                title="Channels Updated",
                description="The bot will now only respond in the following channels:"
            )
            
            # Add channel mentions
            channel_mentions = []
            for channel_id in channel_ids:
                channel = ctx.guild.get_channel(channel_id)
                if channel:
                    channel_mentions.append(channel.mention)
                    
            embed.add_field(name="Channels", value=", ".join(channel_mentions), inline=False)
            
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="config_admin_add")
    @app_commands.describe(user="Add an admin ID")
    async def config_admin_add(self, ctx, user: discord.Member):
        """Add a user to the config admins"""
        # Check if command is used in a guild
        if not ctx.guild:
            return await ctx.send("This command can only be used in a server!")
            
        # Check if user has appropriate permissions
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("You need to be a server administrator to use this command!")
            
        # Get guild config
        async with get_session() as session:
            guild_config = await session.get(GuildConfig, ctx.guild.id)
            
            if not guild_config:
                # Create default config
                guild_config = GuildConfig(
                    guild_id=ctx.guild.id,
                    prefix="$",
                    admin_ids=[ctx.guild.owner_id],
                    force_commands=False
                )
                session.add(guild_config)
            
            # Check if user is already an admin
            if user.id in guild_config.admin_ids:
                return await ctx.send(f"{user.mention} is already a config admin!")
                
            # Add user to admin IDs
            guild_config.admin_ids.append(user.id)
            await session.commit()
            
            # Create success embed
            embed = EmbedBuilder.success(
                title="Config Admin Added",
                description=f"{user.mention} can now modify the bot configuration for this server!"
            )
            
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="config_admin_remove")
    @app_commands.describe(user="Remove an admin ID")
    async def config_admin_remove(self, ctx, user: discord.Member):
        """Remove a user from the config admins"""
        # Check if command is used in a guild
        if not ctx.guild:
            return await ctx.send("This command can only be used in a server!")
            
        # Check if user has appropriate permissions
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("You need to be a server administrator to use this command!")
            
        # Get guild config
        async with get_session() as session:
            guild_config = await session.get(GuildConfig, ctx.guild.id)
            
            if not guild_config:
                return await ctx.send("This server has no custom configuration yet!")
            
            # Check if user is an admin
            if user.id not in guild_config.admin_ids:
                return await ctx.send(f"{user.mention} is not a config admin!")
                
            # Check if trying to remove the owner
            if user.id == ctx.guild.owner_id:
                return await ctx.send("You cannot remove the server owner from config admins!")
                
            # Remove user from admin IDs
            guild_config.admin_ids.remove(user.id)
            await session.commit()
            
            # Create success embed
            embed = EmbedBuilder.success(
                title="Config Admin Removed",
                description=f"{user.mention} can no longer modify the bot configuration for this server!"
            )
            
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="updates", aliases=["announcements", "announce"])
    async def updates(self, ctx):
        """Shows the latest updates for the bot, changed every time the bot is updated"""
        embed = EmbedBuilder.info(
            title="Latest Bot Updates",
            description="Here are the most recent changes and improvements to the bot:"
        )
        
        # Add update information
        embed.add_field(
            name="Version 1.0",
            value=(
                "- Initial bot release\n"
                "- Added basic economy commands\n"
                "- Added mining mini-game\n"
                "- Added gambling games\n"
                "- Added guild configuration options"
            ),
            inline=False
        )
        
        # Add any future updates here
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GuildCommands(bot))
