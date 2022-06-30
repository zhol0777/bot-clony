'''Purge users messages'''
import os

from discord.ext import commands
import discord
import util

MOD_ROLE = os.getenv('MOD_ROLE')


class Deport(commands.Cog):
    '''Cog to ban+purge users messages'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_role(MOD_ROLE)
    async def purgelast(self, ctx: commands.Context, *args):
        '''
        Usage: !purgelast [@ user tag] [count]
               [as message reply] !purgelast [count]
        Go through last 100 messages and purge those from user
        tagged or replied to
        '''
        if ctx.message.reference is not None:
            original_msg = await ctx.fetch_message(
                id=ctx.message.reference.message_id)
            purged_user = original_msg.author
            count = int(args[0]) if len(args) > 0 else 100
        else:
            user_id = util.get_id_from_tag(args[0])
            purged_user = self.client.get_user(user_id)
            count = int(args[1]) if len(args) > 1 else 100

        def is_purged_user(message):
            return message.author == purged_user

        # TODO: figure out less dumb way to do this
        # TODO: async purge
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.purge(limit=count, check=is_purged_user)

        # TODO: is this necessary?
        await ctx.guild.ban(purged_user)
        # TODO: decide on delete_message_days value for ctx.guild.ban arg
        await ctx.message.delete()

    @commands.command()
    @commands.has_role(MOD_ROLE)
    async def purge(self, ctx: commands.Context, count: int):
        '''
        Usage: !purge [count]
        Purges the last [count] messages from the channel it is posted in
        '''
        await ctx.message.delete()
        await ctx.channel.purge(limit=count-1)


def setup(client):
    '''setup'''
    client.add_cog(Deport(client))
