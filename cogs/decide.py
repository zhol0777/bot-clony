'''
Deicde on something for a user who can't help themselves
'''
from random import randint, choice as rand_choice, randrange
import asyncio
import os

from discord.ext import commands


MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))

DISCLAIMER = '''
Inciting this decision implies a legally binding agreement to abide by the
decision that the bot provides for you. Making the choice to ignore this choice
is a sign that this forum is not the proper location for you to request advice.
'''

EXCUSES: list[str] = [
    "Considering thock metrics...",
    "Calculating nylon content...",
    "Passing high school Algebra...",
    "Optimizing clack...",
    "Consulting leading experts...",
    "Deciding on how contrarian to make decision...",
    "Asking a punk...",
    "Making decision perfect if you're a complainer...",
    "Asking someone else...",
    "Crying about it..."
]


class Generics(commands.Cog):
    '''Cog to provide very generic accounts'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def decide(self, ctx: commands.Context, *args):
        """
        Usage: !decide sonnet75 obliterated75 gmmkpro q1 m1
        """
        await ctx.channel.send(DISCLAIMER)
        loading_message = await ctx.channel.send("Calculating decision...")
        for _ in range(0, randint(0, 6)):
            await asyncio.sleep(randint(2, 5))
            await loading_message.edit(content=EXCUSES[randrange(0, len(EXCUSES))])
        await loading_message.edit(content="**BZZZZT DECISION HAS BEEN MADE**\n"
                                   f"{rand_choice(args)}")
