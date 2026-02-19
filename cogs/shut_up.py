'''
Track specific strings (like gifs of a cat jerking itself off or a lil shoosh soundtest)
that triggers response
'''
import logging
import os
from datetime import datetime
from io import BytesIO

import better_profanity
import discord
import imagehash
from discord.ext import commands, tasks
from PIL import Image
from urlextract import URLExtract

import db
import util

TOXIC_CONTAINMENT_CHANNEL_ID = int(os.getenv('TOXIC_CONTAINMENT_CHANNEL_ID', '0'))
SPAM_CONTAINMENT_CHANNEL_ID = int(os.getenv('SPAM_CONTAINMENT_CHANNEL_ID', '0'))
BANNED_WORDLIST = os.getenv('BANNED_WORDLIST_FILE_PATH', '')
HELPER_CHAT_ID = int(os.getenv('HELPER_CHAT_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

LOOP_TIME = 60
SPAM_INTERVAL = 15


class ShutUp(commands.Cog):
    '''Oh My God Stop Posting Multiple Times In Every Channel'''
    def __init__(self, client: discord.Client):
        self.client = client
        self.should_censor = False
        if os.path.exists(BANNED_WORDLIST):
            better_profanity.profanity.load_censor_words_from_file(BANNED_WORDLIST)
            log.info("Bad words have been loaded into the censor.")
            self.should_censor = True
        else:
            log.info("Censor word file %s not found, do not engage censorship", BANNED_WORDLIST)
            better_profanity.profanity.load_censor_words([])

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

    def get_message_identifier(self, message_hash: str | int, author_id: int,
                               row_id: int | None = None,) -> db.MessageIdentifier:
        '''kind of a macro'''
        if row_id:
            return db.MessageIdentifier.get(id=row_id)
        return db.MessageIdentifier.get(message_hash=message_hash,
                                        user_id=author_id)

    # TODO: deal with race condition
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        '''
        send annoyance message if message has been sent multiple times in last 15s
        send user to jail if they're using a no-no word
        '''
        # do not do this to zholbot and end up in infinite feedback loop
        # do not do this to messages that only have a sticker
        # do not do this to messages that are empty for some reason
        # do not do this if the guy's already been contained
        if any([message.author.id == self.client.user.id,  # ty: ignore[unresolved-attribute]
                message.stickers,
                not message.content and not message.attachments and not message.embeds,
                message.channel.id in {TOXIC_CONTAINMENT_CHANNEL_ID,
                                       SPAM_CONTAINMENT_CHANNEL_ID}]):
            return

        if self.should_censor and better_profanity.profanity.contains_profanity(message.content):
            await util.apply_role(message.author, message.author.id, 'Razer Hate',  # ty: ignore[invalid-argument-type]
                                  'hatesonar set off by following message: '
                                  f'{message.content[:100]}...')
            await self.send_hate_alert(message)

        if message.attachments:
            attachment = None
            for att in message.attachments:
                if att.content_type and att.content_type.startswith('image/'):
                    attachment = att
                    break
            if not attachment:
                return
            buffer = BytesIO()
            await attachment.save(buffer)
            buffer.seek(0)
            img = Image.open(buffer)
            message_hash = str(imagehash.average_hash(img))
        # NOTE: link won't detect if content is something like "discord dot gg"
        # so, uh, watch out!
        elif message.mention_everyone or message.role_mentions or URLExtract().gen_urls(message.content):
            message_hash = str(hash(message.content))
        else:
            return

        with db.bot_db.atomic():
            db.bot_db.execute_sql(
                "INSERT INTO messageidentifier (message_hash, user_id, instance_count, created_at) "
                "VALUES (?, ?, 1, ?) "
                "ON CONFLICT(message_hash, user_id) DO UPDATE SET instance_count = instance_count + 1",
                (message_hash, message.author.id, message.created_at)
            )

        with db.bot_db:
            # Then fetch the updated row if you need instance_count:
            message_identifier = self.get_message_identifier(message_hash, message.author.id)
            time_delta = message.created_at - self.parse_date_time_str(message_identifier.created_at)  # ty: ignore[invalid-argument-type]
            # send annoyance message if message has been sent multiple times in last 15s
            if message_identifier.instance_count > 1:
                log.info("%s has repeated message hash %s %s times", message.author.name, message_hash,
                        message_identifier.instance_count)
            if time_delta.seconds > SPAM_INTERVAL:
                return
            if message_identifier.instance_count < 5:
                return
            await self.send_spam_alert(message, message_hash, message_identifier)

    async def send_hate_alert(self, message: discord.Message):
        '''
        Alert channel for guy spreading likely hate speech
        '''
        embed = discord.Embed(color=discord.Colour.orange())
        embed.set_author(name="Hate Signal")
        embed.add_field(name="User", value=f'<@{message.author.id}>')
        embed.add_field(name="Message Content", value=f'`{message.content}`')
        embed.add_field(name="Message link", value=str(message.jump_url))
        content = f'<@688959322708901907>: <@{message.author.id}> is sending messages that can be interpreted '
        content += 'as hateful. \nIf this is not the case, please explain what happened so mute can be lifted.'
        if channel := await self.get_containment_channel():
            await channel.send(content=content, embed=embed)

    async def send_spam_alert(self, message: discord.Message, message_hash: str | int,
                              message_identifier: db.MessageIdentifier):
        '''
        Alert channel for likely compromised account
        '''
        log.warning("Attempting to send spam alert for user %s", message.author.name)
        embed = discord.Embed(color=discord.Colour.orange())
        embed.set_author(name="Spam Signal")
        embed.add_field(name="User", value=f'<@{message.author.id}>')
        embed.add_field(name="Message Content", value=f'`{message.content}`')
        attachment_str_field = \
            ' '.join(f"[{idx}]({attachment.url})" for idx, attachment in enumerate(message.attachments))
        if attachment_str_field:
            embed.add_field(name="Message attachments", value=attachment_str_field)
        embed.add_field(name="Instance Count", value=message_identifier.instance_count)
        embed.add_field(name="Message link", value=str(message.jump_url))
        content = f'<@688959322708901907>: <@{message.author.id}> is spamming a lot!'
        content += '\nIf you are not sending phishing links, please explain what happened so mute can be lifted.'
        # need as fresh as possible because i don't know how to handle race conditions
        message_identifier = self.get_message_identifier(message_hash, message.author.id)
        if not message_identifier.tracking_message_id:
            await util.apply_role(message.author, message.author.id, 'Razer Hate',  # ty: ignore[invalid-argument-type]
                                    'this guy might be spamming')
            if channel := await self.get_containment_channel():
                tracking_message = await channel.send(content=content, embed=embed)
                db.MessageIdentifier.update(
                    tracking_message_id=tracking_message.id).where(
                        db.MessageIdentifier.user_id == message.author.id,
                        db.MessageIdentifier.message_hash == hash(message.content)
                    ).execute()
            await self.purge(message.author.id, message.guild)  # ty: ignore[invalid-argument-type]
        elif channel := await self.get_containment_channel():
            try:
                original_message = await channel.fetch_message(
                    message_identifier.tracking_message_id)
            except discord.NotFound:
                log.error("Could not find spam alert message to edit even though it is seemingly sent?")
            await original_message.edit(content=content, embed=embed)
        else:
            log.error("Cannot send spam alert due to missing channel?")

    def parse_date_time_str(self, date_time_str: str | datetime) -> datetime:
        "dates are sometimes saved in two different formats"
        if isinstance(date_time_str, datetime):
            return date_time_str
        try:
            return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f%z')
        except ValueError:
            return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S%z')

    async def get_containment_channel(self) -> discord.TextChannel | None:
        '''
        provide containment channel since cannot be done during init
        '''
        channel = self.client.get_channel(SPAM_CONTAINMENT_CHANNEL_ID)
        if not channel:
            channel = self.client.get_channel(TOXIC_CONTAINMENT_CHANNEL_ID)
        if not channel:
            log.error("Please set up a containment channel!")
            return
        if not isinstance(channel, discord.TextChannel):
            log.error("Containment channel should be a TextChannel, not %s", type(channel))
            return
        return channel

    async def purge(self, purged_user_id: int, guild: discord.Guild):
        '''
        Go through last 100 messages and purge those from user
        tagged or replied to
        '''
        # TODO: figure out less dumb way to do this
        # TODO: async purge
        # guild = await util.fetch_primary_guild(self.client)
        for channel in guild.channels:
            if not isinstance(channel, discord.TextChannel):
                continue
            try:
                # await channel.purge(limit=20, check=should_be_purged)
                async for message in channel.history(limit=20):
                    if message.author.id == purged_user_id:
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
    await client.add_cog(ShutUp(client))
