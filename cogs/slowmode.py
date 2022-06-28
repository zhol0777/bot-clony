'''
Cog to allow helpers to apply slowmode in help channels
'''
import discord
from discord.ext import commands


class SlowMode(commands.Cog):
    '''Cog to allow helpers to apply slowmode in help channels'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role('Helpers', 'mods')
    async def slowmode(self, ctx: commands.Context, interval: int):
        '''Activate slowmode in help channels'''
        # TODO: check against channel ID instead of name
        if isinstance(ctx.channel, discord.TextChannel) and \
                ctx.channel.name in ['kb-help', 'kb-buying-advice']:
            await ctx.channel.edit(slowmode_delay=interval)
            await ctx.channel.send("Slow it down!")


def setup(client):
    '''setup'''
    client.add_cog(SlowMode(client))
