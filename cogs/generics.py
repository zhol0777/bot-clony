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
        '''Posts the new vendors list'''
        reply_message = await util.get_reply_message(ctx, ctx.message)
        await ctx.channel.send('https://mechkeys.me/VENDORS.html',
                               reference=reply_message)

    @commands.command()
    async def notathing(self, ctx):
        '''explanation that we cant have what we want all the time'''
        await ctx.channel.send('the odds that this is a real thing are looking slim')

    @commands.command()
    async def bestgamingswitch(self, ctx):
        '''point out what the best gaming switch is'''
        await ctx.channel.send('the best switch for gaming is a nintendo switch')
        await ctx.message.delete()


async def setup(client):
    '''setup'''
    await client.add_cog(Generics(client))
