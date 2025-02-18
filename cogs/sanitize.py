'''
Command to sanitize trackers out of URL parameters by stripping params
'''
import os
import pickle
from functools import lru_cache
from typing import Set

import discord
from discord.ext import commands

import db
import sanitizer_utils
import util

SCOLD_MESSAGE = '''
-# [*Why was this message sent?*](<https://faun.pub/url-sanitization-the-why-and-how-9f14e1547151>)
'''

MESSAGE_PREFIX = '''
List of sanitized URLs:
'''

MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
ALLOWED_PARAMS_FILE = os.getenv('ALLOWED_PARAMS_FILE', '')


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
        sanitized_message, needs_sanitizing, post_warning = sanitizer_utils.sanitize_message(
            reply_message.content)
        if needs_sanitizing:
            if post_warning:
                sanitized_message = MESSAGE_PREFIX + sanitized_message + SCOLD_MESSAGE
            await message.channel.send(sanitized_message, reference=reply_message,
                                       mention_author=False)
            try:
                await message.edit(suppress=True)
            except Exception:  # pylint: disable=broad-exception-caught
                pass

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
    @commands.has_any_role(MOD_ROLE_ID)
    async def autosanitize(self, ctx, value: bool) -> None:
        '''
        Usage: !autosanitize True
               !autosanitize False
        Enables or disables auto-sanitizing feature for the channel the message is sent in
        '''
        with db.bot_db:
            if value:
                db.SanitizedChannel.create(
                    channel_id=ctx.channel.id
                )
                await ctx.channel.send(f"Enabling auto-sanitizer for {ctx.channel.name}")
            else:
                db.SanitizedChannel.delete().where(
                    db.SanitizedChannel.channel_id == ctx.channel.id
                ).execute()
                await ctx.channel.send(f"Disabling auto-sanitizer for {ctx.channel.name}")
        self.should_sanitize.cache_clear()  # pylint: disable=no-member

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
        if self.should_sanitize(message.channel.id):
            if message.content.startswith(f"{os.getenv('COMMAND_PREFIX')}sanitize"):
                return  # someone else will get to it
            if message.content.startswith('# '):
                is_annoying = True
                for line in message.content.split('\n'):
                    if not line.strip().startswith('# '):
                        is_annoying = False
                        break
                if is_annoying:
                    await message.delete()
                return
            await self.send_sanitized_message(message, get_reply=False)

    @commands.command()
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def allow_param(self, ctx, param) -> None:  # noqa: ARG002  # pylint: disable=W0613
        """command to add allowed param at runtime"""
        non_hardcoded_params: Set[str] = set()
        if ALLOWED_PARAMS_FILE and os.path.exists(ALLOWED_PARAMS_FILE):
            try:
                with open(ALLOWED_PARAMS_FILE, 'rb') as allowed_params_data:
                    non_hardcoded_params = pickle.load(allowed_params_data)
            except (pickle.PicklingError, EOFError):
                pass
            non_hardcoded_params.add(param)
            with open(ALLOWED_PARAMS_FILE, 'wb') as allowed_params_data:
                pickle.dump(non_hardcoded_params, allowed_params_data)

    @commands.command()
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def remove_param(self, ctx, param) -> None:  # noqa: ARG002  # pylint: disable=W0613
        """command to remove allowed param at runtime"""
        if ALLOWED_PARAMS_FILE and os.path.exists(ALLOWED_PARAMS_FILE):
            try:
                with open(ALLOWED_PARAMS_FILE, 'rb') as allowed_params_data:
                    non_hardcoded_params: Set[str] = pickle.load(allowed_params_data)
            except (EOFError, pickle.UnpicklingError):
                pass
            if param in non_hardcoded_params:
                non_hardcoded_params.remove(param)
                with open(ALLOWED_PARAMS_FILE, 'wb') as allowed_params_data:
                    pickle.dump(non_hardcoded_params, allowed_params_data)

    @lru_cache  # set max_size if server has more than 128 channels
    def should_sanitize(self, message_channel_id: int) -> bool:
        '''determines based on message_channel_id if a message should be auto-sanitized'''
        with db.bot_db:
            return db.SanitizedChannel.select().where(
                    db.SanitizedChannel.channel_id == message_channel_id).exists()


async def setup(client):
    '''setup'''
    await client.add_cog(Sanitize(client))
