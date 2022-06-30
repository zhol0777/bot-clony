'''
main.py
Run this to run bot-clony
'''
import logging
import os

from discord.ext import commands
from dotenv import load_dotenv
import discord

import db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')

bot = commands.Bot(command_prefix=COMMAND_PREFIX,
                   intents=discord.Intents.all())


@bot.event
async def on_ready():
    '''Load in all cogs into bot'''
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and '__init__' not in filename:
            bot.load_extension(f"cogs.{filename[:-3]}")
    log.warning("I am ready.")

db.create_tables()
bot.run(DISCORD_TOKEN)
