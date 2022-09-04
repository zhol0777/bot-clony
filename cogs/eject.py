'''
Eject users from the help channels and log the assignment accordingly
'''
import asyncio
import os

from discord.ext import commands
import discord

import db
import util

HELPER_ROLE = os.getenv('HELPER_ROLE')
MOD_ROLE = os.getenv('MOD_ROLE')


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
        Listens for eject and only records the eject in db'''
        if ctx.message.reference is not None:
            # replying to someone who is about to be ejected
            original_msg = await ctx.fetch_message(
                id=ctx.message.reference.message_id)
            ejected_user = original_msg.author
            ejected_member = await ctx.guild.fetch_member(ejected_user.id)
            if isinstance(ejected_member, discord.Member):
                with db.bot_db:
                    db.RoleAssignment.create(
                        user_id=ejected_user.id,
                        role_name='ejected'
                    )

        else:
            ejected_user_id = util.get_id_from_tag(args[0])
            eject_reason = ' '.join(args[1:]) if len(args) >= 2 else ''
            ejected_member = await ctx.guild.fetch_member(ejected_user_id)
            await util.apply_role(ejected_member, ejected_user_id,
                                  'ejected', reason=eject_reason)

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def uneject(self, ctx: commands.Context, *args):
        '''
        Usage: !uneject [@ user tag]
        Uneject a user
        '''
        user_id = util.get_id_from_tag(args[0])
        ejected_member = await ctx.guild.fetch_member(user_id)
        await util.remove_role(ejected_member, user_id, 'ejected')

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def tempeject(self, ctx: commands.Context, tag: str, sleep_time: str,
                        *args):
        '''
        Usage: !tempeject [time] [@ user tag] [reason...]
        '''

        sleep_time_s = util.get_id_from_tag(sleep_time)
        if sleep_time.endswith('m'):
            sleep_time_s *= 60
        if sleep_time.endswith('h'):
            sleep_time_s *= 3600

        user_id = util.get_id_from_tag(tag)
        ejected_member = await ctx.guild.fetch_member(user_id)
        with db.bot_db:
            await util.apply_role(ejected_member, user_id, 'ejected',
                                  ' '.join(args), False)
            await ctx.channel.send('lol ejected')
            await asyncio.sleep(sleep_time_s)
            await util.remove_role(ejected_member, user_id, 'ejected')


def setup(client):
    '''setup'''
    client.add_cog(Eject(client))
