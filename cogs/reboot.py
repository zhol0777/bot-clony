'''
Command to sanitize trackers out of URL parameters by stripping params
'''
import os
import subprocess
import sys

from discord.ext import commands
from discord.errors import Forbidden

BANNERLORD_ROLE_ID = int(os.getenv('BANNERLORD_ROLE_ID', '0'))


class Reboot(commands.Cog):
    '''Cog to reboot this thing when it needs to'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_role(BANNERLORD_ROLE_ID)
    async def update(self, ctx: commands.Context):
        '''
        Usage: !update
        git pull, then bot reboot
        '''
        await ctx.message.channel.send('ok updating...')
        try:
            await ctx.message.delete()
        except Forbidden:
            pass
        subprocess.run('git pull origin granmark', shell=True, check=True)
        os.execv(sys.executable, ['python'] + sys.argv)


async def setup(client):
    '''setup'''
    await client.add_cog(Reboot(client))
