'''
Generic commands that provide simple responses
'''
from discord.ext import commands
import discord

import util

TRADE_DISCLAIMER = '''
This is a reminder that this discord SHOULD NOT be used as a trading platform.
We have no way of preventing scammers from utilizing this service and we have
 no way to verify trades or crosscheck the scammer list.
Exercise caution if you do trade with other members of the discord, and
 remember to always use Paypal "Goods and Services" or equivalent.
Trade with users here at your own risk.
'''

GROUP_BUY = '''
People interest in the product pay up front to the owner of the group buy to
 help the funding of the product. Once the product is succesfully funded it
 goes into production and begins to ship.
'''

OOS = '''
Wondering why everything you see is out of stock? Remember, this is a small
 hobby with high demand and low supply. Either you missed the group purchase
 or it will restock eventually.
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
        await ctx.channel.send("<- Nobody likes row 8")

    @commands.command()
    async def google(self, ctx: commands.Context):
        await ctx.channel.send("Look up your question before asking!")

    @commands.command()
    async def groupbuy(self, ctx: commands.Context):
        await ctx.channel.send(GROUP_BUY)

    @commands.command()
    async def northfacing(self, ctx: commands.Context):
        await ctx.channel.send("https://www.youtube.com/watch?v=pFySgr0xmPw")

    @commands.command()
    async def oos(self, ctx: commands.Context):
        await ctx.channel.send(OOS)

    @commands.command()
    async def pins(self, ctx: commands.Context):
        await ctx.channel.send("Check the pins!")

    @commands.command()
    async def spraylubing(self, ctx: commands.Context):
        await ctx.channel.send("https://geekhack.org/index.php?topic=108287.0")
    
    @commands.command()
    async def thock(self, ctx: commands.Context):
        '''Posts the vendors list'''
        reply_message = await util.get_reply_message(ctx, ctx.message)
        await ctx.channel.send('shut up',
                               reference=reply_message)


def setup(client):
    '''setup'''
    client.add_cog(Generics(client))
