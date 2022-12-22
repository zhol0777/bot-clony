"""
Cog to allow helpers to apply slowmode in help channels
"""
import os

from discord.ext import commands
import discord

import util

import time

HELPER_ROLE = os.getenv("HELPER_ROLE")
MOD_ROLE = os.getenv("MOD_ROLE")

SLOWMODE_CHANNELS = [190327462087884811, 766335071590023247]


class SlowMode(commands.Cog):
    """Cog to allow helpers to apply slowmode in help channels"""

    def __init__(self, client):
        self.client = client
        self.message_cache = {}
        self.previous_delays = {}
        self.last_updated = 0
        self.disabled = False

        # How often slowmode is changed
        self.update_frequency = 30

        self.SLOWMODE_CONFIG = {
            # messages per self.update_frequency : slowmode delay
            5: 0,
            10: 1,
            20: 3,
            30: 5,
            40: 10,
            50: 15,
        }

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def slowmode(self, ctx: commands.Context, interval_str: str):
        """Activate slowmode in help channels"""
        interval = util.get_id_from_tag(interval_str)
        if (
            isinstance(ctx.channel, discord.TextChannel)
            and ctx.channel.id in SLOWMODE_CHANNELS
        ):
            await ctx.channel.edit(slowmode_delay=interval)
            await ctx.channel.send("Slow it down!")

    def get_delay(self, message_count):
        message_limits = sorted(self.SLOWMODE_CONFIG, reverse=True)
        for limit in message_limits:
            if message_count >= limit:
                return self.SLOWMODE_CONFIG[limit]
        return 0

    async def update_slowmode(self):
        """Gets slowmode delay and updates channel"""
        if self.disabled == True:
            return
        new_channel_delays = {}
        for channel_id in self.message_cache.keys():
            delay = self.get_delay(self.message_cache[channel_id])
            if channel_id in previous_delays.keys():
                if previous_delays[channel_id] == delay:
                    new_channel_delays[channel_id] = delay
                    continue
            channel = self.client.get_channel(channel_id)
            await channel.edit(slowmode_delay=delay)
            new_channel_delays[channel_id] = delay

        self.last_updated = time.time()
        previous_delays = new_channel_delays

    @commands.event
    async def on_message(self, message):
        """Listen for messages in help channels"""

        channel_id = message.channel.id

        if self.disabled == True:
            return

        if channel_id not in SLOWMODE_CHANNELS:
            return

        if time.time() >= self.last_updated + self.update_frequency:
            await self.update_slowmode()

        if message.channel.id not in self.message_cache.keys():
            self.message_cache[channel_id] = 1
            return

        self.message_cache[channel_id] += 1


async def setup(client):
    """Setup"""
    await client.add_cog(SlowMode(client))
