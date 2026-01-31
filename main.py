'''
main.py
Run this to run bot-clony
'''
import asyncio
import logging
import os
import sys

import discord
import dotenv
from discord.ext import commands

import db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

dotenv.load_dotenv()

db.create_tables()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')

bot = commands.Bot(command_prefix=COMMAND_PREFIX,  # ty: ignore[invalid-argument-type]
                   intents=discord.Intents.all())
bot.remove_command('help')


async def load_extensions():
    '''load extensions in'''
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and '__init__' not in filename:
            await bot.load_extension(f"cogs.{filename[:-3]}")


asyncio.run(load_extensions())
if not DISCORD_TOKEN:
    log.error("DISCORD_TOKEN os env not found, exiting")
    sys.exit(1)
bot.run(DISCORD_TOKEN)  # ty: ignore[invalid-argument-type]
