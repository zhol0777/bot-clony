'''
Command to sanitize trackers out of URL parameters by stripping params
'''

from discord.ext import commands
import discord
import logging

import util

log = logging.getLogger(__name__)


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
        sanitized_message, needs_sanitizing, _ = util.sanitize_message(
            reply_message.content)
        if needs_sanitizing:
            await message.channel.send(sanitized_message, reference=reply_message,
                                       mention_author=False)
            try:
                await message.edit(suppress=True)
            except Exception:
                log.exception("Bot is missing MANAGE_MESSAGES permission, cannot hide embed")

    @commands.command(aliases=['sanitise'])
    async def sanitize(self, ctx: commands.Context) -> None:
        '''
        Usage: !sanitize [url1] [url2] ...
               [as message reply] !sanitize
        Sanitizes URLs in messages it is told to
        '''
        await self.send_sanitized_message(ctx.message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        '''auto-sanitize messages where necessary when requested'''
        if message.author.bot:
            return
        if message.attachments:
            for attachment in message.attachments:
                # URL for image sometimes has a bunch of inscrutable parameters
                # that just clutter chat if they're sanitized away, and breaks the embed
                # hopefully users won't embed an image through a link and then other
                # garbage links, but if so, well, tell them to get bent
                if str(attachment.content_type).startswith('image'):
                    return
        await self.send_sanitized_message(message, get_reply=False)

    @commands.command()
    async def pink(self, ctx: commands.Context) -> None:
        '''
        Pink keys pink stabilizer pink keyboard I'm so cute aaaahhhh
        '''
        await ctx.message.channel.send("omg pink pcb pink switches pink hot sockets pink keycaps "
                                       "pink keyboard pink plate pink deskmat pink monitor "
                                       "pink lights pink mouse pink desk pink shelves pink artisans "
                                       "pink tray pink pink PIIIIINK IM SUCH A CUUUTIE AAAAAA")


async def setup(client):
    '''setup'''
    await client.add_cog(Sanitize(client))
