import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from datetime import datetime
import config
from utils.cooldowns import cooldown
from utils.embeds import EmbedBuilder
from utils.economy import EconomyManager
from utils.helpers import parse_amount, get_mentioned_user, format_number
from database.models import User, Transaction
from database.database import get_session

class PlayerCommands(commands.Cog):
    """Commands related to player economy and profile management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager(bot)
    
    #
    # PROFILE AND BALANCE COMMANDS
    #
    
    @commands.hybrid_command(name="profile", aliases=["me", "bal", "balance", "my"])
    @app_commands.describe(page="The sub-page to show")
    async def profile(self, ctx, page: str = None):
        """Show your player stats including cash, top scores and experience"""
        user_id = ctx.author.id
        
        async with get_session() as session:
            user_db = await session.get(User, user_id)
            if not user_db:
                user_db = await self.economy.get_user(user_id)
            
            # Get sub-page
            valid_pages = ["score", "stats", "mine", "achievements", "inventory"]
            if page and page.lower() in valid_pages:
                page = page.lower()
            else:
                page = None
            
            # Generate appropriate embed based on page
            if page == "score" or page == "stats":
                # Get top game scores
                scores = {}  # Replace with actual score fetching
                embed = EmbedBuilder.profile(
                    ctx.author, 
                    user_db.cash,
                    user_db.level,
                    user_db.experience,
                    scores
                )
                embed.title = f"{ctx.author.name}'s Game Stats"
                
            elif page == "mine":
                # Show mining stats
                embed = EmbedBuilder.info(
                    title=f"{ctx.author.name}'s Mine",
                    description="Your mining operation stats",
                    thumbnail=ctx.author.avatar.url if ctx.author.avatar else None
                )
                # Add mining stats fields here
                
            elif page == "achievements" or page == "inventory":
                # Show achievements or inventory
                embed = EmbedBuilder.info(
                    title=f"{ctx.author.name}'s {page.capitalize()}",
                    description=f"Your {page}",
                    thumbnail=ctx.author.avatar.url if ctx.author.avatar else None
                )
                # Add achievement or inventory fields here
                
            else:
                # Default profile page
                embed = EmbedBuilder.profile(
                    ctx.author, 
                    user_db.cash,
                    user_db.level,
                    user_db.experience
                )
                
                # Add additional profile details
                embed.add_field(name="Mining Level", value=user_db.mining_level, inline=True)
                embed.add_field(name="Commands Used", value=user_db.commands_used, inline=True)
                embed.add_field(name="Games Played", value=user_db.games_played, inline=True)
            
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="lookup", aliases=["find"])
    @app_commands.describe(user="The user to look up", page="The sub-page to show")
    async def lookup(self, ctx, user: discord.Member, page: str = None):
        """Show the stats for a given player including cash, top scores and experience"""
        if not user:
            return await ctx.send("User not found.")
            
        user_id = user.id
        
        async with get_session() as session:
            user_db = await session.get(User, user_id)
            if not user_db:
                user_db = await self.economy.get_user(user_id)
            
            # Similar to profile command, but for another user
            # Generate appropriate embed based on page
            if page and page.lower() in ["score", "stats"]:
                # Get top game scores
                scores = {}  # Replace with actual score fetching
                embed = EmbedBuilder.profile(
                    user, 
                    user_db.cash,
                    user_db.level,
                    user_db.experience,
                    scores
                )
                embed.title = f"{user.name}'s Game Stats"
                
            elif page and page.lower() == "mine":
                # Show mining stats
                embed = EmbedBuilder.info(
                    title=f"{user.name}'s Mine",
                    description="Mining operation stats",
                    thumbnail=user.avatar.url if user.avatar else None
                )
                # Add mining stats fields here
                
            elif page and page.lower() in ["achievements", "inventory"]:
                # Show achievements or inventory
                page = page.lower()
                embed = EmbedBuilder.info(
                    title=f"{user.name}'s {page.capitalize()}",
                    description=f"Their {page}",
                    thumbnail=user.avatar.url if user.avatar else None
                )
                # Add achievement or inventory fields here
                
            else:
                # Default profile page
                embed = EmbedBuilder.profile(
                    user, 
                    user_db.cash,
                    user_db.level,
                    user_db.experience
                )
                
                # Add additional profile details
                embed.add_field(name="Mining Level", value=user_db.mining_level, inline=True)
                embed.add_field(name="Commands Used", value=user_db.commands_used, inline=True)
                embed.add_field(name="Games Played", value=user_db.games_played, inline=True)
            
            await ctx.send(embed=embed)
    
    #
    # ECONOMY COMMANDS
    #
    
    @commands.hybrid_command(name="daily")
    @cooldown("daily")
    async def daily(self, ctx):
        """Collect your daily ration of cash."""
        reward, new_balance = await self.economy.daily_reward(ctx.author.id)
        
        embed = EmbedBuilder.success(
            title="Daily Reward",
            description=f"You received ${reward:,} from your daily reward!",
            footer=f"New Balance: ${new_balance:,}"
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="weekly", aliases=["supporter"])
    @cooldown("weekly")
    async def weekly(self, ctx):
        """Collect your weekly ration of cash."""
        reward, new_balance = await self.economy.weekly_reward(ctx.author.id)
        
        embed = EmbedBuilder.success(
            title="Weekly Reward",
            description=f"You received ${reward:,} from your weekly reward!",
            footer=f"New Balance: ${new_balance:,}"
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="monthly", aliases=["patron"])
    @cooldown("monthly")
    async def monthly(self, ctx):
        """Collect your monthly ration of cash."""
        reward, new_balance = await self.economy.monthly_reward(ctx.author.id)
        
        embed = EmbedBuilder.success(
            title="Monthly Reward",
            description=f"You received ${reward:,} from your monthly reward!",
            footer=f"New Balance: ${new_balance:,}"
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="yearly", aliases=["godlike"])
    @cooldown("yearly")
    async def yearly(self, ctx):
        """Collect your yearly ration of cash."""
        reward, new_balance = await self.economy.yearly_reward(ctx.author.id)
        
        embed = EmbedBuilder.success(
            title="Yearly Reward",
            description=f"You received ${reward:,} from your yearly reward!",
            footer=f"New Balance: ${new_balance:,}"
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="work", aliases=["wk", "w"])
    @cooldown("work")
    async def work(self, ctx):
        """Collect your hard earned wages at work."""
        reward, new_balance = await self.economy.work_reward(ctx.author.id)
        
        embed = EmbedBuilder.success(
            title="Work Reward",
            description=f"You worked hard and earned ${reward:,}!",
            footer=f"New Balance: ${new_balance:,}"
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="overtime", aliases=["ot"])
    @cooldown("overtime")
    async def overtime(self, ctx):
        """Put in some extra time at work."""
        reward, new_balance = await self.economy.overtime_reward(ctx.author.id)
        
        embed = EmbedBuilder.success(
            title="Overtime Reward",
            description=f"You put in extra hours and earned ${reward:,}!",
            footer=f"New Balance: ${new_balance:,}"
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="send", aliases=["transfer", "give"])
    async def send(self, ctx, recipient: discord.Member = None, amount: str = None):
        """Send money to a friend!"""
        # Show send info if no arguments provided
        if not recipient or not amount:
            embed = EmbedBuilder.info(
                title="Send Cash",
                description="Send money to other users!",
                footer="Tax is based on combined sales tax of sender and receiver."
            )
            embed.add_field(name="Usage", value=f"{config.DEFAULT_PREFIX}send @user amount", inline=False)
            embed.add_field(name="Example", value=f"{config.DEFAULT_PREFIX}send @friend 10000", inline=False)
            
            return await ctx.send(embed=embed)
        
        # Check if trying to send to self
        if recipient.id == ctx.author.id:
            return await ctx.send("You can't send money to yourself!")
            
        # Get sender's cash balance
        async with get_session() as session:
            sender = await session.get(User, ctx.author.id)
            if not sender:
                sender = await self.economy.get_user(ctx.author.id)
            
            # Parse amount
            parsed_amount = parse_amount(amount, sender.cash)
            if not parsed_amount or parsed_amount <= 0:
                return await ctx.send("Please enter a valid amount!")
                
            # Default tax rate (can be adjusted based on user levels/perks)
            tax_rate = 0.05  # 5% tax
            
            # Process transaction
            success, result = await self.economy.transfer_cash(
                ctx.author.id, 
                recipient.id, 
                parsed_amount, 
                tax_rate
            )
            
            if not success:
                return await ctx.send(result)  # Error message
                
            # Create success embed
            embed = EmbedBuilder.success(
                title="Money Sent",
                description=f"Successfully sent money to {recipient.mention}!"
            )
            
            embed.add_field(name="Amount Sent", value=f"${parsed_amount:,}", inline=True)
            embed.add_field(name="Tax Paid", value=f"${result['tax']:,} ({tax_rate*100:.1f}%)", inline=True)
            embed.add_field(name="Amount Received", value=f"${result['final_amount']:,}", inline=True)
            embed.add_field(name="Your New Balance", value=f"${result['sender_balance']:,}", inline=False)
            
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="cooldowns", aliases=["cd", "c"])
    @app_commands.describe(detailed="Show exact expiry times for cooldowns")
    async def cooldowns(self, ctx, detailed: str = None):
        """Lists any active cooldowns you currently have"""
        # Initialize cooldowns if not already done
        if not hasattr(self.bot, "cooldowns"):
            from utils.cooldowns import Cooldowns
            self.bot.cooldowns = Cooldowns(self.bot)
            
        # Check for detailed option
        show_detailed = detailed in ["detailed", "d"]
        
        # Get all cooldowns for the user
        user_cooldowns = self.bot.cooldowns.get_all_cooldowns(ctx.author.id, show_detailed)
        
        # Create and send the embed
        embed = EmbedBuilder.cooldowns(ctx.author, user_cooldowns)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="gift", aliases=["gifts"])
    @app_commands.describe(recipient="The user to receive the free gift")
    @cooldown("gift")
    async def gift(self, ctx, recipient: discord.Member = None):
        """Send up to five free gifts every 12 hours!"""
        # If no recipient specified, show gift info
        if not recipient:
            embed = EmbedBuilder.info(
                title="Free Gifts",
                description="Send free gifts to other users!"
            )
            embed.add_field(
                name="Instructions", 
                value="You can send up to 5 gifts every 12 hours.\nGifts don't cost you anything, and you can't give all gifts to the same person.", 
                inline=False
            )
            embed.add_field(name="Usage", value=f"{config.DEFAULT_PREFIX}gift @user", inline=False)
            
            return await ctx.send(embed=embed)
            
        # Check if trying to gift self
        if recipient.id == ctx.author.id:
            return await ctx.send("You can't send gifts to yourself!")
            
        # TODO: Implement gift limits and tracking
        # For now, we'll just give a random reward
        gift_amount = random.randint(500, 2000)
        
        # Add gift amount to recipient
        new_balance = await self.economy.add_cash(recipient.id, gift_amount, f"Gift from {ctx.author.id}")
        
        # Create success embed
        embed = EmbedBuilder.success(
            title="Gift Sent",
            description=f"You sent a gift to {recipient.mention}!"
        )
        
        embed.add_field(name="Gift Amount", value=f"${gift_amount:,}", inline=True)
        embed.add_field(name="Recipient's New Balance", value=f"${new_balance:,}", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="leaderboard")
    @app_commands.describe(
        leaderboard="The leaderboard to choose",
        global_opt="Whether to show global scores"
    )
    async def leaderboard(self, ctx, leaderboard: str, global_opt: str = None):
        """Show the leaderboard for a game!"""
        # Validate leaderboard type
        valid_types = ["cash", "level", "mining", "blackjack", "slots", "dice"]
        
        if leaderboard.lower() not in valid_types:
            return await ctx.send(f"Invalid leaderboard type. Choose from: {', '.join(valid_types)}")
            
        # Determine if global
        is_global = global_opt in ["global", "g"]
        
        # Create leaderboard embed
        embed = EmbedBuilder.info(
            title=f"{leaderboard.capitalize()} Leaderboard",
            description=f"{'Global' if is_global else 'Server'} rankings for {leaderboard}"
        )
        
        # Get leaderboard data (simple implementation for now)
        async with get_session() as session:
            if leaderboard.lower() == "cash":
                query = """
                SELECT id, cash FROM user
                ORDER BY cash DESC
                LIMIT 10
                """
                # TODO: Filter by guild if not global
                
                # Execute the query
                result = await session.execute(query)
                entries = result.all()
                
                # Add entries to embed
                for i, (user_id, cash) in enumerate(entries, 1):
                    user = await self.bot.fetch_user(user_id)
                    embed.add_field(
                        name=f"{i}. {user.name}",
                        value=f"${cash:,}",
                        inline=False
                    )
            
            # Add other leaderboard types here
            
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="vote", aliases=["v"])
    @app_commands.describe(detailed="Show exact expiry times for cooldowns")
    async def vote(self, ctx, detailed: str = None):
        """Show the site voting instructions and your current cooldowns for voting."""
        # Check for detailed option
        show_detailed = detailed in ["detailed", "d"]
        
        # Create vote info embed
        embed = EmbedBuilder.info(
            title="Vote for Rewards",
            description="Vote for the bot on these sites to get rewards!"
        )
        
        # Add voting site information
        embed.add_field(
            name="Voting Sites",
            value=(
                "[top.gg](https://top.gg/bot/botid/vote)\n"
                "[Discord Bot List](https://discordbotlist.com/bots/botid/upvote)\n"
                "[Botlist.me](https://botlist.me/bots/botid/vote)"
            ),
            inline=False
        )
        
        # Add rewards info
        embed.add_field(
            name="Vote Rewards",
            value=(
                f"**Cash:** 100,000 × player level\n"
                f"**Crypto:** 10 × player level\n"
                f"**XP:** 5 × player level\n"
                f"**Items:** 2 × player level"
            ),
            inline=False
        )
        
        # Add vote streak info
        embed.add_field(
            name="Vote Streak",
            value=(
                "Every 7 days of voting (21 votes) your reward is tripled for one vote.\n"
                "Every 21 votes increases the base reward multiplier by 1."
            ),
            inline=False
        )
        
        # Add voting cooldown info
        if hasattr(self.bot, "cooldowns"):
            vote_cooldown = self.bot.cooldowns.get_cooldown_remaining(ctx.author.id, "vote")
            if vote_cooldown > 0:
                if show_detailed:
                    from datetime import datetime
                    # Format as timestamp
                    dt = datetime.fromtimestamp(time.time() + vote_cooldown)
                    cooldown_text = discord.utils.format_dt(dt, style='R')
                else:
                    # Format as relative time
                    cooldown_text = self.bot.cooldowns.format_cooldown_time(vote_cooldown)
                    
                embed.add_field(name="Cooldown", value=f"You can vote again in {cooldown_text}", inline=False)
            else:
                embed.add_field(name="Cooldown", value="You can vote now!", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="spin", aliases=["randomItem"])
    @cooldown("spin")
    async def spin(self, ctx):
        """Spin the wheel of fortune to win a random item!"""
        # List of potential items
        items = [
            {"name": "Common Loot Box", "value": 500, "rarity": "common"},
            {"name": "Uncommon Loot Box", "value": 1000, "rarity": "uncommon"},
            {"name": "Rare Loot Box", "value": 2500, "rarity": "rare"},
            {"name": "Epic Loot Box", "value": 5000, "rarity": "epic"},
            {"name": "Legendary Loot Box", "value": 10000, "rarity": "legendary"},
            {"name": "Mining Boost", "value": 2000, "rarity": "rare"},
            {"name": "Cash Booster", "value": 1500, "rarity": "uncommon"},
            {"name": "XP Booster", "value": 1500, "rarity": "uncommon"},
            {"name": "Random Gems", "value": 3000, "rarity": "rare"}
        ]
        
        # Weight by rarity
        weights = {
            "common": 50,
            "uncommon": 30,
            "rare": 15,
            "epic": 4,
            "legendary": 1
        }
        
        # Create weighted list
        weighted_items = []
        for item in items:
            weighted_items.extend([item] * weights[item["rarity"]])
            
        # Spin the wheel
        result = random.choice(weighted_items)
        
        # Send spinning animation
        message = await ctx.send("Spinning the wheel... 🎡")
        
        # Add suspense with typing indicator
        await ctx.typing()
        await asyncio.sleep(2)
        
        # Create result embed
        rarity_colors = {
            "common": 0x969696,      # Gray
            "uncommon": 0x1eff00,    # Green
            "rare": 0x0070dd,        # Blue
            "epic": 0xa335ee,        # Purple
            "legendary": 0xff8000    # Orange
        }
        
        embed = discord.Embed(
            title="Wheel of Fortune",
            description=f"You won a **{result['name']}**!",
            color=rarity_colors[result["rarity"]]
        )
        
        embed.add_field(name="Rarity", value=result["rarity"].capitalize(), inline=True)
        embed.add_field(name="Value", value=f"${result['value']:,}", inline=True)
        
        # Update the message
        await message.edit(content=None, embed=embed)
        
        # TODO: Add the item to the user's inventory
        # For now, just give them the cash value
        await self.economy.add_cash(ctx.author.id, result["value"], "Wheel of Fortune prize")

async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
