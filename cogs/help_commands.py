import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.embeds import EmbedBuilder
import config
from utils.helpers import create_paginated_embed

class HelpCommands(commands.Cog):
    """Commands related to help and information"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="help", aliases=["h", "wtf"])
    @app_commands.describe(command_name="The command to look up. Start typing to search for a command")
    async def help(self, ctx, *, command_name: str = None):
        """Show the help for all the commands available in the bot"""
        if command_name:
            await self.show_command_help(ctx, command_name)
        else:
            await self.show_general_help(ctx)
    
    async def show_command_help(self, ctx, command_name):
        """Show help for a specific command"""
        # Clean command name
        command_name = command_name.lower().strip()
        
        # Find the command
        command = self.bot.get_command(command_name)
        if command is None:
            # Check aliases
            for cmd in self.bot.commands:
                if cmd.aliases and command_name in [alias.lower() for alias in cmd.aliases]:
                    command = cmd
                    break
        
        if command is None:
            return await ctx.send(f"Command `{command_name}` not found. Use `{config.DEFAULT_PREFIX}help` to see all commands.")
            
        # Create embed for command
        embed = EmbedBuilder.info(
            title=f"Help: {command.name}",
            description=command.help or "No description available."
        )
        
        # Add usage info
        usage = f"{config.DEFAULT_PREFIX}{command.name}"
        if command.signature:
            usage += f" {command.signature}"
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
        
        # Add aliases if any
        if command.aliases:
            aliases = ", ".join([f"{config.DEFAULT_PREFIX}{alias}" for alias in command.aliases])
            embed.add_field(name="Aliases", value=aliases, inline=False)
        
        # Add cooldown if any
        if command._buckets and command._buckets._cooldown:
            cooldown = command._buckets._cooldown
            embed.add_field(
                name="Cooldown",
                value=f"{cooldown.rate} use(s) every {cooldown.per:.0f} seconds",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def show_general_help(self, ctx):
        """Show general help with command categories"""
        # Group commands by cogs
        command_categories = {}
        for command in self.bot.commands:
            if command.hidden:
                continue
                
            category = command.cog.qualified_name if command.cog else "No Category"
            if category not in command_categories:
                command_categories[category] = []
                
            command_categories[category].append(command)
        
        # Create main help embed
        main_embed = EmbedBuilder.info(
            title="Bot Help",
            description=f"Use `{config.DEFAULT_PREFIX}help [command]` for more info on a command."
        )
        
        # Add categories overview
        for category, commands in command_categories.items():
            main_embed.add_field(
                name=category,
                value=", ".join([f"`{cmd.name}`" for cmd in commands]),
                inline=False
            )
        
        # Add additional info
        main_embed.add_field(
            name="Links",
            value=(
                "[Support Server](https://discord.gg/support)\n"
                "[Invite Bot](https://discord.com/oauth2/authorize)\n"
                "[Vote for Bot](https://top.gg/bot/vote)"
            ),
            inline=False
        )
        
        await ctx.send(embed=main_embed)
    
    @commands.hybrid_command(name="invite")
    async def invite(self, ctx):
        """Shares the details of how to add the bot"""
        embed = EmbedBuilder.info(
            title="Invite Rocket Gambling Bot",
            description="Add the bot to your own server!"
        )
        
        embed.add_field(
            name="Invite Link",
            value="[Click here to invite the bot](https://discord.com/oauth2/authorize)",
            inline=False
        )
        
        embed.add_field(
            name="Support",
            value="[Join our support server](https://discord.gg/support)",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="stats", aliases=["ping", "status", "about", "info", "owner"])
    async def stats(self, ctx):
        """Shows a selection of bot stats including ping, player count, guild count etc."""
        # Get bot statistics
        guild_count = len(self.bot.guilds)
        member_count = sum(guild.member_count for guild in self.bot.guilds)
        
        # Get ping latency
        ping = round(self.bot.latency * 1000)
        
        # Create embed
        embed = EmbedBuilder.info(
            title="Bot Statistics",
            description="Here are some statistics about the bot:"
        )
        
        # Add stats
        embed.add_field(name="Servers", value=f"{guild_count:,}", inline=True)
        embed.add_field(name="Users", value=f"{member_count:,}", inline=True)
        embed.add_field(name="Ping", value=f"{ping}ms", inline=True)
        
        # Add uptime (would need to track this separately)
        
        # Add version
        embed.add_field(name="Version", value="1.0", inline=True)
        
        # Add links
        embed.add_field(
            name="Links",
            value=(
                "[Support Server](https://discord.gg/support)\n"
                "[Invite Bot](https://discord.com/oauth2/authorize)\n"
                "[Vote for Bot](https://top.gg/bot/vote)"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="support")
    async def support(self, ctx):
        """Shares a link to the support server"""
        embed = EmbedBuilder.info(
            title="Support Server",
            description="Need help with the bot? Join our support server!"
        )
        
        embed.add_field(
            name="Join Link",
            value="[Click here to join](https://discord.gg/support)",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="donate")
    async def donate(self, ctx):
        """Shares a link to donate to the bot"""
        embed = EmbedBuilder.info(
            title="Support the Bot",
            description="Donate to help keep the bot running and unlock special perks!"
        )
        
        embed.add_field(
            name="Donation Options",
            value=(
                "**Patreon:** [Click here](https://patreon.com/bot)\n"
                "**PayPal:** [Click here](https://paypal.me/bot)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Perks",
            value=(
                "- **Custom cash name/emoji** for your server\n"
                "- **Increased cash multipliers** for rewards\n"
                "- **Priority support** in our server\n"
                "- **Early access** to new features"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="delete_my_data")
    async def delete_my_data(self, ctx):
        """The command used to clear all of your data from the bot. Use this if you want to start from scratch"""
        # Create confirmation message
        embed = EmbedBuilder.warning(
            title="Delete Your Data",
            description="⚠️ **WARNING: This will delete ALL your data from the bot!** ⚠️"
        )
        
        embed.add_field(
            name="What will be deleted",
            value=(
                "- All your economy data (cash, items, etc.)\n"
                "- All your mining progress\n"
                "- All your game statistics\n"
                "- Any other personal data stored by the bot"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Confirmation Required",
            value="To confirm, type `yes, delete my data` within 30 seconds.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Wait for confirmation
        def check(message):
            return message.author == ctx.author and message.content.lower() == "yes, delete my data"
            
        try:
            await self.bot.wait_for("message", check=check, timeout=30.0)
            
            # If confirmed, delete data
            from database.database import get_session
            from database.models import User, MiningStats, Inventory
            
            async with get_session() as session:
                # Delete all user data
                user = await session.get(User, ctx.author.id)
                if user:
                    await session.delete(user)
                    
                mining_stats = await session.get(MiningStats, ctx.author.id)
                if mining_stats:
                    await session.delete(mining_stats)
                    
                inventory = await session.get(Inventory, ctx.author.id)
                if inventory:
                    await session.delete(inventory)
                    
                # Commit changes
                await session.commit()
                
            # Send success message
            success_embed = EmbedBuilder.success(
                title="Data Deleted",
                description="All your data has been deleted from the bot. You're starting fresh!"
            )
            
            await ctx.send(embed=success_embed)
            
        except asyncio.TimeoutError:
            # If timed out, cancel
            cancel_embed = EmbedBuilder.error(
                title="Deletion Cancelled",
                description="Data deletion was cancelled due to timeout."
            )
            
            await ctx.send(embed=cancel_embed)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
