'''
Command to sanitize trackers out of URL parameters by stripping params
'''
import discord
from discord.ext import commands

import util


class Sanitize(commands.Cog):
    '''Cog to sanitize messages'''
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['sanitise'])
    async def sanitize(self, ctx: commands.Context):
        '''
        Usage: !sanitize [url1] [url2] ...
               [as message reply] !sanitize
        Sanitizes URLs in messages it is told to
        '''
        reply_message = await util.get_reply_message(ctx, ctx.message)
        sanitized_message, needs_sanitizing = util.sanitize_message(
            reply_message.content)
        if needs_sanitizing:
            await ctx.channel.send(sanitized_message, reference=reply_message, mention_author=False)
            await ctx.channel.send("Stop leaving trackers in your URLs!\n"
                                   "<https://faun.pub/url-sanitization-the-why-and-how-9f14e1547151>")


async def setup(client):
    '''setup'''
    await client.add_cog(Sanitize(client))
