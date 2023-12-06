'''
Track specific strings (like gifs of a cat jerking itself off or a lil shoosh soundtest)
that triggers response
'''
from functools import lru_cache
from datetime import datetime
import logging
import os

from discord.ext import commands, tasks
import discord

import db
import util

HELPER_CHAT_ID = int(os.getenv('HELPER_CHAT_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
log = logging.getLogger(__name__)

LOOP_TIME = 60


class ShutUp(commands.Cog):
    '''Oh My God Stop Posting This Awful Link'''
    def __init__(self, client):
        self.client = client

    @commands.group()
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def blacklist(self, ctx: commands.Context):
        '''
        !blacklist imagehosting.net/catjackoff.gif oh my god stop posting this
        '''
        message_words = ctx.message.content.split()
        try:
            message_text = message_words[0]
        except IndexError:
            await util.handle_error(ctx, "No bad link provided")
            return
        try:
            response_text = ' '.join(message_words[1:])
        except IndexError:
            response_text = ''
            await util.handle_error(ctx, "No response text provided, leaving blank")

        with db.bot_db():
            db.StupidMessage.create(message_text=message_text,
                                    response_text=response_text)
        await ctx.message.channel.send("Bot will now yell at people who post: " + message_text)
        self.get_blacklisted_messages.cache_clear()  # pylint: disable=no-member

    @blacklist.command()  # type: ignore
    @commands.has_any_role(HELPER_ROLE_ID, MOD_ROLE_ID)
    async def list(self, ctx: commands.Context):
        '''
        !blacklist list
        '''
        channel = self.client.get_channel(HELPER_CHAT_ID)
        if not channel:
            channel = await ctx.message.author.create_dm()
            if not channel:
                return

        stupid_messages = self.get_blacklisted_messages()

        for s_m in stupid_messages:  # pylint: disable=not-an-iterable
            embed = discord.Embed(color=discord.Colour.orange())
            embed.set_author(name="Message To Yell At")
            embed.add_field(name="id", value=str(s_m.id))
            embed.add_field(name="String to search", value=str(s_m.message_text))
            embed.add_field(name="Response text", value=str(s_m.response_text))
            await channel.send(embed=embed)

    @blacklist.command()  # type: ignore
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def delete(self, ctx: commands.Context, blacklist_id: int):
        '''
        Usage: !blacklist delete [blacklist ID]
        delete a blacklisted string per ID
        '''
        with db.bot_db:
            reason = db.StupidMessage.get_by_id(blacklist_id)
            if reason:
                reason.delete_instance()
                await ctx.channel.send("Deleted")
                self.get_blacklisted_messages.cache_clear()  # pylint: disable=no-member

    @lru_cache
    def get_blacklisted_messages(self):
        '''
        cache bad messages so you don't have to read DB on every message
        '''
        with db.bot_db():
            return db.StupidMessage.select()

    @commands.Cog.listener()
    async def on_message(self, message):
        '''Auto-respond to every message that bot finds sus'''
        for bl_msg in self.get_blacklisted_messages():
            if bl_msg.message_text():
                await message.channel.send(bl_msg.response_text)


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
            now = datetime.now()
            for message in db.TrackedMessage.select():
                time_delta = message.created_at - now
                if time_delta.seconds > 60:
                    message.delete_instance()

    @commands.Cog.listener()
    async def on_message(self, message):
        '''send annoyance message if message has been sent multiple times in last 15s'''
        with db.bot_db:
            tracked_message = db.TrackedMessage.get_or_none(message_hash=hash(message.content))
            if not tracked_message:
                db.TrackedMessage.create(message_hash=hash(message.content),
                                         created_at=message.created_at)
                return
            time_delta = message.created_at - tracked_message.created_at
            # send annoyance message if message has been sent multiple times in last 15s
            if time_delta.seconds < 15:
                await message.channel.send('Stop sending the same message to multiple channels!')


async def setup(client):
    '''setup'''
    await client.add_cog(ShutUp(client))
    await client.add_cog(DoublePosting(client))
