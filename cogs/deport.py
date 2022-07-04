'''
Cog to deport/un-deport on-command and mark role assignment in db
'''
import os

from discord.ext import commands
import discord

import util

HELPER_ROLE = os.getenv('HELPER_ROLE')
MOD_ROLE = os.getenv('MOD_ROLE')


class Deport(commands.Cog):
    '''cog'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def deport(self, ctx: commands.Context, *args):
        '''
        Usage: !deport [@ user tag] [reason...]
               [as message reply] !deport [reason...]
        Deport a user from the elitism channels'''
        if ctx.message.reference is not None:
            # replying to someone who is about to be deported
            original_msg = await ctx.fetch_message(
                id=ctx.message.reference.message_id)
            deported_user = original_msg.author
            deported_member = await ctx.guild.fetch_member(deported_user.id)
            if isinstance(deported_member, discord.Member):
                await util.apply_role(deported_member, deported_user.id,
                                      'deported')

        else:
            deported_user_id = util.get_id_from_tag(args[0])
            deported_member = await ctx.guild.fetch_member(deported_user_id)
            if isinstance(deported_member, discord.Member):
                await util.apply_role(deported_member, deported_user_id,
                                      'deported')

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def undeport(self, ctx: commands.Context, *args):
        '''
        Usage: !undeport [@ user tag]
        Un-deport a user from elitism channels
        '''
        deported_user_id = util.get_id_from_tag(args[0])
        deported_member = await ctx.guild.fetch_member(deported_user_id)
        await util.remove_role(deported_member, deported_user_id,
                               'deported')


def setup(client):
    '''setup'''
    client.add_cog(Deport(client))
