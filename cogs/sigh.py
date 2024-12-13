'''
sigh
'''

import pickle
from pathlib import Path

from discord.ext import commands


class Sigh(commands.Cog):
    '''steal emojis'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def sigh(self, ctx: commands.Context):
        '''
        Usage: !sigh
        '''
        if Path('sigh.pickle').exists():
            with open('sigh.pickle', 'rb') as _file:
                sigh_count = pickle.load(_file)
        else:
            sigh_count = 0
        sigh_count += 1
        with open('sigh.pickle', 'wb') as _file:
            pickle.dump(sigh_count, _file)
        await ctx.channel.send(f"## `{sigh_count} sighs...`")


async def setup(client):
    '''setup'''
    await client.add_cog(Sigh(client))
