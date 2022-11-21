'''
Cog to allow helpers to apply slowmode in help channels
'''
import os

from discord.ext import commands
import discord

import util

import time

HELPER_ROLE = os.getenv('HELPER_ROLE')
MOD_ROLE = os.getenv('MOD_ROLE')

CHANNELS = [190327462087884811, 766335071590023247]

message_cache = {}
previous_delays = {}
last_updated = 0


UPDATE_FREQUENCY = 30
time_configs = {
    # messages per UPDATE_FREQUENCY : slowmode delay
    5: 0,
    10: 1,
    20: 3,
    30: 5,
    40: 10,
    50: 15,
}


class SlowMode(commands.Cog):
    '''Cog to allow helpers to apply slowmode in help channels'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def slowmode(self, ctx: commands.Context, interval_str: str):
        '''Activate slowmode in help channels'''
        interval = util.get_id_from_tag(interval_str)
        if isinstance(ctx.channel, discord.TextChannel) and ctx.channel.id in CHANNELS:
            await ctx.channel.edit(slowmode_delay=interval)
            await ctx.channel.send("Slow it down!")


    def get_delay(self, message_count):
        message_limits = sorted(time_configs, reverse=True)
        for limit in message_limits:
            if message_count >= limit:
                return time_configs[limit]
        return 0


    async def update_slowmode(self):
        global last_updated, message_cache, previous_delays
        new_channel_delays = {}
        for channel_id in message_cache.keys():
            delay = self.get_delay(message_cache[channel_id])
            if channel_id in previous_delays.keys():
                if previous_delays[channel_id] == delay:
                    new_channel_delays[channel_id] = delay
                    continue
            channel = self.client.get_channel(channel_id)
            await channel.edit(slowmode_delay=delay)
            await channel.send(f"Slowmode has been automaticly set to {delay}s")
            new_channel_delays[channel_id] = delay

        message_cache = {}
        last_updated = time.time()
        previous_delays = new_channel_delays


    @commands.event
    async def on_message(self, message):
        global last_updated, message_cache
        channel_id = message.channel.id

        if time.time() >= last_updated + UPDATE_FREQUENCY:
            await self.update_slowmode()

        if channel_id not in CHANNELS:
            return

        if message.channel.id not in message_cache.keys():
            message_cache[channel_id] = 1
            return

        message_cache[channel_id] += 1


async def setup(client):
    '''setup'''
    await client.add_cog(SlowMode(client))
