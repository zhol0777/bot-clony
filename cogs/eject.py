'''
Eject users from the help channels and log the assignment accordingly
'''
import logging
import os

from discord.ext import commands
import discord

import db
import util

HELPER_ROLE = os.getenv('HELPER_ROLE')
MOD_ROLE = os.getenv('MOD_ROLE')


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Eject(commands.Cog):
    '''Eject/uneject users'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def eject(self, ctx: commands.Context, *args):
        '''
        Usage: !eject [@ user tag] [reason...]
               [as message reply] !eject [reason...]
        Eject a user from the help channels'''
        eject_role = discord.utils.get(ctx.guild.roles, name="ejected")
        if ctx.message.reference is not None:
            # replying to someone who is about to be ejected
            reply_message = await util.get_reply_message(ctx, ctx.message)
            original_msg = await ctx.fetch_message(
                id=ctx.message.reference.message_id)
            ejected_user = original_msg.author
            ejected_member = await ctx.guild.fetch_member(ejected_user.id)
            if isinstance(ejected_member, discord.Member):
                with db.bot_db:
                    await util.apply_role(ejected_member, ejected_user.id,
                                          eject_role, reason=' '.join(args))
                    await ctx.channel.send("lol ejected",
                                           reference=reply_message)
                    # TODO: send message into appeals channel

        else:
            ejected_user_id = util.get_id_from_tag(args[0])
            eject_reason = ' '.join(args[1:]) if len(args) >= 2 else ''
            ejected_member = await ctx.guild.fetch_member(ejected_user_id)
            with db.bot_db:
                await util.apply_role(ejected_member, ejected_user_id,
                                      eject_role, reason=eject_reason)
                await ctx.channel.send("lol ejected")

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def uneject(self, ctx: commands.Context, *args):
        '''
        Usage: !uneject [@ user tag]
        Uneject a user
        '''
        eject_role = discord.utils.get(ctx.guild.roles, name="ejected")
        user_id = util.get_id_from_tag(args[0])
        ejected_member = await ctx.guild.fetch_member(user_id)
        with db.bot_db:
            await util.remove_role(ejected_member, user_id, eject_role)


def setup(client):
    '''setup'''
    client.add_cog(Eject(client))
