'''
Eject users from the help channels and log the assignment accordingly
'''
import asyncio
import logging
import os
import time

from discord.ext import commands, tasks  # type: ignore

import db
import util

HELPER_ROLE = os.getenv('HELPER_ROLE')
ZHOLBOT_CHANNEL_ID = int(os.getenv('ZHOLBOT_CHANNEL_ID', '0'))
MOD_ROLE = os.getenv('MOD_ROLE')
LOOP_TIME = 60
log = logging.getLogger(__name__)


class Eject(commands.Cog):
    '''Eject/uneject users'''
    def __init__(self, client):
        self.client = client
        self.guild = None

    @commands.command()
    @commands.has_any_role(HELPER_ROLE, MOD_ROLE)
    async def eject(self, ctx: commands.Context, *args):
        '''
        bot-sony handles eject role assignment.
        this only removes any possible temp eject so that a temp eject isn't
        removed later.
        Usage:  !eject [@ user tag] [reason...]
        [reply] !eject [reason...]
        '''

        if ctx.message.reference is not None:
            # replying to someone who is about to be ejected
            original_msg = await ctx.fetch_message(
                ctx.message.reference.message_id)
            ejected_user = original_msg.author
            user_id = ejected_user.id
        else:
            user_id = util.get_id_from_tag(args[0])
        with db.bot_db:
            db.UnejectTime.delete().where(
                db.UnejectTime.user_id == user_id
            ).execute()

    @commands.command()
    @commands.has_any_role(HELPER_ROLE)
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
    async def tempeject(self, ctx: commands.Context,  # pylint: disable=keyword-arg-before-vararg,too-many-branches
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

        with db.bot_db:
            temp_ejected = db.UnejectTime.get_or_none(user_id=user_id)
            if db.RoleAssignment.get_or_none(user_id=user_id,
                                             role_name='ejected') and not temp_ejected:
                await ctx.channel.send("User already ejected. No temp eject will be placed.")
                return
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
            # TODO: handle via role IDs
            await util.apply_role(ejected_member, user_id, 'ejected',
                                  ' '.join(args), False)
            if not temp_ejected:
                await ctx.channel.send(f'lol ejected <@{user_id}>\n'
                                       f'eject will be lifted at approx. <t:{lift_time}:f>')
                if sleep_time_s < LOOP_TIME:
                    await asyncio.sleep(sleep_time_s)
                    await util.remove_role(ejected_member, user_id, 'ejected')
                    channel = self.client.get_channel(ZHOLBOT_CHANNEL_ID)
                    await channel.send(f"removing temp eject for <@{user_id}>.\n"
                                       "if this is erroneous, please re-apply eject role and ask zhol for debug.")
                else:
                    db.UnejectTime.create(
                        user_id=user_id,
                        uneject_epoch_time=lift_time
                    )
            else:
                db.UnejectTime.update(
                    uneject_epoch_time=lift_time
                ).where(
                    (db.UnejectTime.user_id == user_id) &
                    (db.UnejectTime.uneject_epoch_time < lift_time)
                ).execute()
                if lift_time > temp_ejected.uneject_epoch_time:
                    await ctx.channel.send(f'temp eject will be extended to <t:{lift_time}:f>')
                else:
                    await ctx.channel.send('temp eject time will not be extended')

    @commands.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def unejectloopstart(self, ctx):  # pylint: disable=unused-argument
        '''start uneject loop'''
        self.guild, dm_channel = util.get_guild(ctx, self.client)
        try:
            self.undo_temp_eject.start()  # pylint: disable=no-member
            await dm_channel.send('temp eject monitoring loop started')
        except RuntimeError:
            await dm_channel.send('temp eject monitoring loop already running')

    @tasks.loop(seconds=LOOP_TIME)
    async def undo_temp_eject(self):
        '''loop through db to see when to eject someone'''
        current_time = time.time()
        with db.bot_db:
            entries = db.UnejectTime.select()
            for temp_eject_entry in entries:
                if current_time > temp_eject_entry.uneject_epoch_time:
                    channel = self.client.get_channel(ZHOLBOT_CHANNEL_ID)  # this is bot test channel
                    await channel.send(f"removing temp eject for <@{temp_eject_entry.user_id}>.\n"
                                       "if this is erroneous, please re-apply eject role and ask zhol for debug.")
                    ejected_member = await self.guild.fetch_member(temp_eject_entry.user_id)
                    await util.remove_role(ejected_member,
                                           temp_eject_entry.user_id,
                                           'ejected')
                    temp_eject_entry.delete_instance()


async def setup(client):
    '''setup'''
    await client.add_cog(Eject(client))
