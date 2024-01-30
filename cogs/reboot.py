'''
Command to sanitize trackers out of URL parameters by stripping params
'''
import os
import subprocess
import sys

from discord.ext import commands
from discord.errors import Forbidden

MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))


class Reboot(commands.Cog):
    '''Cog to reboot this thing when it needs to'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_role(MOD_ROLE_ID)
    async def reboot(self, ctx: commands.Context):
        '''
        Usage: !reboot
        Reboot bot
        '''
        await ctx.message.delete()
        os.execv(sys.executable, ['python'] + sys.argv)

    @commands.command()
    @commands.has_role(MOD_ROLE_ID)
    async def update(self, ctx: commands.Context):
        '''
        Usage: !update
               !update pull-frozen    # pull dependencies from requirements.txt
               !update pull-unfrozen  # pull dependencies from requirements-unfrozen.txt
        git pull, then bot reboot
        '''
        try:
            await ctx.message.delete()
        except Forbidden:
            pass
        subprocess.run('git pull origin bot-lite', shell=True, check=True)
        if 'pull-unfrozen' in ctx.message.content:
            subprocess.run('pip3 install -U --no-cache-dir -r requirements.txt',
                           shell=True, check=True)
        if 'pull-frozen' in ctx.message.content:
            subprocess.run('pip3 install -U --no-cache-dir -r requirements.txt',
                           shell=True, check=True)
        os.execv(sys.executable, ['python'] + sys.argv)


async def setup(client):
    '''setup'''
    await client.add_cog(Reboot(client))
