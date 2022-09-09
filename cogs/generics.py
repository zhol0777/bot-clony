'''
Generic commands that provide simple responses
'''
from discord.ext import commands

import util


class Generics(commands.Cog):
    '''Cog to provide very generic accounts'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def newvendors(self, ctx: commands.Context):
        '''Posts the vendors list'''
        reply_message = await util.get_reply_message(ctx, ctx.message)
        await ctx.channel.send('https://mechkeys.me/VENDORS.html',
                               reference=reply_message)

    @commands.command()
    async def notathing(self, ctx):
        ''''''
        await ctx.channel.send('the odds that this is a real thing are looking slim')


async def setup(client):
    '''setup'''
    await client.add_cog(Generics(client))
