import os
import asyncio
import logging
from bot import setup_bot

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get token from environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    logging.error("No Discord bot token found. Set the DISCORD_BOT_TOKEN environment variable.")
    exit(1)

async def main():
    """Main entry point for the bot"""
    bot = await setup_bot()
    
    try:
        await bot.start(TOKEN)
    except asyncio.CancelledError:
        logging.warning("Bot operation was cancelled.")
        await bot.close()
    except KeyboardInterrupt:
        logging.info("Bot shutdown requested by user.")
        await bot.close()
    finally:
        logging.info("Bot has been shut down.")

if __name__ == "__main__":
    # Start the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
