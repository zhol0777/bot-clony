'''
Command to track usage of the word "thock"
'''
from functools import lru_cache
import os

from discord.ext import commands
import discord

import db

THOCK = 'thoc'
THOCK_EMOTE = os.getenv('THOCK_EMOTE', '🧱')
COMMAND_NAME = f"{os.getenv('COMMAND_PREFIX', '!')}thock"
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))


class ThockCount(commands.Cog):
    '''Cog to sanitize messages'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def thock(self, ctx) -> None:
        '''provide a count of total usage of 'thock' as well as local channel usage'''
        if not self.is_tracking(ctx.channel.id):
            return
        local_count = 0
        with db.bot_db:
            local_channel = db.ThockTrackingChannel.get_or_none(channel_id=ctx.channel.id)
            if local_channel:
                local_count = local_channel.counter
                await ctx.channel.send(f"{ctx.channel.name} `thock` usage reads: {local_count}")

    @commands.command()
    @commands.has_role(MOD_ROLE_ID)
    async def countthock(self, ctx, value: bool) -> None:
        '''
        Usage: !countthock True
               !countthock False
        Enables or disables auto-sanitizing feature for the channel the message is sent in
        '''
        with db.bot_db:
            if value:
                db.ThockTrackingChannel.create(
                    channel_id=ctx.channel.id,
                    counter=0
                )
                await ctx.channel.send(f"Enabling thock counting for {ctx.channel.name}")
            else:
                db.ThockTrackingChannel.delete().where(
                    db.ThockTrackingChannel.channel_id == ctx.channel.id
                ).execute()
                await ctx.channel.send(f"Disabling thock counting for {ctx.channel.name}")
        self.is_tracking.cache_clear()  # pylint: disable=no-member

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        '''increment thock-counter'''
        if message.author.bot:
            return
        if THOCK not in message.content.lower() or message.content.lower().startswith(COMMAND_NAME):
            return
        if self.is_tracking(message.channel.id):
            counter = 0
            for word in message.content.lower().split():
                if word.startswith(THOCK):
                    counter += 1
            if counter > 0:
                with db.bot_db:
                    db.ThockTrackingChannel.update(
                            counter=db.ThockTrackingChannel.counter + counter).where(
                                db.ThockTrackingChannel.channel_id == message.channel.id
                            ).execute()
                try:
                    await message.add_reaction(THOCK_EMOTE)
                except discord.errors.HTTPException:
                    # above is an emoji specific to mechkeys
                    pass

    @lru_cache  # set max_size if server has more than 128 channels
    def is_tracking(self, message_channel_id: int) -> bool:
        '''determines if channel has thock count tracked'''
        with db.bot_db:
            return db.ThockTrackingChannel.select().where(
                    db.ThockTrackingChannel.channel_id == message_channel_id).exists()


async def setup(client):
    '''setup'''
    await client.add_cog(ThockCount(client))
