'''
Eject users from the help channels and log the assignment accordingly
'''
import asyncio
import logging
import os
import time

from discord.ext import commands, tasks
import discord

import db
import util

HELPER_ROLE = os.getenv('HELPER_ROLE')
MOD_ROLE = os.getenv('MOD_ROLE')
LOOP_TIME = 60
log = logging.getLogger(__name__)


class Eject(commands.Cog):
    '''Eject/uneject users'''
    def __init__(self, client):
        self.client = client
        self.guild = None

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
            await ctx.channel.send(f'lol ejected\neject will be lifted at approx. <t:{lift_time}:f>')
            if sleep_time_s < LOOP_TIME:
                await asyncio.sleep(sleep_time_s)
                await util.remove_role(ejected_member, user_id, 'ejected')
            else:
                db.UnejectTime.create(
                    user_id=user_id,
                    uneject_epoch_time=lift_time
                )

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def unejectloopstart(self, ctx):  # pylint: disable=unused-argument
        '''start uneject loop'''
        for guild in self.client.guilds:
            if guild.id == int(os.getenv('SERVER_ID', '0')):
                self.guild = guild
                self.undo_temp_eject.start()  # pylint: disable=no-member

    @tasks.loop(seconds=LOOP_TIME)
    async def undo_temp_eject(self):
        '''loop through db to see when to eject someone'''
        current_time = time.time()
        with db.bot_db:
            entries = db.UnejectTime.select()
            for temp_eject_entry in entries:
                if current_time > temp_eject_entry.uneject_epoch_time:
                    ejected_member = await self.guild.fetch_member(temp_eject_entry.user_id)
                    log.debug('Remove eject role for %s', ejected_member.display_name)
                    temp_eject_entry.delete_instance()
                    await util.remove_role(ejected_member,
                                           temp_eject_entry.user_id,
                                           'ejected')


async def setup(client):
    '''setup'''
    await client.add_cog(Eject(client))
