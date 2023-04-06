'''
Generic commands that provide simple responses
'''
import os

from discord.ext import commands
from discord import TextChannel

import util

MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))


class Generics(commands.Cog):
    '''Cog to provide very generic accounts'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def newvendors(self, ctx: commands.Context):
        '''Posts the new vendors list'''
        reply_message = await util.get_reply_message(ctx.message)
        await ctx.channel.send('https://wiki.keyboard.gay/VENDORS.html',
                               reference=reply_message)

    @commands.command()
    async def bestgamingswitch(self, ctx):
        '''point out what the best gaming switch is'''
        await ctx.channel.send('the best switch for gaming is a nintendo switch')
        await ctx.message.delete()

    @commands.has_any_role(HELPER_ROLE_ID, MOD_ROLE_ID)
    @commands.command(aliases=['say'])
    async def parrot(self, ctx):
        '''parrot a message back'''
        reply_message = await util.get_reply_message(ctx.message)
        if len(ctx.message.content.split()) <= 1:
            return
        content = ' '.join(ctx.message.content.split()[1:])
        if ctx.message.reference is not None:
            reply_message = await util.get_reply_message(ctx.message)
            await ctx.message.delete()
            await ctx.message.channel.send(content, reference=reply_message,
                                           mention_author=False)
            return
        await ctx.message.delete()
        await ctx.message.channel.send(content)

    @commands.command()
    async def channeldescription(self, ctx):
        '''print the channel description'''
        if isinstance(ctx.channel, TextChannel):
            await ctx.message.channel.send(ctx.channel.topic)


async def setup(client):
    '''setup'''
    await client.add_cog(Generics(client))
