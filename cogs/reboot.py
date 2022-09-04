'''
Command to sanitize trackers out of URL parameters by stripping params
'''
import os
import subprocess
import sys

from discord.ext import commands

MOD_ROLE = os.getenv('MOD_ROLE')


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
        await ctx.channel.send("Rebooting...")
        os.execv(sys.executable, ['python'] + sys.argv)

    @commands.command()
    @commands.has_role(MOD_ROLE)
    async def update(self, ctx: commands.Context):
        '''
        Usage: !update
        git pull, then bot reboot
        '''
        await ctx.channel.send("Updating...")
        subprocess.run('git pull origin main', shell=True, check=True)
        await ctx.channel.send("Rebooting...")
        os.execv(sys.executable, ['python'] + sys.argv)


def setup(client):
    '''setup'''
    client.add_cog(Reboot(client))
