'''
Verify phrase and region role phrase
'''
import os

import discord
from discord.ext import commands

VERIFY_CHANNEL_ID = int(os.getenv('VERIFY_CHANNEL_ID', '0'))
REGION_ROLE_CHANNEL_ID = int(os.getenv('REGION_ROLE_CHANNEL_ID', '0'))
VERIFY_PHRASE = os.getenv('VERIFY_PHRASE', None)

COMMAND_TO_ROLE_DICT = {
    "!US": "United States",
    "!CANADA": "Canada",
    "!MEXICO": "Mexico",
    "!SA": "Central/South America",
    "!BREXIT": "United Kingdom",
    "!EU": "Europe",
    "!OCE": "Oceania",
    "!ASIA": "Asia",
    "!SEA": "South East Asia",
    "!ME": "Middle East",
    "!AFRICA": "Africa"
}


class Verify(commands.Cog):
    '''Cog to verify users and assign region roles'''
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id == VERIFY_CHANNEL_ID:
            if VERIFY_PHRASE and message.content == VERIFY_PHRASE:
                if isinstance(message.author, discord.Member):
                    role = discord.utils.get(message.author.guild.roles, name='Verified')
                    if role:
                        await message.author.add_roles(role)
            await message.delete()
        elif message.channel.id == REGION_ROLE_CHANNEL_ID:
            if role_name := COMMAND_TO_ROLE_DICT.get(message.content):
                if isinstance(message.author, discord.Member):
                    role = discord.utils.get(message.author.guild.roles, name=role_name)
                    if role:
                        await message.author.add_roles(role)
            await message.delete()


async def setup(client):
    '''setup'''
    await client.add_cog(Verify(client))
