import discord
import re
import asyncio
import random
from datetime import datetime, timedelta

def parse_amount(amount_str, max_value):
    """Parse an amount string, supporting 'max'/'all' keywords"""
    if amount_str.lower() in ('max', 'all', 'a', 'm'):
        return max_value
        
    try:
        amount = int(amount_str)
        return min(amount, max_value)
    except ValueError:
        return None

async def get_mentioned_user(ctx, mention_str):
    """Get a user from a mention string or user ID"""
    if not mention_str:
        return None
        
    # Check if it's a mention
    mention_match = re.match(r'<@!?(\d+)>', mention_str)
    if mention_match:
        user_id = int(mention_match.group(1))
    else:
        # Check if it's a user ID
        try:
            user_id = int(mention_str)
        except ValueError:
            return None
    
    # Try to fetch the user
    try:
        return await ctx.bot.fetch_user(user_id)
    except discord.NotFound:
        return None

def format_number(number):
    """Format a number with commas and handle large numbers with suffixes"""
    if number < 1000:
        return str(number)
        
    if number < 1000000:
        return f"{number:,}"
        
    if number < 1000000000:
        return f"{number/1000000:.1f}M"
        
    return f"{number/1000000000:.1f}B"

def get_game_emoji(game_name):
    """Get the emoji for a specific game"""
    emojis = {
        "slots": "🎰",
        "blackjack": "♠️",
        "dice": "🎲",
        "roulette": "🎡",
        "coinflip": "🪙",
        "wheel": "🎪",
        "connect4": "🔢",
        "lottery": "🎟️",
        "mining": "⛏️"
    }
    
    return emojis.get(game_name.lower(), "🎮")

async def create_paginated_embed(ctx, pages, timeout=60):
    """Create a paginated embed with navigation buttons"""
    if not pages:
        return await ctx.send("No pages to display.")
        
    current_page = 0
    
    # Create the initial message
    message = await ctx.send(embed=pages[current_page])
    
    # Add navigation reactions
    navigation = ["⬅️", "➡️", "❌"]
    for emoji in navigation:
        await message.add_reaction(emoji)
        
    def check(reaction, user):
        return (
            reaction.message.id == message.id and
            user.id == ctx.author.id and
            str(reaction.emoji) in navigation
        )
    
    # Listen for reactions
    while True:
        try:
            reaction, user = await ctx.bot.wait_for("reaction_add", timeout=timeout, check=check)
            
            # Remove the user's reaction
            await message.remove_reaction(reaction, user)
            
            # Handle navigation
            if str(reaction.emoji) == "⬅️":
                current_page = (current_page - 1) % len(pages)
                await message.edit(embed=pages[current_page])
                
            elif str(reaction.emoji) == "➡️":
                current_page = (current_page + 1) % len(pages)
                await message.edit(embed=pages[current_page])
                
            elif str(reaction.emoji) == "❌":
                await message.clear_reactions()
                break
                
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break

class RockPaperScissors:
    """Helper class for Rock Paper Scissors game"""
    CHOICES = ["rock", "paper", "scissors"]
    
    @staticmethod
    def determine_winner(player_choice, bot_choice):
        """Determine the winner of a RPS round"""
        if player_choice == bot_choice:
            return "tie"
            
        if (
            (player_choice == "rock" and bot_choice == "scissors") or
            (player_choice == "paper" and bot_choice == "rock") or
            (player_choice == "scissors" and bot_choice == "paper")
        ):
            return "player"
            
        return "bot"
    
    @staticmethod
    def get_choice_emoji(choice):
        """Get the emoji for a RPS choice"""
        emojis = {
            "rock": "🪨",
            "paper": "📄",
            "scissors": "✂️"
        }
        return emojis.get(choice, "❓")

class SlotMachine:
    """Helper class for Slots game"""
    # Define slot symbols and their weights/payouts
    SYMBOLS = {
        "diamond": {"emoji": "💎", "weight": 1, "payout": 10},
        "heart": {"emoji": "❤️", "weight": 3, "payout": 5},
        "lemon": {"emoji": "🍋", "weight": 5, "payout": 3},
        "melon": {"emoji": "🍉", "weight": 5, "payout": 3},
        "seven": {"emoji": "7️⃣", "weight": 2, "payout": 7},
        "horseshoe": {"emoji": "🧲", "weight": 4, "payout": 4}
    }
    
    @staticmethod
    def spin():
        """Spin the slot machine and get results"""
        # Create weighted list of symbols
        weighted_symbols = []
        for symbol, data in SlotMachine.SYMBOLS.items():
            weighted_symbols.extend([symbol] * data["weight"])
            
        # Spin the reels
        results = [random.choice(weighted_symbols) for _ in range(3)]
        
        # Get the symbols' emoji representation
        emojis = [SlotMachine.SYMBOLS[symbol]["emoji"] for symbol in results]
        
        # Calculate win multiplier
        multiplier = 0
        
        # Check for 3 of a kind
        if results[0] == results[1] == results[2]:
            multiplier = SlotMachine.SYMBOLS[results[0]]["payout"]
        # Check for 2 of a kind
        elif results[0] == results[1] or results[1] == results[2] or results[0] == results[2]:
            # Get the symbol that appears more than once
            if results[0] == results[1]:
                matching_symbol = results[0]
            elif results[1] == results[2]:
                matching_symbol = results[1]
            else:
                matching_symbol = results[0]
                
            # Half payout for 2 of a kind
            multiplier = SlotMachine.SYMBOLS[matching_symbol]["payout"] // 2
            
        return {
            "symbols": results,
            "emojis": emojis,
            "multiplier": multiplier,
            "display": " | ".join(emojis)
        }
