'''
Generic commands that provide simple responses
'''
import os

from discord.ext import commands

import util

MOD_ROLE = os.getenv('MOD_ROLE')
HELPER_ROLE = os.getenv('HELPER_ROLE')


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

    @commands.has_any_role(HELPER_ROLE, MOD_ROLE)
    @commands.command(aliases=['say'])
    async def parrot(self, ctx):
        '''parrot a message back'''
        if len(ctx.message.content.split()) <= 1:
            return
        content = ' '.join(ctx.message.content.split()[1:])
        await ctx.message.delete()
        await ctx.message.channel.send(content)


async def setup(client):
    '''setup'''
    await client.add_cog(Generics(client))
