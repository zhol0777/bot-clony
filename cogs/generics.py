'''
Generic commands that provide simple responses
'''
from discord.ext import commands
import discord

import util

TRADE_DISCLAIMER = '''
This is a reminder that MechKeys should NOT be used as a trading platform.
We do not audit against known scammer lists and do not exist to verify trades.
'''


class Generics(commands.Cog):
    '''Cog to provide very generic accounts'''
    def __init__(self, client):
        self.client = client

    @commands.command(
        aliases=['buy']
    )
    async def map(self, ctx: commands.Context):
        '''Posts the link to mechmap'''
        reply_message = await util.get_reply_message(ctx, ctx.message)
        await ctx.channel.send("https://mechmap.tech/",
                               reference=reply_message)

    @commands.command()
    async def trade(self, ctx: commands.Context):
        '''Posts a warning against organizing trades on discord'''
        reply_message = await util.get_reply_message(ctx, ctx.message)
        await ctx.channel.send(TRADE_DISCLAIMER, reference=reply_message)

    @commands.command()
    async def vendors(self, ctx: commands.Context):
        '''Posts the vendors list'''
        reply_message = await util.get_reply_message(ctx, ctx.message)
        await ctx.channel.send('https://mechkeys.me/VENDORS.html',
                               reference=reply_message)

    @commands.command()
    async def flashsales(self, ctx: commands.Context):
        '''apply/remove flash sales role'''
        user = ctx.message.author
        member = await ctx.guild.fetch_member(user.id)
        if member:
            if not discord.utils.get(member.roles, name='Flash Sales'):
                await util.apply_role(member, user.id, 'Flash Sales',
                                      enter_in_db=False)
            else:
                await util.remove_role(member, user.id, 'Flash Sales')

    @commands.command()
    async def vote(self, ctx: commands.Context):
        '''add emotes implying a poll'''
        await ctx.message.add_reaction("👍")
        await ctx.message.add_reaction("👎")


def setup(client):
    '''setup'''
    client.add_cog(Generics(client))
