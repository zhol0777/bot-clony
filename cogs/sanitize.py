'''
Command to sanitize trackers out of URL parameters by stripping params
'''

from discord.ext import commands
import discord

import util

SCOLD_MESSAGE = '''
Beware of leaving trackers in your URLs! (Please complain to zhol to report false positives)
<https://faun.pub/url-sanitization-the-why-and-how-9f14e1547151>
'''

MESSAGE_PREFIX = '''
List of sanitized URLs:
'''


class Sanitize(commands.Cog):
    '''Cog to sanitize messages'''
    def __init__(self, client):
        self.client = client

    async def send_sanitized_message(self, message: discord.Message,
                                     get_reply: bool = True) -> None:
        '''
        util function to send a message with content sanitized
        :param message: the message to be sanitized
        :param get_reply: this needs to be set to false when called within on_message
                          otherwise bot will repeatedly sanitize the same message
        '''
        reply_message = await util.get_reply_message(message) if get_reply else message
        sanitized_message, needs_sanitizing = util.sanitize_message(
            reply_message.content)
        if needs_sanitizing:
            sanitized_message = MESSAGE_PREFIX + sanitized_message
            await message.channel.send(sanitized_message, reference=reply_message,
                                       mention_author=False)
            await message.channel.send(SCOLD_MESSAGE)

    @commands.command(aliases=['sanitise'])
    async def sanitize(self, ctx: commands.Context) -> None:
        '''
        Usage: !sanitize [url1] [url2] ...
               [as message reply] !sanitize
        Sanitizes URLs in messages it is told to
        '''
        await self.send_sanitized_message(ctx.message)
        await ctx.message.delete()

    @commands.command()
    async def pink(self, ctx: commands.Context) -> None:
        '''
        Pink keys pink stabilizer pink keyboard I'm so cute aaaahhhh
        '''
        await ctx.message.channel.send("Pink keys pink stabilizer pink keyboard I'm so cute aaaahhhh")


async def setup(client):
    '''setup'''
    await client.add_cog(Sanitize(client))
