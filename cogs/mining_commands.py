import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import config
from utils.cooldowns import cooldown
from utils.embeds import EmbedBuilder
from utils.economy import EconomyManager
from utils.helpers import parse_amount, get_mentioned_user, format_number
from database.models import User, MiningStats, Inventory
from database.database import get_session

class MiningCommands(commands.Cog):
    """Commands related to the mining mini-game"""
    
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager(bot)
    
    @commands.hybrid_command(name="start_mine", aliases=["startMine", "start"])
    async def start_mine(self, ctx, *, name: str = None):
        """Start your mining career! Takes an optional name"""
        # Use the user's name if none provided
        if not name:
            name = ctx.author.name + "'s Mine"
            
        # Check if user already has a mine
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
                
            # Check if mining stats already exist
            mining_stats = await session.get(MiningStats, ctx.author.id)
            
            if mining_stats:
                # Update name if mine already exists
                mining_stats.mine_name = name
                await session.commit()
                
                embed = EmbedBuilder.info(
                    title="Mine Renamed",
                    description=f"Your mine has been renamed to **{name}**!"
                )
                
                return await ctx.send(embed=embed)
                
            # Create new mining stats
            mining_stats = MiningStats(
                user_id=ctx.author.id,
                mine_name=name,
                mining_level=1,
                mine_depth=1,
                gems_found=0,
                ores_mined=0,
                unprocessed_materials=0
            )
            
            session.add(mining_stats)
            await session.commit()
            
            # Create success embed
            embed = EmbedBuilder.success(
                title="Mine Created",
                description=f"You have started your mining career with **{name}**!"
            )
            
            embed.add_field(name="Starting Level", value="1", inline=True)
            embed.add_field(name="Starting Depth", value="1 meter", inline=True)
            embed.add_field(
                name="Next Steps",
                value=f"Use `{config.DEFAULT_PREFIX}dig` to start mining for resources!\nUse `{config.DEFAULT_PREFIX}mine` to see your mine stats.",
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="mine", aliases=["m"])
    async def mine(self, ctx):
        """Shows the information about your mine and the mine shop."""
        # Check if user has started mining
        async with get_session() as session:
            mining_stats = await session.get(MiningStats, ctx.author.id)
            
            if not mining_stats:
                embed = EmbedBuilder.error(
                    title="No Mine Found",
                    description=f"You haven't started mining yet! Use `{config.DEFAULT_PREFIX}start_mine` to begin."
                )
                return await ctx.send(embed=embed)
                
            # Get user inventory
            inventory = await session.get(Inventory, ctx.author.id)
            if not inventory:
                # Create empty inventory
                inventory = Inventory(user_id=ctx.author.id)
                session.add(inventory)
                await session.commit()
            
            # Create mine info embed
            embed = EmbedBuilder.info(
                title=f"{mining_stats.mine_name}",
                description=f"Level {mining_stats.mining_level} Mine | Depth: {mining_stats.mine_depth}m"
            )
            
            # Add mining stats
            embed.add_field(name="Ores Mined", value=format_number(mining_stats.ores_mined), inline=True)
            embed.add_field(name="Gems Found", value=format_number(mining_stats.gems_found), inline=True)
            embed.add_field(name="Unprocessed Materials", value=format_number(mining_stats.unprocessed_materials), inline=True)
            
            # Add resources
            embed.add_field(name="Coal", value=format_number(inventory.coal), inline=True)
            embed.add_field(name="Iron", value=format_number(inventory.iron), inline=True)
            embed.add_field(name="Gold", value=format_number(inventory.gold), inline=True)
            embed.add_field(name="Diamond", value=format_number(inventory.diamond), inline=True)
            embed.add_field(name="Emerald", value=format_number(inventory.emerald), inline=True)
            embed.add_field(name="Redstone", value=format_number(inventory.redstone), inline=True)
            embed.add_field(name="Lapis", value=format_number(inventory.lapis), inline=True)
            
            # Add mining units if any
            # TODO: Implement mining units
            
            # Add command hints
            embed.add_field(
                name="Commands",
                value=(
                    f"`{config.DEFAULT_PREFIX}dig` - Mine for resources\n"
                    f"`{config.DEFAULT_PREFIX}process` - Process unprocessed materials\n"
                    f"`{config.DEFAULT_PREFIX}inventory` - View your inventory\n"
                    f"`{config.DEFAULT_PREFIX}mine shop` - View mining units shop\n"
                    f"`{config.DEFAULT_PREFIX}upgrade miner` - Upgrade your mining units"
                ),
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="dig", aliases=["d"])
    @cooldown("dig")
    async def dig(self, ctx):
        """Dig in the mines to collect coal, ores and unprocessed materials (UM)!"""
        # Check if user has started mining
        async with get_session() as session:
            mining_stats = await session.get(MiningStats, ctx.author.id)
            
            if not mining_stats:
                embed = EmbedBuilder.error(
                    title="No Mine Found",
                    description=f"You haven't started mining yet! Use `{config.DEFAULT_PREFIX}start_mine` to begin."
                )
                return await ctx.send(embed=embed)
                
            # Get user inventory
            inventory = await session.get(Inventory, ctx.author.id)
            if not inventory:
                # Create empty inventory
                inventory = Inventory(user_id=ctx.author.id)
                session.add(inventory)
                await session.commit()
            
            # Calculate resources found based on mining level
            level_multiplier = mining_stats.mining_level * 0.5
            
            # Base resources
            coal_found = random.randint(5, 15) + int(5 * level_multiplier)
            iron_found = random.randint(3, 10) + int(3 * level_multiplier)
            gold_found = random.randint(1, 5) + int(1 * level_multiplier)
            unprocessed_found = random.randint(10, 20) + int(10 * level_multiplier)
            
            # Update inventory
            inventory.coal += coal_found
            inventory.iron += iron_found
            inventory.gold += gold_found
            mining_stats.unprocessed_materials += unprocessed_found
            mining_stats.ores_mined += coal_found + iron_found + gold_found
            
            # Random chance to increase mine depth
            if random.random() < 0.2:  # 20% chance
                mining_stats.mine_depth += 1
                depth_increased = True
            else:
                depth_increased = False
                
            # Random chance to find rare gem directly
            rare_gem_found = None
            if random.random() < 0.05:  # 5% chance
                gems = ["diamond", "emerald", "redstone", "lapis"]
                weights = [1, 2, 3, 3]  # Lower weights for rarer gems
                
                gem_index = random.choices(range(len(gems)), weights=weights, k=1)[0]
                gem_name = gems[gem_index]
                gem_amount = random.randint(1, 3)
                
                # Update inventory with the found gem
                setattr(inventory, gem_name, getattr(inventory, gem_name) + gem_amount)
                mining_stats.gems_found += gem_amount
                
                rare_gem_found = {
                    "name": gem_name.capitalize(),
                    "amount": gem_amount
                }
            
            # Commit changes
            await session.commit()
            
            # Create mining results embed
            embed = EmbedBuilder.success(
                title="Mining Results",
                description=f"You went mining in **{mining_stats.mine_name}** and found:"
            )
            
            # Add resources found
            embed.add_field(name="Coal", value=format_number(coal_found), inline=True)
            embed.add_field(name="Iron", value=format_number(iron_found), inline=True)
            embed.add_field(name="Gold", value=format_number(gold_found), inline=True)
            embed.add_field(name="Unprocessed Materials", value=format_number(unprocessed_found), inline=True)
            
            # Add rare gem if found
            if rare_gem_found:
                embed.add_field(
                    name="Rare Find!",
                    value=f"You found {rare_gem_found['amount']} {rare_gem_found['name']}!",
                    inline=False
                )
                
            # Add depth increase if happened
            if depth_increased:
                embed.add_field(
                    name="Mine Depth Increased!",
                    value=f"Your mine is now {mining_stats.mine_depth}m deep!",
                    inline=False
                )
                
            # Add processing reminder if lots of unprocessed materials
            if mining_stats.unprocessed_materials > 100:
                embed.add_field(
                    name="Reminder",
                    value=f"You have {format_number(mining_stats.unprocessed_materials)} unprocessed materials. Use `{config.DEFAULT_PREFIX}process` to find gems!",
                    inline=False
                )
                
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="process", aliases=["p", "pr"])
    @cooldown("process")
    async def process(self, ctx):
        """Process all your unprocessed materials (UM) to find diamonds, emeralds, lapis and redstone!"""
        # Check if user has started mining
        async with get_session() as session:
            mining_stats = await session.get(MiningStats, ctx.author.id)
            
            if not mining_stats:
                embed = EmbedBuilder.error(
                    title="No Mine Found",
                    description=f"You haven't started mining yet! Use `{config.DEFAULT_PREFIX}start_mine` to begin."
                )
                return await ctx.send(embed=embed)
                
            # Check if user has unprocessed materials
            if mining_stats.unprocessed_materials <= 0:
                embed = EmbedBuilder.error(
                    title="No Materials to Process",
                    description=f"You don't have any unprocessed materials. Use `{config.DEFAULT_PREFIX}dig` to mine for more!"
                )
                return await ctx.send(embed=embed)
                
            # Get user inventory
            inventory = await session.get(Inventory, ctx.author.id)
            if not inventory:
                # Create empty inventory
                inventory = Inventory(user_id=ctx.author.id)
                session.add(inventory)
                await session.commit()
            
            # Calculate gems found based on unprocessed materials and mining level
            amount = mining_stats.unprocessed_materials
            level_bonus = mining_stats.mining_level * 0.02  # 2% bonus per level
            
            # Base gem find rates (adjusted by level)
            diamond_rate = 0.005 + level_bonus  # 0.5% + level bonus
            emerald_rate = 0.01 + level_bonus   # 1% + level bonus
            redstone_rate = 0.03 + level_bonus  # 3% + level bonus
            lapis_rate = 0.03 + level_bonus     # 3% + level bonus
            
            # Calculate gem amounts
            diamond_found = int(amount * diamond_rate)
            emerald_found = int(amount * emerald_rate)
            redstone_found = int(amount * redstone_rate)
            lapis_found = int(amount * lapis_rate)
            
            # Ensure at least some gems are found
            diamond_found = max(1, diamond_found) if random.random() < diamond_rate * 10 else 0
            emerald_found = max(1, emerald_found) if random.random() < emerald_rate * 5 else 0
            redstone_found = max(1, redstone_found)
            lapis_found = max(1, lapis_found)
            
            # Update inventory
            inventory.diamond += diamond_found
            inventory.emerald += emerald_found
            inventory.redstone += redstone_found
            inventory.lapis += lapis_found
            
            # Update mining stats
            total_gems = diamond_found + emerald_found + redstone_found + lapis_found
            mining_stats.gems_found += total_gems
            mining_stats.unprocessed_materials = 0  # Reset unprocessed materials
            
            # Commit changes
            await session.commit()
            
            # Create processing results embed
            embed = EmbedBuilder.success(
                title="Processing Results",
                description=f"You processed {format_number(amount)} unprocessed materials and found:"
            )
            
            # Add gems found
            if diamond_found > 0:
                embed.add_field(name="Diamond", value=format_number(diamond_found), inline=True)
            if emerald_found > 0:
                embed.add_field(name="Emerald", value=format_number(emerald_found), inline=True)
            embed.add_field(name="Redstone", value=format_number(redstone_found), inline=True)
            embed.add_field(name="Lapis", value=format_number(lapis_found), inline=True)
            
            # Add totals
            embed.add_field(
                name="Total Gems Found",
                value=format_number(total_gems),
                inline=False
            )
                
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="inventory", aliases=["inv", "i"])
    async def inventory(self, ctx):
        """Shows your mining inventory"""
        # Check if user has started mining
        async with get_session() as session:
            mining_stats = await session.get(MiningStats, ctx.author.id)
            
            if not mining_stats:
                embed = EmbedBuilder.error(
                    title="No Mine Found",
                    description=f"You haven't started mining yet! Use `{config.DEFAULT_PREFIX}start_mine` to begin."
                )
                return await ctx.send(embed=embed)
                
            # Get user inventory
            inventory = await session.get(Inventory, ctx.author.id)
            if not inventory:
                # Create empty inventory
                inventory = Inventory(user_id=ctx.author.id)
                session.add(inventory)
                await session.commit()
            
            # Create inventory embed
            embed = EmbedBuilder.info(
                title=f"{ctx.author.name}'s Mining Inventory",
                description="Your mining resources and items"
            )
            
            # Add ores section
            embed.add_field(name="__Ores__", value="\u200b", inline=False)
            embed.add_field(name="Coal", value=format_number(inventory.coal), inline=True)
            embed.add_field(name="Iron", value=format_number(inventory.iron), inline=True)
            embed.add_field(name="Gold", value=format_number(inventory.gold), inline=True)
            
            # Add gems section
            embed.add_field(name="__Gems__", value="\u200b", inline=False)
            embed.add_field(name="Diamond", value=format_number(inventory.diamond), inline=True)
            embed.add_field(name="Emerald", value=format_number(inventory.emerald), inline=True)
            embed.add_field(name="Redstone", value=format_number(inventory.redstone), inline=True)
            embed.add_field(name="Lapis", value=format_number(inventory.lapis), inline=True)
            
            # Add crafting materials section
            embed.add_field(name="__Crafting Materials__", value="\u200b", inline=False)
            embed.add_field(name="Tech Packs", value=format_number(inventory.tech_packs), inline=True)
            embed.add_field(name="Utility Packs", value=format_number(inventory.utility_packs), inline=True)
            embed.add_field(name="Production Packs", value=format_number(inventory.production_packs), inline=True)
            
            # Add unprocessed materials
            embed.add_field(
                name="__Unprocessed Materials__",
                value=format_number(mining_stats.unprocessed_materials),
                inline=False
            )
            
            # Add mining units if any
            # TODO: Implement mining units display
            
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="craft", aliases=["cft"])
    @app_commands.describe(
        type="The type of pack to craft leave blank to see menu",
        amount="The amount to craft - Use 'm' for max"
    )
    async def craft(self, ctx, type: str = None, amount: str = None):
        """Craft packs to use when buying new units or research!"""
        # If no type specified, show craft menu
        if not type:
            embed = EmbedBuilder.info(
                title="Crafting Menu",
                description="Craft packs for upgrading and purchasing mining units!"
            )
            
            # Add pack information
            embed.add_field(
                name="Tech Pack (tp)",
                value=(
                    "**Requirements:**\n"
                    "- 50 Redstone\n"
                    "- 20 Lapis\n"
                    "- 10 Gold"
                ),
                inline=True
            )
            
            embed.add_field(
                name="Utility Pack (up)",
                value=(
                    "**Requirements:**\n"
                    "- 30 Iron\n"
                    "- 15 Gold\n"
                    "- 5 Diamond"
                ),
                inline=True
            )
            
            embed.add_field(
                name="Production Pack (pp)",
                value=(
                    "**Requirements:**\n"
                    "- 100 Coal\n"
                    "- 50 Iron\n"
                    "- 5 Emerald"
                ),
                inline=True
            )
            
            embed.add_field(
                name="Usage",
                value=f"`{config.DEFAULT_PREFIX}craft <amount> <pack_type>`",
                inline=False
            )
            
            return await ctx.send(embed=embed)
            
        # Process pack type
        pack_type = type.lower()
        
        # Normalize pack types
        if pack_type in ["tech", "tp", "tech_pack", "tech pack"]:
            pack_type = "tech_packs"
            requirements = {"redstone": 50, "lapis": 20, "gold": 10}
            display_name = "Tech Pack"
        elif pack_type in ["utility", "up", "utility_pack", "utility pack"]:
            pack_type = "utility_packs"
            requirements = {"iron": 30, "gold": 15, "diamond": 5}
            display_name = "Utility Pack"
        elif pack_type in ["production", "pp", "production_pack", "production pack"]:
            pack_type = "production_packs"
            requirements = {"coal": 100, "iron": 50, "emerald": 5}
            display_name = "Production Pack"
        else:
            return await ctx.send(f"Invalid pack type. Use `{config.DEFAULT_PREFIX}craft` to see available options.")
            
        # Process amount
        if not amount:
            amount = "1"
            
        # Check if user has started mining
        async with get_session() as session:
            # Get user inventory
            inventory = await session.get(Inventory, ctx.author.id)
            if not inventory:
                embed = EmbedBuilder.error(
                    title="No Inventory Found",
                    description=f"You haven't started mining yet! Use `{config.DEFAULT_PREFIX}start_mine` to begin."
                )
                return await ctx.send(embed=embed)
                
            # Calculate max craftable based on requirements
            max_craftable = float('inf')
            for material, req_amount in requirements.items():
                available = getattr(inventory, material)
                can_craft = available // req_amount
                max_craftable = min(max_craftable, can_craft)
                
            # Parse the requested amount
            if amount.lower() in ['m', 'max', 'all', 'a']:
                craft_amount = max_craftable
            else:
                try:
                    craft_amount = int(amount)
                    craft_amount = min(craft_amount, max_craftable)
                except ValueError:
                    return await ctx.send("Please enter a valid amount!")
            
            # Check if user can craft the requested amount
            if craft_amount <= 0:
                missing_materials = []
                for material, req_amount in requirements.items():
                    available = getattr(inventory, material)
                    if available < req_amount:
                        missing_materials.append(f"{material.capitalize()}: {available}/{req_amount}")
                
                embed = EmbedBuilder.error(
                    title="Cannot Craft",
                    description=f"You don't have enough materials to craft {display_name}!"
                )
                
                embed.add_field(name="Missing Materials", value="\n".join(missing_materials), inline=False)
                
                return await ctx.send(embed=embed)
                
            # Process the crafting
            for material, req_amount in requirements.items():
                setattr(inventory, material, getattr(inventory, material) - req_amount * craft_amount)
                
            # Add the crafted packs
            setattr(inventory, pack_type, getattr(inventory, pack_type) + craft_amount)
            
            # Commit changes
            await session.commit()
            
            # Create success embed
            embed = EmbedBuilder.success(
                title="Crafting Successful",
                description=f"You crafted {craft_amount} {display_name}(s)!"
            )
            
            # Add updated inventory counts
            embed.add_field(name=f"New {display_name} Count", value=getattr(inventory, pack_type), inline=False)
            
            # Add remaining materials
            embed.add_field(name="Remaining Materials", value="\u200b", inline=False)
            for material in requirements.keys():
                embed.add_field(name=material.capitalize(), value=getattr(inventory, material), inline=True)
                
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="upgrade")
    @app_commands.describe(
        miner="The miner to upgrade",
        upgrade_id="The upgrade to buy",
        amount="The amount to buy - does not support `max` or `all` must be a number"
    )
    async def upgrade(self, ctx, miner: str, upgrade_id: str = None, amount: str = None):
        """Upgrade your mining units"""
        # Simple placeholder for now
        embed = EmbedBuilder.info(
            title="Mining Upgrades",
            description="This feature is coming soon!"
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MiningCommands(bot))
