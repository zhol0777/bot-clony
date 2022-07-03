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

    # pylint: disable=missing-function-docstring
    @commands.command()
    async def eight(self, ctx: commands.Context):
        await ctx.channel.send("No one likes row 8!")

    @commands.command()
    async def google(self, ctx: commands.Context):
        await ctx.channel.send("Look things up before you ask questions!")

    @commands.command()
    async def groupbuy(self, ctx: commands.Context):
        await ctx.channel.send("Individual consumers raise money for a product to be produced. "
                               "Money is then given to an organizer who pays a manufacturer to "
                               "produce that product.")

    @commands.command()
    async def northfacing(self, ctx: commands.Context):
        await ctx.channel.send("https://www.youtube.com/watch?v=pFySgr0xmPw")

    @commands.command()
    async def oos(self, ctx: commands.Context):
        await ctx.channel.send("Many products are produced in small, individual batches that are "
                               "run only at certain times. Hence, after these products have sold, "
                               "they remain out of stock unless another run is produced.")

    @commands.command()
    async def pins(self, ctx: commands.Context):
        await ctx.channel.send("Check the pins!")

    @commands.command()
    async def spraylubing(self, ctx: commands.Context):
        await ctx.channel.send("https://geekhack.org/index.php?topic=108287.0")


def setup(client):
    '''setup'''
    client.add_cog(Generics(client))
