import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import config
from utils.cooldowns import cooldown
from utils.embeds import EmbedBuilder
from utils.economy import EconomyManager
from utils.helpers import parse_amount, SlotMachine, RockPaperScissors
from database.models import User, GameStats
from database.database import get_session
from assets.icons import get_slot_icon, CARD_SUITS, CARD_VALUES

class GamblingCommands(commands.Cog):
    """Commands related to gambling games and betting"""
    
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager(bot)
        self.games_in_progress = {}
    
    #
    # UTILITY METHODS
    #
    
    async def update_game_stats(self, user_id, game_name, bet_amount, won):
        """Update game statistics for a user"""
        async with get_session() as session:
            # Get or create game stats
            stats = await session.get(GameStats, (user_id, game_name))
            if not stats:
                stats = GameStats(
                    user_id=user_id,
                    game_name=game_name,
                    games_played=0,
                    games_won=0,
                    total_bet=0,
                    total_won=0,
                    highest_win=0
                )
                session.add(stats)
            
            # Update stats
            stats.games_played += 1
            stats.total_bet += bet_amount
            
            if won:
                stats.games_won += 1
                stats.total_won += bet_amount
                if bet_amount > stats.highest_win:
                    stats.highest_win = bet_amount
            
            # Also update user's games_played count
            user = await session.get(User, user_id)
            if user:
                user.games_played += 1
                
            await session.commit()
    
    def is_valid_bet(self, cash, bet_amount):
        """Check if a bet amount is valid"""
        if bet_amount < config.MIN_BET:
            return False, f"Minimum bet is ${config.MIN_BET:,}."
        if bet_amount > config.MAX_BET:
            return False, f"Maximum bet is ${config.MAX_BET:,}."
        if bet_amount > cash:
            return False, f"You don't have enough cash! You only have ${cash:,}."
        return True, None
    
    async def process_bet_result(self, ctx, bet_amount, game_name, won, win_amount=None, multiplier=None):
        """Process the result of a bet and send appropriate message"""
        user_id = ctx.author.id
        
        # Calculate win amount if not provided
        if win_amount is None:
            if multiplier is None:
                multiplier = 2  # Default 1:1 payout
            win_amount = bet_amount * multiplier
        
        # Process economy transaction
        if won:
            new_balance = await self.economy.add_cash(user_id, win_amount, f"{game_name} win")
            
            # Create win embed
            embed = EmbedBuilder.success(
                title=f"{game_name} Win!",
                description=f"Congratulations! You won ${win_amount:,}!"
            )
            
            if multiplier:
                embed.add_field(name="Multiplier", value=f"{multiplier}x", inline=True)
                
            embed.add_field(name="New Balance", value=f"${new_balance:,}", inline=True)
            
        else:
            new_balance = await self.economy.remove_cash(user_id, bet_amount, f"{game_name} loss")
            
            # Create loss embed
            embed = EmbedBuilder.error(
                title=f"{game_name} Loss",
                description=f"Sorry! You lost ${bet_amount:,}."
            )
            
            embed.add_field(name="New Balance", value=f"${new_balance:,}", inline=True)
        
        # Update game stats
        await self.update_game_stats(user_id, game_name.lower(), bet_amount, won)
        
        # Send result message
        await ctx.send(embed=embed)
        
        return new_balance
    
    #
    # GAMBLING GAMES
    #
    
    @commands.hybrid_command(name="coinflip", aliases=["coin", "flip", "cf"])
    @app_commands.describe(bet="Amount to bet", choice="Heads or Tails")
    async def coinflip(self, ctx, bet: str, choice: str = None):
        """Flip a coin and bet on the outcome!"""
        # Get user's cash
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
        
        # Parse bet amount
        bet_amount = parse_amount(bet, user.cash)
        if not bet_amount:
            return await ctx.send("Please enter a valid bet amount!")
            
        # Validate bet
        valid, message = self.is_valid_bet(user.cash, bet_amount)
        if not valid:
            return await ctx.send(message)
        
        # Normalize choice
        if choice:
            choice = choice.lower()
            if choice not in ["heads", "tails", "h", "t"]:
                return await ctx.send("Please choose either 'heads' or 'tails'!")
            if choice in ["h", "heads"]:
                choice = "heads"
            else:
                choice = "tails"
        else:
            # If no choice provided, randomly select one
            choice = random.choice(["heads", "tails"])
            await ctx.send(f"No choice provided. I'll choose {choice.capitalize()} for you!")
        
        # Send initial message
        message = await ctx.send("Flipping coin...")
        
        # Add suspense
        await asyncio.sleep(1.5)
        
        # Determine result
        result = random.choice(["heads", "tails"])
        won = result == choice
        
        # Create result embed
        if won:
            embed = EmbedBuilder.success(
                title="Coin Flip Result",
                description=f"The coin landed on **{result.capitalize()}**!\nYou chose **{choice.capitalize()}** and won!"
            )
        else:
            embed = EmbedBuilder.error(
                title="Coin Flip Result",
                description=f"The coin landed on **{result.capitalize()}**!\nYou chose **{choice.capitalize()}** and lost!"
            )
        
        # Add coin emoji
        embed.add_field(name="Result", value="🪙 " + result.capitalize(), inline=True)
        embed.add_field(name="Your Choice", value="🪙 " + choice.capitalize(), inline=True)
        
        # Update the message
        await message.edit(content=None, embed=embed)
        
        # Process bet result
        await self.process_bet_result(ctx, bet_amount, "Coinflip", won)
    
    @commands.hybrid_command(name="slots", aliases=["slot", "s"])
    @app_commands.describe(bet="Amount to bet")
    async def slots(self, ctx, bet: str):
        """Try your luck with the slot machine!"""
        # Get user's cash
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
        
        # Parse bet amount
        bet_amount = parse_amount(bet, user.cash)
        if not bet_amount:
            return await ctx.send("Please enter a valid bet amount!")
            
        # Validate bet
        valid, message = self.is_valid_bet(user.cash, bet_amount)
        if not valid:
            return await ctx.send(message)
        
        # Send initial message
        message = await ctx.send("🎰 Spinning the slots...")
        
        # Add suspense
        await asyncio.sleep(1.5)
        
        # Spin the slots
        result = SlotMachine.spin()
        
        # Check if won
        won = result["multiplier"] > 0
        
        # Create result embed
        if won:
            embed = EmbedBuilder.success(
                title="Slot Machine Results",
                description=f"**{result['display']}**\nYou won with a {result['multiplier']}x multiplier!"
            )
        else:
            embed = EmbedBuilder.error(
                title="Slot Machine Results",
                description=f"**{result['display']}**\nYou lost! Better luck next time."
            )
        
        # Add bet information
        embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
        
        if won:
            win_amount = bet_amount * result["multiplier"]
            embed.add_field(name="Won", value=f"${win_amount:,}", inline=True)
        
        # Update the message
        await message.edit(content=None, embed=embed)
        
        # Process bet result
        await self.process_bet_result(
            ctx, bet_amount, "Slots", won, 
            multiplier=result["multiplier"] if won else None
        )
    
    @commands.hybrid_command(name="dice", aliases=["roll", "rolldice"])
    @app_commands.describe(bet="Amount to bet", choice="Number to bet on (1-6)")
    async def dice(self, ctx, bet: str, choice: int = None):
        """Roll a die and bet on the outcome!"""
        # Get user's cash
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
        
        # Parse bet amount
        bet_amount = parse_amount(bet, user.cash)
        if not bet_amount:
            return await ctx.send("Please enter a valid bet amount!")
            
        # Validate bet
        valid, message = self.is_valid_bet(user.cash, bet_amount)
        if not valid:
            return await ctx.send(message)
        
        # Validate choice
        if choice is not None and (choice < 1 or choice > 6):
            return await ctx.send("Please choose a number between 1 and 6!")
        
        # If no choice, randomly select one
        if choice is None:
            choice = random.randint(1, 6)
            await ctx.send(f"No choice provided. I'll choose {choice} for you!")
        
        # Send initial message
        message = await ctx.send("🎲 Rolling the die...")
        
        # Add suspense
        await asyncio.sleep(1.5)
        
        # Roll the die
        result = random.randint(1, 6)
        won = result == choice
        
        # Get the die emoji
        die_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        result_emoji = die_emojis[result-1]
        
        # Create result embed
        if won:
            embed = EmbedBuilder.success(
                title="Dice Roll Result",
                description=f"The die landed on **{result}** {result_emoji}!\nYou chose **{choice}** and won!"
            )
            # Higher payout since it's 1/6 chance
            multiplier = 5
            embed.add_field(name="Multiplier", value=f"{multiplier}x", inline=True)
        else:
            embed = EmbedBuilder.error(
                title="Dice Roll Result",
                description=f"The die landed on **{result}** {result_emoji}!\nYou chose **{choice}** and lost!"
            )
            multiplier = 0
        
        # Add bet information
        embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
        
        # Update the message
        await message.edit(content=None, embed=embed)
        
        # Process bet result
        await self.process_bet_result(ctx, bet_amount, "Dice", won, multiplier=multiplier if won else None)
    
    @commands.hybrid_command(name="rps", aliases=["rockpaperscissors"])
    @app_commands.describe(bet="Amount to bet", choice="Rock, Paper, or Scissors")
    async def rps(self, ctx, bet: str, choice: str = None):
        """Play Rock, Paper, Scissors!"""
        # Get user's cash
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
        
        # Parse bet amount
        bet_amount = parse_amount(bet, user.cash)
        if not bet_amount:
            return await ctx.send("Please enter a valid bet amount!")
            
        # Validate bet
        valid, message = self.is_valid_bet(user.cash, bet_amount)
        if not valid:
            return await ctx.send(message)
        
        # Normalize choice
        valid_choices = ["rock", "paper", "scissors", "r", "p", "s"]
        if choice:
            choice = choice.lower()
            if choice not in valid_choices:
                return await ctx.send("Please choose 'rock', 'paper', or 'scissors'!")
            
            # Convert short forms
            if choice == "r":
                choice = "rock"
            elif choice == "p":
                choice = "paper"
            elif choice == "s":
                choice = "scissors"
        else:
            # If no choice provided, randomly select one
            choice = random.choice(["rock", "paper", "scissors"])
            await ctx.send(f"No choice provided. I'll choose {choice} for you!")
        
        # Send initial message
        message = await ctx.send(f"Playing Rock, Paper, Scissors...\nYou chose: {RockPaperScissors.get_choice_emoji(choice)} {choice.capitalize()}")
        
        # Add suspense
        await asyncio.sleep(1.5)
        
        # Bot's choice
        bot_choice = random.choice(["rock", "paper", "scissors"])
        
        # Determine winner
        result = RockPaperScissors.determine_winner(choice, bot_choice)
        
        # Create result embed
        if result == "player":
            embed = EmbedBuilder.success(
                title="Rock, Paper, Scissors Result",
                description=f"**You win!**\nYou chose **{choice}** {RockPaperScissors.get_choice_emoji(choice)}\nBot chose **{bot_choice}** {RockPaperScissors.get_choice_emoji(bot_choice)}"
            )
            won = True
        elif result == "bot":
            embed = EmbedBuilder.error(
                title="Rock, Paper, Scissors Result",
                description=f"**You lose!**\nYou chose **{choice}** {RockPaperScissors.get_choice_emoji(choice)}\nBot chose **{bot_choice}** {RockPaperScissors.get_choice_emoji(bot_choice)}"
            )
            won = False
        else:  # tie
            embed = EmbedBuilder.info(
                title="Rock, Paper, Scissors Result",
                description=f"**It's a tie!**\nYou both chose **{choice}** {RockPaperScissors.get_choice_emoji(choice)}"
            )
            # In case of tie, return the bet amount
            await ctx.send("It's a tie! Your bet has been returned.")
            return
        
        # Add bet information
        embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
        
        # Update the message
        await message.edit(content=None, embed=embed)
        
        # Process bet result
        await self.process_bet_result(ctx, bet_amount, "RPS", won)
    
    @commands.hybrid_command(name="blackjack", aliases=["bj", "21"])
    @app_commands.describe(bet="Amount to bet")
    async def blackjack(self, ctx, bet: str):
        """Play a game of Blackjack against the dealer!"""
        # Check if already in a game
        if ctx.author.id in self.games_in_progress:
            return await ctx.send("You are already in a game! Finish it before starting a new one.")
        
        # Get user's cash
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
        
        # Parse bet amount
        bet_amount = parse_amount(bet, user.cash)
        if not bet_amount:
            return await ctx.send("Please enter a valid bet amount!")
            
        # Validate bet
        valid, message = self.is_valid_bet(user.cash, bet_amount)
        if not valid:
            return await ctx.send(message)
        
        # Mark user as in game
        self.games_in_progress[ctx.author.id] = "blackjack"
        
        # Create a deck
        deck = []
        for suit in CARD_SUITS:
            for value in CARD_VALUES:
                deck.append({"suit": suit, "value": value})
        random.shuffle(deck)
        
        # Deal initial cards
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        # Calculate hand values
        def calculate_hand_value(hand):
            value = 0
            aces = 0
            
            for card in hand:
                if card["value"] in ["J", "Q", "K"]:
                    value += 10
                elif card["value"] == "A":
                    aces += 1
                    value += 11
                else:
                    value += int(card["value"])
            
            # Adjust for aces
            while value > 21 and aces > 0:
                value -= 10
                aces -= 1
                
            return value
        
        # Format cards for display
        def format_card(card, hidden=False):
            if hidden:
                return "🂠"
                
            value = card["value"]
            suit = card["suit"]
            
            # Get emoji for card
            if suit == "♥️":
                color = "red"
            elif suit == "♦️":
                color = "red"
            else:
                color = "black"
                
            return f"{value}{suit}"
        
        def format_hand(hand, hide_second=False):
            formatted = []
            for i, card in enumerate(hand):
                if i == 1 and hide_second:
                    formatted.append(format_card(card, hidden=True))
                else:
                    formatted.append(format_card(card))
            return " ".join(formatted)
        
        # Show initial hands
        player_value = calculate_hand_value(player_hand)
        dealer_value = calculate_hand_value([dealer_hand[0]])  # Only count visible card
        
        # Create initial embed
        embed = EmbedBuilder.info(
            title="Blackjack",
            description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand, hide_second=True)} (Showing: {dealer_value})"
        )
        
        embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
        embed.add_field(name="Actions", value="Type **hit** or **stand**", inline=True)
        
        game_message = await ctx.send(embed=embed)
        
        # Check for natural blackjack
        if player_value == 21:
            dealer_full_value = calculate_hand_value(dealer_hand)
            if dealer_full_value == 21:
                # Both have blackjack - it's a push (tie)
                embed = EmbedBuilder.info(
                    title="Blackjack - Push!",
                    description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand)} (Value: {dealer_full_value})\n\nBoth you and the dealer have Blackjack! It's a push (tie)."
                )
                await game_message.edit(embed=embed)
                del self.games_in_progress[ctx.author.id]
                return
            else:
                # Player has natural blackjack - pays 3:2
                win_amount = int(bet_amount * 1.5)
                
                embed = EmbedBuilder.success(
                    title="Blackjack - You Win!",
                    description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand)} (Value: {dealer_full_value})\n\nYou got a natural Blackjack! You win ${win_amount:,}!"
                )
                
                await game_message.edit(embed=embed)
                
                # Process win with 1.5x multiplier
                await self.process_bet_result(ctx, bet_amount, "Blackjack", True, multiplier=1.5)
                del self.games_in_progress[ctx.author.id]
                return
        
        # Game loop
        def check(message):
            return (
                message.author == ctx.author and
                message.channel == ctx.channel and
                message.content.lower() in ["hit", "h", "stand", "s"]
            )
        
        game_over = False
        while not game_over:
            try:
                player_action = await self.bot.wait_for("message", check=check, timeout=60.0)
                
                action = player_action.content.lower()
                
                if action in ["hit", "h"]:
                    # Deal another card to player
                    player_hand.append(deck.pop())
                    player_value = calculate_hand_value(player_hand)
                    
                    # Update embed
                    embed = EmbedBuilder.info(
                        title="Blackjack - Hit",
                        description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand, hide_second=True)} (Showing: {dealer_value})"
                    )
                    
                    embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
                    
                    if player_value > 21:
                        # Player busts
                        embed = EmbedBuilder.error(
                            title="Blackjack - Bust!",
                            description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand)} (Value: {calculate_hand_value(dealer_hand)})\n\nYou bust! Dealer wins."
                        )
                        await game_message.edit(embed=embed)
                        
                        # Process loss
                        await self.process_bet_result(ctx, bet_amount, "Blackjack", False)
                        game_over = True
                    elif player_value == 21:
                        # Player has 21, automatically stand
                        embed.add_field(name="Actions", value="You have 21! Standing automatically.", inline=True)
                        await game_message.edit(embed=embed)
                        
                        # Continue to dealer's turn
                        action = "stand"
                    else:
                        embed.add_field(name="Actions", value="Type **hit** or **stand**", inline=True)
                        await game_message.edit(embed=embed)
                
                if action in ["stand", "s"]:
                    # Dealer's turn
                    dealer_full_value = calculate_hand_value(dealer_hand)
                    
                    # Reveal dealer's hand
                    embed = EmbedBuilder.info(
                        title="Blackjack - Dealer's Turn",
                        description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand)} (Value: {dealer_full_value})"
                    )
                    
                    embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
                    embed.add_field(name="Status", value="Dealer is playing...", inline=True)
                    
                    await game_message.edit(embed=embed)
                    await asyncio.sleep(1)
                    
                    # Dealer hits until 17 or higher
                    while dealer_full_value < 17:
                        dealer_hand.append(deck.pop())
                        dealer_full_value = calculate_hand_value(dealer_hand)
                        
                        # Update embed
                        embed = EmbedBuilder.info(
                            title="Blackjack - Dealer's Turn",
                            description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand)} (Value: {dealer_full_value})"
                        )
                        
                        embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
                        embed.add_field(name="Status", value="Dealer is playing...", inline=True)
                        
                        await game_message.edit(embed=embed)
                        await asyncio.sleep(1)
                    
                    # Determine winner
                    if dealer_full_value > 21:
                        # Dealer busts
                        embed = EmbedBuilder.success(
                            title="Blackjack - You Win!",
                            description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand)} (Value: {dealer_full_value})\n\nDealer busts! You win!"
                        )
                        
                        await game_message.edit(embed=embed)
                        
                        # Process win
                        await self.process_bet_result(ctx, bet_amount, "Blackjack", True)
                    elif dealer_full_value > player_value:
                        # Dealer wins
                        embed = EmbedBuilder.error(
                            title="Blackjack - Dealer Wins",
                            description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand)} (Value: {dealer_full_value})\n\nDealer has higher value. You lose!"
                        )
                        
                        await game_message.edit(embed=embed)
                        
                        # Process loss
                        await self.process_bet_result(ctx, bet_amount, "Blackjack", False)
                    elif dealer_full_value < player_value:
                        # Player wins
                        embed = EmbedBuilder.success(
                            title="Blackjack - You Win!",
                            description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand)} (Value: {dealer_full_value})\n\nYou have higher value. You win!"
                        )
                        
                        await game_message.edit(embed=embed)
                        
                        # Process win
                        await self.process_bet_result(ctx, bet_amount, "Blackjack", True)
                    else:
                        # Push (tie)
                        embed = EmbedBuilder.info(
                            title="Blackjack - Push!",
                            description=f"**Your hand:** {format_hand(player_hand)} (Value: {player_value})\n**Dealer's hand:** {format_hand(dealer_hand)} (Value: {dealer_full_value})\n\nIt's a tie! Your bet is returned."
                        )
                        
                        await game_message.edit(embed=embed)
                        
                        # No win/loss for a push
                        await ctx.send("It's a push (tie)! Your bet has been returned.")
                    
                    game_over = True
                
            except asyncio.TimeoutError:
                # Player took too long
                embed = EmbedBuilder.error(
                    title="Blackjack - Timeout",
                    description="You took too long to respond! Game cancelled."
                )
                await game_message.edit(embed=embed)
                game_over = True
        
        # Remove from active games
        del self.games_in_progress[ctx.author.id]
    
    @commands.hybrid_command(name="roulette", aliases=["r"])
    @app_commands.describe(bet="Amount to bet", choice="Number, color, or bet type")
    async def roulette(self, ctx, bet: str, choice: str):
        """Bet on a roulette wheel spin!"""
        # Get user's cash
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
        
        # Parse bet amount
        bet_amount = parse_amount(bet, user.cash)
        if not bet_amount:
            return await ctx.send("Please enter a valid bet amount!")
            
        # Validate bet
        valid, message = self.is_valid_bet(user.cash, bet_amount)
        if not valid:
            return await ctx.send(message)
        
        # Validate choice
        choice = choice.lower()
        
        # Define valid bets and their payouts
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        
        # Check bet type
        if choice in ["red", "r"]:
            bet_type = "color"
            bet_value = "red"
            payout = 2  # 1:1 payout
        elif choice in ["black", "b"]:
            bet_type = "color"
            bet_value = "black"
            payout = 2  # 1:1 payout
        elif choice in ["green", "g", "0"]:
            bet_type = "green"
            bet_value = 0
            payout = 36  # 35:1 payout
        elif choice in ["even", "e"]:
            bet_type = "even_odd"
            bet_value = "even"
            payout = 2  # 1:1 payout
        elif choice in ["odd", "o"]:
            bet_type = "even_odd"
            bet_value = "odd"
            payout = 2  # 1:1 payout
        elif choice in ["1-18", "low", "l"]:
            bet_type = "half"
            bet_value = "low"
            payout = 2  # 1:1 payout
        elif choice in ["19-36", "high", "h"]:
            bet_type = "half"
            bet_value = "high"
            payout = 2  # 1:1 payout
        elif choice in ["1-12", "first12", "1st12", "first dozen"]:
            bet_type = "dozen"
            bet_value = "first"
            payout = 3  # 2:1 payout
        elif choice in ["13-24", "second12", "2nd12", "second dozen"]:
            bet_type = "dozen"
            bet_value = "second"
            payout = 3  # 2:1 payout
        elif choice in ["25-36", "third12", "3rd12", "third dozen"]:
            bet_type = "dozen"
            bet_value = "third"
            payout = 3  # 2:1 payout
        else:
            # Try to parse as a number
            try:
                number = int(choice)
                if 0 <= number <= 36:
                    bet_type = "number"
                    bet_value = number
                    payout = 36  # 35:1 payout
                else:
                    return await ctx.send("Please choose a valid bet: a number from 0-36, 'red', 'black', 'even', 'odd', '1-18', '19-36', etc.")
            except ValueError:
                return await ctx.send("Please choose a valid bet: a number from 0-36, 'red', 'black', 'even', 'odd', '1-18', '19-36', etc.")
        
        # Send initial message
        message = await ctx.send("🎡 Spinning the roulette wheel...")
        
        # Add suspense
        await asyncio.sleep(2)
        
        # Spin the wheel
        result = random.randint(0, 36)
        
        # Determine result color
        if result == 0:
            result_color = "green"
        elif result in red_numbers:
            result_color = "red"
        else:
            result_color = "black"
            
        # Check if player won
        won = False
        
        if bet_type == "color":
            won = bet_value == result_color
        elif bet_type == "green":
            won = result == 0
        elif bet_type == "number":
            won = bet_value == result
        elif bet_type == "even_odd":
            if result == 0:
                won = False
            elif bet_value == "even":
                won = result % 2 == 0
            else:  # odd
                won = result % 2 == 1
        elif bet_type == "half":
            if result == 0:
                won = False
            elif bet_value == "low":
                won = 1 <= result <= 18
            else:  # high
                won = 19 <= result <= 36
        elif bet_type == "dozen":
            if result == 0:
                won = False
            elif bet_value == "first":
                won = 1 <= result <= 12
            elif bet_value == "second":
                won = 13 <= result <= 24
            else:  # third
                won = 25 <= result <= 36
        
        # Format result color for display
        if result_color == "red":
            result_display = f"🔴 {result}"
        elif result_color == "black":
            result_display = f"⚫ {result}"
        else:  # green
            result_display = f"🟢 {result}"
            
        # Create result embed
        if won:
            win_amount = bet_amount * payout - bet_amount
            embed = EmbedBuilder.success(
                title="Roulette Win!",
                description=f"The ball landed on **{result_display}**!\nYou bet on **{choice}** and won ${win_amount:,}!"
            )
        else:
            embed = EmbedBuilder.error(
                title="Roulette Loss",
                description=f"The ball landed on **{result_display}**!\nYou bet on **{choice}** and lost ${bet_amount:,}."
            )
        
        # Add bet information
        embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
        
        if won:
            embed.add_field(name="Payout", value=f"{payout}:1", inline=True)
            embed.add_field(name="Won", value=f"${win_amount:,}", inline=True)
        
        # Update the message
        await message.edit(content=None, embed=embed)
        
        # Process bet result
        if won:
            await self.process_bet_result(ctx, bet_amount, "Roulette", True, multiplier=payout-1)
        else:
            await self.process_bet_result(ctx, bet_amount, "Roulette", False)
    
    @commands.hybrid_command(name="highlow", aliases=["hl", "hilo"])
    @app_commands.describe(bet="Amount to bet", choice="Higher, Lower, or Same")
    async def highlow(self, ctx, bet: str, choice: str):
        """Guess if the next card will be higher, lower, or the same!"""
        # Get user's cash
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
        
        # Parse bet amount
        bet_amount = parse_amount(bet, user.cash)
        if not bet_amount:
            return await ctx.send("Please enter a valid bet amount!")
            
        # Validate bet
        valid, message = self.is_valid_bet(user.cash, bet_amount)
        if not valid:
            return await ctx.send(message)
        
        # Validate choice
        choice = choice.lower()
        valid_choices = ["higher", "high", "h", "lower", "low", "l", "same", "s"]
        
        if choice not in valid_choices:
            return await ctx.send("Please choose 'higher', 'lower', or 'same'!")
            
        # Normalize choice
        if choice in ["higher", "high", "h"]:
            choice = "higher"
        elif choice in ["lower", "low", "l"]:
            choice = "lower"
        else:
            choice = "same"
        
        # Create a deck
        card_values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        value_map = {card: idx for idx, card in enumerate(card_values)}
        
        # Deal initial card
        first_card = {"value": random.choice(card_values), "suit": random.choice(CARD_SUITS)}
        
        # Send initial message
        embed = EmbedBuilder.info(
            title="High-Low Game",
            description=f"Your card is: **{first_card['value']}{first_card['suit']}**\nWill the next card be **higher**, **lower**, or the **same**?"
        )
        
        embed.add_field(name="Your Choice", value=choice.capitalize(), inline=True)
        embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
        
        message = await ctx.send(embed=embed)
        
        # Add suspense
        await asyncio.sleep(1.5)
        
        # Deal second card
        second_card = {"value": random.choice(card_values), "suit": random.choice(CARD_SUITS)}
        
        # Determine result
        first_value = value_map[first_card["value"]]
        second_value = value_map[second_card["value"]]
        
        if first_value < second_value:
            result = "higher"
        elif first_value > second_value:
            result = "lower"
        else:
            result = "same"
            
        won = choice == result
        
        # Different payout for "same" bet since it's less likely
        payout = 12 if choice == "same" else 2
        
        # Create result embed
        if won:
            win_amount = bet_amount * (payout - 1)
            embed = EmbedBuilder.success(
                title="High-Low Win!",
                description=f"First card: **{first_card['value']}{first_card['suit']}**\nSecond card: **{second_card['value']}{second_card['suit']}**\n\nThe second card was **{result}**! You win ${win_amount:,}!"
            )
        else:
            embed = EmbedBuilder.error(
                title="High-Low Loss",
                description=f"First card: **{first_card['value']}{first_card['suit']}**\nSecond card: **{second_card['value']}{second_card['suit']}**\n\nThe second card was **{result}**! You lose ${bet_amount:,}."
            )
        
        # Add bet information
        embed.add_field(name="Your Choice", value=choice.capitalize(), inline=True)
        embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
        
        if won:
            embed.add_field(name="Payout", value=f"{payout}:1", inline=True)
        
        # Update the message
        await message.edit(embed=embed)
        
        # Process bet result
        if won:
            await self.process_bet_result(ctx, bet_amount, "HighLow", True, multiplier=payout-1)
        else:
            await self.process_bet_result(ctx, bet_amount, "HighLow", False)
    
    @commands.hybrid_command(name="connect4", aliases=["c4"])
    @app_commands.describe(opponent="The opponent to play against", bet="Amount to bet")
    async def connect4(self, ctx, opponent: discord.Member, bet: str = "0"):
        """Play Connect 4 against another user with an optional bet!"""
        # Check if already in a game
        if ctx.author.id in self.games_in_progress:
            return await ctx.send("You are already in a game! Finish it before starting a new one.")
            
        # Validate opponent
        if opponent.bot:
            return await ctx.send("You can't play against a bot!")
            
        if opponent.id == ctx.author.id:
            return await ctx.send("You can't play against yourself!")
            
        if opponent.id in self.games_in_progress:
            return await ctx.send(f"{opponent.display_name} is already in a game!")
        
        # Get user cash
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
                
            opponent_user = await session.get(User, opponent.id)
            if not opponent_user:
                opponent_user = await self.economy.get_user(opponent.id)
        
        # Parse bet amount
        bet_amount = parse_amount(bet, min(user.cash, opponent_user.cash))
        if bet_amount is None:
            bet_amount = 0
            
        # Validate bet if not zero
        if bet_amount > 0:
            valid, message = self.is_valid_bet(user.cash, bet_amount)
            if not valid:
                return await ctx.send(message)
                
            valid, message = self.is_valid_bet(opponent_user.cash, bet_amount)
            if not valid:
                return await ctx.send(f"{opponent.display_name} {message[4:]}")  # Remove "You " from the message
        
        # Send challenge
        if bet_amount > 0:
            embed = EmbedBuilder.info(
                title="Connect 4 Challenge",
                description=f"{opponent.mention}, {ctx.author.display_name} has challenged you to a game of Connect 4 with a bet of ${bet_amount:,}!\nDo you accept the challenge?"
            )
        else:
            embed = EmbedBuilder.info(
                title="Connect 4 Challenge",
                description=f"{opponent.mention}, {ctx.author.display_name} has challenged you to a friendly game of Connect 4!\nDo you accept the challenge?"
            )
            
        challenge_message = await ctx.send(embed=embed)
        
        # Add reaction buttons
        await challenge_message.add_reaction("✅")  # Accept
        await challenge_message.add_reaction("❌")  # Decline
        
        # Wait for response
        def check(reaction, user):
            return (
                user.id == opponent.id and
                reaction.message.id == challenge_message.id and
                str(reaction.emoji) in ["✅", "❌"]
            )
            
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await challenge_message.edit(
                    embed=EmbedBuilder.error(
                        title="Challenge Declined",
                        description=f"{opponent.display_name} has declined the Connect 4 challenge."
                    )
                )
                return
                
            # Challenge accepted, start the game
            await challenge_message.edit(
                embed=EmbedBuilder.success(
                    title="Challenge Accepted",
                    description=f"Setting up Connect 4 game between {ctx.author.display_name} and {opponent.display_name}..."
                )
            )
            
            # Mark players as in game
            self.games_in_progress[ctx.author.id] = "connect4"
            self.games_in_progress[opponent.id] = "connect4"
            
            # Initialize the game
            board = [[" " for _ in range(7)] for _ in range(6)]
            players = [ctx.author, opponent]
            symbols = ["🔴", "🟡"]
            current_player = 0
            
            # Format board for display
            def format_board():
                display = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣\n"
                for row in board:
                    for cell in row:
                        if cell == " ":
                            display += "⚪"
                        else:
                            display += cell
                    display += "\n"
                return display
            
            # Check for win
            def check_win(symbol):
                # Check horizontal
                for row in range(6):
                    for col in range(4):
                        if all(board[row][col+i] == symbol for i in range(4)):
                            return True
                
                # Check vertical
                for row in range(3):
                    for col in range(7):
                        if all(board[row+i][col] == symbol for i in range(4)):
                            return True
                
                # Check diagonal (down-right)
                for row in range(3):
                    for col in range(4):
                        if all(board[row+i][col+i] == symbol for i in range(4)):
                            return True
                
                # Check diagonal (up-right)
                for row in range(3, 6):
                    for col in range(4):
                        if all(board[row-i][col+i] == symbol for i in range(4)):
                            return True
                
                return False
            
            # Check if board is full
            def is_board_full():
                return all(cell != " " for row in board for cell in row)
            
            # Make a move
            def make_move(column, symbol):
                # Convert to 0-indexed
                column = column - 1
                
                # Check if valid column
                if column < 0 or column > 6:
                    return False
                
                # Check if column is full
                if board[0][column] != " ":
                    return False
                
                # Find the first empty cell from bottom
                for row in range(5, -1, -1):
                    if board[row][column] == " ":
                        board[row][column] = symbol
                        return True
                
                return False
            
            # Create game embed
            def create_game_embed():
                if bet_amount > 0:
                    description = f"{players[current_player].mention}'s turn ({symbols[current_player]})\n\n{format_board()}\n\nBet: ${bet_amount:,}"
                else:
                    description = f"{players[current_player].mention}'s turn ({symbols[current_player]})\n\n{format_board()}"
                    
                embed = EmbedBuilder.info(
                    title="Connect 4",
                    description=description
                )
                
                embed.add_field(name="How to Play", value="Type a number 1-7 to drop your piece in that column.", inline=False)
                
                return embed
            
            # Send initial game board
            game_message = await ctx.send(embed=create_game_embed())
            
            # Game loop
            game_over = False
            while not game_over:
                # Wait for player's move
                def move_check(message):
                    return (
                        message.author.id == players[current_player].id and
                        message.channel == ctx.channel and
                        message.content.isdigit() and
                        1 <= int(message.content) <= 7
                    )
                
                try:
                    move_message = await self.bot.wait_for("message", check=move_check, timeout=60.0)
                    
                    # Parse move
                    column = int(move_message.content)
                    
                    # Make move
                    if make_move(column, symbols[current_player]):
                        # Check for win
                        if check_win(symbols[current_player]):
                            # Create win embed
                            win_embed = EmbedBuilder.success(
                                title=f"{players[current_player].display_name} Wins!",
                                description=f"{format_board()}\n\n{players[current_player].mention} ({symbols[current_player]}) has won the game!"
                            )
                            
                            if bet_amount > 0:
                                win_embed.add_field(name="Bet", value=f"${bet_amount:,} has been transferred.", inline=False)
                                
                                # Process bet
                                winner_id = players[current_player].id
                                loser_id = players[1 - current_player].id
                                
                                await self.economy.remove_cash(loser_id, bet_amount, f"Connect4 loss to {winner_id}")
                                await self.economy.add_cash(winner_id, bet_amount, f"Connect4 win against {loser_id}")
                                
                                # Update game stats
                                await self.update_game_stats(winner_id, "Connect4", bet_amount, True)
                                await self.update_game_stats(loser_id, "Connect4", bet_amount, False)
                            
                            await game_message.edit(embed=win_embed)
                            game_over = True
                            
                        # Check for tie
                        elif is_board_full():
                            # Create tie embed
                            tie_embed = EmbedBuilder.info(
                                title="Connect 4 - Tie Game!",
                                description=f"{format_board()}\n\nThe game is a tie! Board is full."
                            )
                            
                            if bet_amount > 0:
                                tie_embed.add_field(name="Bet", value=f"${bet_amount:,} has been returned to both players.", inline=False)
                            
                            await game_message.edit(embed=tie_embed)
                            game_over = True
                            
                        else:
                            # Switch players
                            current_player = 1 - current_player
                            
                            # Update game board
                            await game_message.edit(embed=create_game_embed())
                    else:
                        # Invalid move
                        await ctx.send(f"{players[current_player].mention} That column is full! Choose another column.", delete_after=5)
                
                except asyncio.TimeoutError:
                    # Player took too long
                    timeout_embed = EmbedBuilder.error(
                        title="Connect 4 - Timeout",
                        description=f"{players[current_player].mention} took too long to make a move! Game cancelled."
                    )
                    
                    if bet_amount > 0:
                        timeout_embed.add_field(name="Bet", value=f"${bet_amount:,} has been returned to both players.", inline=False)
                    
                    await game_message.edit(embed=timeout_embed)
                    game_over = True
            
            # Remove players from active games
            del self.games_in_progress[ctx.author.id]
            del self.games_in_progress[opponent.id]
            
        except asyncio.TimeoutError:
            # Challenge timed out
            await challenge_message.edit(
                embed=EmbedBuilder.error(
                    title="Challenge Expired",
                    description=f"{opponent.display_name} did not respond to the Connect 4 challenge in time."
                )
            )
    
    @commands.hybrid_command(name="lotto", aliases=["lottery", "ticket", "tickets"])
    @app_commands.describe(tickets_to_buy="The number of tickets to buy. Use 'm' to buy max")
    async def lotto(self, ctx, tickets_to_buy: str = None):
        """Participate in the weekly lottery!"""
        TICKET_PRICE = 1000
        MAX_TICKETS = 1000
        
        if not tickets_to_buy:
            # Show lottery info
            async with get_session() as session:
                user = await session.get(User, ctx.author.id)
                if not user:
                    user = await self.economy.get_user(ctx.author.id)
                    
                # Get ticket count for user
                # This would come from a proper lottery system
                tickets_owned = getattr(user, "lottery_tickets", 0)
                
                # Get total pot and other lottery stats
                # This would come from a proper lottery system
                total_pot = 5000000  # Example placeholder
                total_tickets = 1000  # Example placeholder
                next_draw = "Saturday at 11:00am UTC"  # Example placeholder
                
                embed = EmbedBuilder.info(
                    title="Weekly Lottery",
                    description="Buy tickets for a chance to win big in the weekly lottery!"
                )
                
                embed.add_field(name="Your Tickets", value=str(tickets_owned), inline=True)
                embed.add_field(name="Total Pot", value=f"${total_pot:,}", inline=True)
                embed.add_field(name="Total Tickets", value=str(total_tickets), inline=True)
                embed.add_field(name="Ticket Price", value=f"${TICKET_PRICE:,}", inline=True)
                embed.add_field(name="Max Tickets", value=str(MAX_TICKETS), inline=True)
                embed.add_field(name="Next Draw", value=next_draw, inline=True)
                embed.add_field(
                    name="How to Play",
                    value=f"Use `{config.DEFAULT_PREFIX}lotto <number>` to buy tickets! Use 'm' to buy the max.",
                    inline=False
                )
                
                return await ctx.send(embed=embed)
        
        # Parse tickets to buy
        async with get_session() as session:
            user = await session.get(User, ctx.author.id)
            if not user:
                user = await self.economy.get_user(ctx.author.id)
                
            # Get current tickets
            tickets_owned = getattr(user, "lottery_tickets", 0)
            
            # Calculate max tickets user can buy
            max_more_tickets = min(MAX_TICKETS - tickets_owned, user.cash // TICKET_PRICE)
            
            # Parse ticket amount
            if tickets_to_buy.lower() in ['m', 'max', 'all', 'a']:
                tickets = max_more_tickets
            else:
                try:
                    tickets = int(tickets_to_buy)
                    tickets = min(tickets, max_more_tickets)
                except ValueError:
                    return await ctx.send("Please enter a valid number of tickets!")
            
            if tickets <= 0:
                if tickets_owned >= MAX_TICKETS:
                    return await ctx.send(f"You already have the maximum of {MAX_TICKETS} tickets!")
                elif user.cash < TICKET_PRICE:
                    return await ctx.send(f"You don't have enough money! Each ticket costs ${TICKET_PRICE:,}.")
                else:
                    return await ctx.send("You need to buy at least 1 ticket!")
            
            # Calculate total cost
            total_cost = tickets * TICKET_PRICE
            
            # Update user's cash and tickets
            user.cash -= total_cost
            
            # In a real system, you'd update the lottery tickets in a separate table
            # For this example, we'll add it as a property to the user
            user.lottery_tickets = tickets_owned + tickets
            
            await session.commit()
            
            # Create success embed
            embed = EmbedBuilder.success(
                title="Lottery Tickets Purchased",
                description=f"You bought {tickets} lottery ticket{'s' if tickets != 1 else ''}!"
            )
            
            embed.add_field(name="Cost", value=f"${total_cost:,}", inline=True)
            embed.add_field(name="Your Tickets", value=str(user.lottery_tickets), inline=True)
            embed.add_field(name="New Balance", value=f"${user.cash:,}", inline=True)
            
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GamblingCommands(bot))
