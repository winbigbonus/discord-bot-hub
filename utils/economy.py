import random
import asyncio
import discord
from discord.ext import commands
import config
from database.models import User, Transaction
from database.database import get_session

class EconomyManager:
    """Utility class to handle economic transactions in the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        
    async def get_user(self, user_id):
        """Get or create user in the database"""
        async with get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                # Create new user
                user = User(
                    id=user_id,
                    cash=config.STARTING_CASH,
                    level=1,
                    experience=0
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user
    
    async def add_cash(self, user_id, amount, reason=None):
        """Add cash to a user's balance"""
        if amount <= 0:
            return False
            
        async with get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                user = await self.get_user(user_id)
                
            user.cash += amount
            
            # Record transaction
            if reason:
                transaction = Transaction(
                    user_id=user_id,
                    amount=amount,
                    type="credit",
                    reason=reason
                )
                session.add(transaction)
                
            await session.commit()
            return user.cash
    
    async def remove_cash(self, user_id, amount, reason=None):
        """Remove cash from a user's balance"""
        if amount <= 0:
            return False
            
        async with get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                user = await self.get_user(user_id)
                
            if user.cash < amount:
                return False
                
            user.cash -= amount
            
            # Record transaction
            if reason:
                transaction = Transaction(
                    user_id=user_id,
                    amount=amount,
                    type="debit",
                    reason=reason
                )
                session.add(transaction)
                
            await session.commit()
            return user.cash
    
    async def transfer_cash(self, sender_id, receiver_id, amount, tax_rate=0):
        """Transfer cash between users with optional tax"""
        if amount <= 0:
            return False, "Amount must be positive."
            
        if sender_id == receiver_id:
            return False, "You can't send money to yourself."
            
        async with get_session() as session:
            sender = await session.get(User, sender_id)
            if not sender:
                sender = await self.get_user(sender_id)
                
            receiver = await session.get(User, receiver_id)
            if not receiver:
                receiver = await self.get_user(receiver_id)
                
            if sender.cash < amount:
                return False, "You don't have enough cash."
                
            # Calculate tax
            tax_amount = int(amount * tax_rate)
            final_amount = amount - tax_amount
            
            # Process the transfer
            sender.cash -= amount
            receiver.cash += final_amount
            
            # Record transactions
            sender_transaction = Transaction(
                user_id=sender_id,
                amount=amount,
                type="debit",
                reason=f"Transfer to {receiver_id}"
            )
            receiver_transaction = Transaction(
                user_id=receiver_id,
                amount=final_amount,
                type="credit",
                reason=f"Transfer from {sender_id}"
            )
            
            session.add(sender_transaction)
            session.add(receiver_transaction)
            
            await session.commit()
            
            return True, {
                "sender_balance": sender.cash,
                "receiver_balance": receiver.cash,
                "amount": amount,
                "tax": tax_amount,
                "final_amount": final_amount
            }
    
    async def daily_reward(self, user_id):
        """Give a daily reward to a user"""
        reward = random.randint(config.DAILY_MIN, config.DAILY_MAX)
        
        # Check for multipliers or bonuses
        async with get_session() as session:
            user = await session.get(User, user_id)
            if user and user.cash_multiplier > 1:
                reward = int(reward * user.cash_multiplier)
        
        new_balance = await self.add_cash(user_id, reward, "Daily reward")
        return reward, new_balance
    
    async def weekly_reward(self, user_id):
        """Give a weekly reward to a user"""
        reward = random.randint(config.WEEKLY_MIN, config.WEEKLY_MAX)
        
        # Check for multipliers or bonuses
        async with get_session() as session:
            user = await session.get(User, user_id)
            if user and user.cash_multiplier > 1:
                reward = int(reward * user.cash_multiplier)
        
        new_balance = await self.add_cash(user_id, reward, "Weekly reward")
        return reward, new_balance
    
    async def monthly_reward(self, user_id):
        """Give a monthly reward to a user"""
        reward = random.randint(config.MONTHLY_MIN, config.MONTHLY_MAX)
        
        # Check for multipliers or bonuses
        async with get_session() as session:
            user = await session.get(User, user_id)
            if user and user.cash_multiplier > 1:
                reward = int(reward * user.cash_multiplier)
        
        new_balance = await self.add_cash(user_id, reward, "Monthly reward")
        return reward, new_balance
    
    async def yearly_reward(self, user_id):
        """Give a yearly reward to a user"""
        reward = random.randint(config.YEARLY_MIN, config.YEARLY_MAX)
        
        # Check for multipliers or bonuses
        async with get_session() as session:
            user = await session.get(User, user_id)
            if user and user.cash_multiplier > 1:
                reward = int(reward * user.cash_multiplier)
        
        new_balance = await self.add_cash(user_id, reward, "Yearly reward")
        return reward, new_balance
    
    async def work_reward(self, user_id):
        """Give a work reward to a user"""
        reward = random.randint(config.WORK_MIN, config.WORK_MAX)
        
        # Check for multipliers or bonuses
        async with get_session() as session:
            user = await session.get(User, user_id)
            if user and user.cash_multiplier > 1:
                reward = int(reward * user.cash_multiplier)
        
        new_balance = await self.add_cash(user_id, reward, "Work reward")
        return reward, new_balance
    
    async def overtime_reward(self, user_id):
        """Give an overtime reward to a user"""
        reward = random.randint(config.OVERTIME_MIN, config.OVERTIME_MAX)
        
        # Check for multipliers or bonuses
        async with get_session() as session:
            user = await session.get(User, user_id)
            if user and user.cash_multiplier > 1:
                reward = int(reward * user.cash_multiplier)
        
        new_balance = await self.add_cash(user_id, reward, "Overtime reward")
        return reward, new_balance
