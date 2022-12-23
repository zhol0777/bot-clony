'''
Command to sanitize trackers out of URL parameters by stripping params
'''
import os
import subprocess
import sys

from discord.ext import commands
from discord.errors import Forbidden

MOD_ROLE = os.getenv('MOD_ROLE')

BOOTSTRAP_REMINDER = '''
Please start up the task loops by running
`!unejectloopstart` and `!startreminderloop` and `!startpurgeloop`
within the server after reboot/restart have completed
'''


class Reboot(commands.Cog):
    '''Cog to reboot this thing when it needs to'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_role(MOD_ROLE)
    async def reboot(self, ctx: commands.Context):
        '''
        Usage: !reboot
        Reboot bot
        '''
        dm_channel = await ctx.message.author.create_dm()
        await dm_channel.send(BOOTSTRAP_REMINDER)
        await ctx.message.delete()
        os.execv(sys.executable, ['python'] + sys.argv)

    @commands.command()
    @commands.has_role(MOD_ROLE)
    async def update(self, ctx: commands.Context):
        '''
        Usage: !update
        git pull, then bot reboot
        '''
        dm_channel = await ctx.message.author.create_dm()
        await dm_channel.send(BOOTSTRAP_REMINDER)
        try:
            await ctx.message.delete()
        except Forbidden:
            pass
        subprocess.run('git pull origin bot-lite', shell=True, check=True)
        os.execv(sys.executable, ['python'] + sys.argv)


async def setup(client):
    '''setup'''
    await client.add_cog(Reboot(client))
