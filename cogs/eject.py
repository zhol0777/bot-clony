'''
Eject users from the help channels and log the assignment accordingly
'''
import asyncio
import os
import time

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
                ctx.message.reference.message_id)
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
    async def tempeject(self, ctx: commands.Context,  # pylint: disable=keyword-arg-before-vararg
                        tag: str, sleep_time: str = '0', *args):
        '''
        Usage:  !tempeject [@ user tag] [time] [reason...]
        [reply] !tempeject [time] [reason...]
        '''
        if ctx.message.reference is not None:
            # replying to someone who is about to be ejected
            original_msg = await ctx.fetch_message(
                ctx.message.reference.message_id)
            ejected_user = original_msg.author
            user_id = ejected_user.id
            ejected_member = await ctx.guild.fetch_member(ejected_user.id)
            sleep_time = tag
        else:
            user_id = util.get_id_from_tag(tag)
            ejected_member = await ctx.guild.fetch_member(user_id)

        sleep_time_s = util.get_id_from_tag(sleep_time)
        if sleep_time.endswith('m'):
            sleep_time_s *= 60
        elif sleep_time.endswith('h'):
            sleep_time_s *= (60 * 60)
        elif sleep_time.endswith('d'):
            sleep_time_s *= (60 * 60 * 24)
        elif sleep_time.endswith('w'):
            sleep_time_s *= (60 * 60 * 24 * 7)

        lift_time = int(time.time()) + sleep_time_s
        with db.bot_db:
            await util.apply_role(ejected_member, user_id, 'ejected',
                                  ' '.join(args), False)
            await ctx.channel.send(f'lol ejected\neject will be lifted at <t:{lift_time}:f>')
            await asyncio.sleep(sleep_time_s)
            await util.remove_role(ejected_member, user_id, 'ejected')


async def setup(client):
    '''setup'''
    await client.add_cog(Eject(client))
