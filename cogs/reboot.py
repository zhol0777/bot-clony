'''
Command to sanitize trackers out of URL parameters by stripping params
'''
import os
import subprocess
import sys

from discord.errors import Forbidden
from discord.ext import commands


class Reboot(commands.Cog):
    '''Cog to reboot this thing when it needs to'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def reboot(self, ctx: commands.Context):
        '''
        Usage: !reboot
        Reboot bot
        '''
        await ctx.message.delete()
        os.execv(sys.executable, [sys.executable, *sys.argv])

    @commands.command()
    async def update(self, ctx: commands.Context):
        '''
        Usage: !update
        git pull, then bot reboot
        '''
        try:
            await ctx.message.delete()
        except Forbidden:
            pass
        subprocess.run('git pull origin pasture', shell=True, check=True)
        subprocess.run('uv sync', shell=True, check=True)
        os.execv(sys.executable, [sys.executable, *sys.argv])


async def setup(client):
    '''setup'''
    await client.add_cog(Reboot(client))
