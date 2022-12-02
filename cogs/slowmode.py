'''
Cog to allow helpers to apply slowmode in help channels
'''
import os

from discord.ext import commands
import discord

import util

HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))


class SlowMode(commands.Cog):
    '''Cog to allow helpers to apply slowmode in help channels'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def slowmode(self, ctx: commands.Context, interval_str: str):
        '''Activate slowmode in help channels'''
        # TODO: check against channel ID instead of name
        interval = util.get_id_from_tag(interval_str)
        if isinstance(ctx.channel, discord.TextChannel) and \
                ctx.channel.name in ['kb-help', 'kb-buying-advice']:
            await ctx.channel.edit(slowmode_delay=interval)
            await ctx.channel.send("Slow it down!")


async def setup(client):
    '''setup'''
    await client.add_cog(SlowMode(client))
