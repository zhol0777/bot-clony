'''
Track specific strings (like gifs of a cat jerking itself off or a lil shoosh soundtest)
that triggers response
'''
import logging
import os
import typing
from datetime import datetime

import discord
from discord.ext import commands, tasks
from urlextract import URLExtract

import db
import util

ZHOLBOT_CHANNEL_ID = int(os.getenv('ZHOLBOT_CHANNEL_ID', '0'))
SPAM_CONTAINMENT_CHANNEL_ID = int(os.getenv('SPAM_CONTAINMENT_CHANNEL_ID', '0'))
HELPER_CHAT_ID = int(os.getenv('HELPER_CHAT_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

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
        db.bot_db.execute_sql(
            "DELETE FROM messageidentifier WHERE created_at < datetime('now', '-60 seconds');")
        # with db.bot_db:
        #     now = datetime.now(timezone.utc)
        #     for message in db.MessageIdentifier.select():
        #         time_delta = now - self.parse_date_time_str(message.created_at)
        #         if time_delta.seconds > 60:
        #             message.delete_instance()

    def get_message_identifier(self, message: discord.Message,
                               row_id: int | None = None) -> typing.Union[db.MessageIdentifier, None]:
        '''kind of a macro'''
        if row_id:
            return db.MessageIdentifier.get_or_none(id=row_id)
        return db.MessageIdentifier.get_or_none(message_hash=hash(message.content),
                                                user_id=message.author.id)

    # TODO: deal with race condition
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        '''send annoyance message if message has been sent multiple times in last 15s'''
        # do not do this to zholbot and end up in infinite feedback loop
        # do not do this to messages that only have a sticker
        # do not do this to messages that are empty for some reason
        if any([message.author.id == self.client.user.id, message.stickers, not message.content]):
            return

        # NOTE: link won't detect if content is something like "discord dot gg"
        # so, uh, watch out! most spam we're getting is steamcommunity phishing
        # links which would normally detect anyway
        has_link = False
        for _ in URLExtract().gen_urls(message.content):
            has_link = True
            break
        if not has_link:
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
                    db.MessageIdentifier.id == message_identifier.id,  # pylint: disable=no-member
                ).execute()

            channel = self.client.get_channel(SPAM_CONTAINMENT_CHANNEL_ID)
            if not channel:
                channel = self.client.get_channel(ZHOLBOT_CHANNEL_ID)
                if not channel:
                    log.error("Please set up a containment channel!")
                    return

            # send message if over threshold
            message_identifier = self.get_message_identifier(message, message_identifier.id)  # type: ignore
            if message_identifier.instance_count < 5:  # type: ignore
                return

            embed = discord.Embed(color=discord.Colour.orange())
            embed.set_author(name="Spam Signal")
            embed.add_field(name="User", value=f'<@{message.author.id}>')
            embed.add_field(name="Message Content", value=f'`{message.content}`')
            embed.add_field(name="Instance Count", value=message_identifier.instance_count)  # type: ignore
            embed.add_field(name="Message link", value=str(message.jump_url))
            content = f'<@688959322708901907>: <@{message.author.id}> is spamming a lot!'
            content += '\nIf you are not sending phishing links, please explain what happened so mute can be lifted.'
            # need as fresh as possible because i don't know how to handle race conditions
            message_identifier = self.get_message_identifier(message, message_identifier.id)  # type: ignore
            if not message_identifier.tracking_message_id:  # type: ignore
                await util.apply_role(message.author, message.author.id, 'Razer Hate',  # type: ignore
                                      'this guy might be spamming')
                tracking_message = await channel.send(content=content, embed=embed)
                db.MessageIdentifier.update(
                    tracking_message_id=tracking_message.id).where(
                        db.MessageIdentifier.user_id == message.author.id,
                        db.MessageIdentifier.message_hash == hash(message.content)
                    ).execute()
                await self.purge(message.author.id, message.guild, message.content)  # type: ignore
            else:
                original_message = await channel.fetch_message(message_identifier.tracking_message_id)  # type: ignore
                await original_message.edit(content=content, embed=embed)

    def parse_date_time_str(self, date_time_str) -> datetime:
        "dates are sometimes saved in two different formats"
        if isinstance(date_time_str, datetime):
            return date_time_str
        try:
            return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f%z')
        except ValueError:
            return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S%z')

    async def purge(self, purged_user_id: int, guild: discord.Guild,
                    message_content: str):
        '''
        Go through last 100 messages and purge those from user
        tagged or replied to
        '''

        def should_be_purged(message: discord.Message):
            return message.author.id == purged_user_id and hash(message_content) == hash(message.content)

        # TODO: figure out less dumb way to do this
        # TODO: async purge
        # guild = await util.fetch_primary_guild(self.client)
        for channel in guild.channels:
            if not isinstance(channel, discord.TextChannel):
                continue
            try:
                # await channel.purge(limit=20, check=should_be_purged)
                async for message in channel.history(limit=20):
                    if should_be_purged(message):
                        try:
                            await message.delete()
                        except discord.NotFound:
                            pass  # hopefully already deleted?
            except discord.errors.Forbidden:
                pass
            except Exception as exc:  # pylint: disable=broad-exception-caught
                log.error("Cant purge from %s due to %s...", channel.name, exc)
                # await channel.purge(limit=20, check=should_be_purged)


async def setup(client):
    '''setup'''
    await client.add_cog(DoublePosting(client))
