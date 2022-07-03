'''
Command to sanitize trackers out of URL parameters by stripping params
'''
import os

from discord.ext import commands
import discord

import util

MOD_CHAT_CHANNEL_NAME = os.getenv('MOD_CHAT')


class LifeAlert(commands.Cog):
    '''Send life alert message to mod chat'''
    def __init__(self, client):
        self.client = client

    async def provide_reply(self, ctx: commands.Context, args):
        '''Reply based on lifealert reason being provided'''
        reason = ' '.join(args) if len(args) > 0 else ''
        if not reason:
            reason = 'N/A'
            channel_msg = 'Provide a reason with lifealert!'
        else:
            channel_msg = 'LifeAlert received...'
        message_sent = await ctx.channel.send(channel_msg)
        return message_sent, reason

    @commands.command()
    async def lifealert(self, ctx: commands.Context, *args):
        '''
        Usage: !lifealert [reason...] ...
               [as message reply] !lifelaert [reason...]
        Sanitizes URLs in messages it is told to
        '''
        message_sent, reason = await self.provide_reply(ctx, args)
        message_to_link = await util.get_reply_message(ctx, message_sent)
        reporter = ctx.message.author
        await ctx.message.delete()
        channel = discord.utils.get(ctx.guild.channels,
                                    name=MOD_CHAT_CHANNEL_NAME)

        embed = discord.Embed(colour=discord.Colour.red())
        embed.set_author(name="LifeAlert")
        embed.add_field(name="Channel", value=ctx.channel.name)
        embed.add_field(name="Reason", value=reason)
        if message_to_link.author.name not in (reporter.name, self.client.user.name):
            embed.add_field(name="Reported user", value=message_to_link.author)
            if message_to_link.content:
                embed.add_field(name="Message content", value=message_to_link.content)
        embed.add_field(name="Link", value=message_to_link.jump_url)
        await channel.send('@here', embed=embed)

    @commands.command()
    async def fakelifealert(self, ctx: commands.Context, *args):
        '''
        Usage: !fakelifealert [reason...] ...
        '''
        await self.provide_reply(ctx, args)
        await ctx.message.delete()


def setup(client):
    '''setup'''
    client.add_cog(LifeAlert(client))
