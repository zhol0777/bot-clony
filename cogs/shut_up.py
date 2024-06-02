'''
Track specific strings (like gifs of a cat jerking itself off or a lil shoosh soundtest)
that triggers response
'''
# from functools import lru_cache
from datetime import datetime, timezone
import logging
import os
import typing

from discord.ext import commands, tasks
import discord

import db
import util

ZHOLBOT_CHANNEL_ID = int(os.getenv('ZHOLBOT_CHANNEL_ID', '0'))
HELPER_CHAT_ID = int(os.getenv('HELPER_CHAT_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
log = logging.getLogger(__name__)

LOOP_TIME = 60
SPAM_INTERVAL = 15


class DoublePosting(commands.Cog):
    '''Oh My God Stop Posting Multiple Times In Every Channel'''
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        '''mostly to start task loop on bringup'''
        try:
            self.purge_loop_function.start()  # pylint: disable=no-member
        except RuntimeError:
            pass

    @tasks.loop(seconds=LOOP_TIME)
    async def purge_loop_function(self):
        '''delete messages that were initially sent too long ago'''
        with db.bot_db:
            now = datetime.now(timezone.utc)
            for message in db.MessageIdentifier.select():
                time_delta = now - self.parse_date_time_str(message.created_at)
                if time_delta.seconds > 60:
                    message.delete_instance()

    def get_message_identifier(self, message: discord.Message) -> typing.Union[db.MessageIdentifier, None]:
        '''kind of a macro'''
        return db.MessageIdentifier.get_or_none(message_hash=hash(message.content),
                                                user_id=message.author.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        '''send annoyance message if message has been sent multiple times in last 15s'''
        # do not do this to zholbot and end up in infinite feedback loop
        if message.author.id == self.client.user.id:
            return
        if message.stickers:
            return
        with db.bot_db:
            message_identifier = self.get_message_identifier(message)

            if not message_identifier:
                db.MessageIdentifier.create(message_hash=hash(message.content),
                                            user_id=message.author.id,
                                            instance_count=1,
                                            created_at=message.created_at)
                return

            time_delta = message.created_at - self.parse_date_time_str(message_identifier.created_at)
            # send annoyance message if message has been sent multiple times in last 15s
            if time_delta.seconds > SPAM_INTERVAL:
                return

            # increment count
            db.MessageIdentifier.update(
                instance_count=db.MessageIdentifier.instance_count + 1).where(
                    db.MessageIdentifier.user_id == message.author.id,
                    db.MessageIdentifier.message_hash == hash(message.content)
                ).execute()

            # TODO: make this SCIF instead
            channel = self.client.get_channel(ZHOLBOT_CHANNEL_ID)
            if not channel:
                return
            # send message if over threshold
            message_identifier = self.get_message_identifier(message)
            if message_identifier.instance_count < 4:
                return

            embed = discord.Embed(color=discord.Colour.orange())
            embed.set_author(name="Spam Signal")
            embed.add_field(name="User", value=f'<@{message.author.id}>')
            embed.add_field(name="Message Content", value=f'`{message.content}`')
            embed.add_field(name="Instance Count", value=message_identifier.instance_count)
            embed.add_field(name="Message link", value=str(message.jump_url))
            content = f'<@688959322708901907>: <@{message.author.id}> is spamming a lot!'
            if not message_identifier.tracking_message_id:
                tracking_message = await channel.send(content=content, embed=embed)
                db.MessageIdentifier.update(
                    tracking_message_id=tracking_message.id).where(
                        db.MessageIdentifier.user_id == message.author.id,
                        db.MessageIdentifier.message_hash == hash(message.content)
                    ).execute()
                
            else:
                original_message = await channel.fetch_message(message_identifier.tracking_message_id)
                await original_message.edit(content=content, embed=embed)

    def parse_date_time_str(self, date_time_str) -> datetime:
        "dates are sometimes saved in two different formats"
        try:
            return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f%z')
        except ValueError:
            return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S%z')

    async def purge(self, user_id: int):
        '''
        Go through last 100 messages and purge those from user
        tagged or replied to
        '''
        purged_user = self.client.get_user(user_id)

        def is_purged_user(message):
            return message.author == purged_user

        # TODO: figure out less dumb way to do this
        # TODO: async purge
        guild = util.fetch_primary_guild(self.client)
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.purge(limit=100, check=is_purged_user)


async def setup(client):
    '''setup'''
    await client.add_cog(DoublePosting(client))
