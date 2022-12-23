"""
Cog to allow helpers to apply slowmode in help channels
"""
import os

import time
from discord.ext import commands
import discord

import util


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

        self.slowmode_config = {
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

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def autoslow(self, ctx: commands.Context, messages: str, delay: str = None):
        """Change auto slowmode timing"""
        if messages.lower() == "off":
            self.disabled = True
            await ctx.channel.send("Disabled auto slowmode")
        if messages.lower() == "on":
            self.disabled = False
            await ctx.channel.send("Enabled auto slowmode")
        messages_int = util.get_id_from_tag(messages)
        delay_int = util.get_id_from_tag(delay)
        if messages_int in self.slowmode_config:
            self.slowmode_config[messages_int] = delay_int
            await ctx.channel.send(self.slowmode_config)
        else:
            await ctx.channel.send("Key not in dict")

    def get_delay(self, message_count):
        """Delay based on amount of messages"""
        message_limits = sorted(self.slowmode_config, reverse=True)
        for limit in message_limits:
            if message_count >= limit:
                return self.slowmode_config[limit]
        return 0

    async def update_slowmode(self):
        """Gets slowmode delay and updates channel"""
        if self.disabled is True:
            return
        new_channel_delays = {}
        for channel_id, messages in self.message_cache.items():
            delay = self.get_delay(messages)
            if channel_id in self.previous_delays:
                if self.previous_delays[channel_id] == delay:
                    new_channel_delays[channel_id] = delay
                    continue
            channel = self.client.get_channel(channel_id)
            await channel.edit(slowmode_delay=delay)
            new_channel_delays[channel_id] = delay

        self.last_updated = time.time()
        self.previous_delays = new_channel_delays

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages in help channels"""

        channel_id = message.channel.id

        if self.disabled is True:
            return

        if channel_id not in SLOWMODE_CHANNELS:
            return

        if time.time() >= self.last_updated + self.update_frequency:
            await self.update_slowmode()

        if message.channel.id not in self.message_cache:
            self.message_cache[channel_id] = 1
            return

        self.message_cache[channel_id] += 1


async def setup(client):
    """Setup"""
    await client.add_cog(SlowMode(client))
