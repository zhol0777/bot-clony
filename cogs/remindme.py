'''
DM a user a reminder of something they needed to be reminded of
'''
import asyncio
import os
import time
from typing import Union

import discord
from discord.ext import commands, tasks  # type: ignore

import db
import util

LOOP_TIME = 60
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))


class RemindMe(commands.Cog):
    '''Send a reminder later'''
    def __init__(self, client):
        self.client = client
        self.guild = None

    @commands.command()
    async def remindme(self, ctx: commands.Context,  # pylint: disable=keyword-arg-before-vararg,too-many-branches
                       wait_time: str = '0', *args):
        '''
        Usage:  !remindme [wait_time] [reason...]
        '''
        with db.bot_db:
            try:
                wait_time_s = util.get_id_from_tag(wait_time)
            except ValueError:
                await util.handle_error(ctx, self.remindme.__doc__)
            if wait_time.endswith('m'):
                wait_time_s *= 60
            if wait_time.endswith('h'):
                wait_time_s *= (60 * 60)
            elif wait_time.endswith('d'):
                wait_time_s *= (60 * 60 * 24)
            elif wait_time.endswith('w'):
                wait_time_s *= (60 * 60 * 24 * 7)
            elif wait_time.endswith('M'):
                wait_time_s *= (60 * 60 * 24 * 30)
            elif wait_time.endswith('y'):  # thanks jymv
                wait_time_s *= (60 * 60 * 24 * 365)

            if len(args) > 0:
                reason = ' '.join(args)
            else:
                reason = 'No reason provided'

            alert_time = int(time.time()) + wait_time_s

            if wait_time_s > LOOP_TIME:
                db.Reminder.create(
                    user_id=ctx.message.author.id,
                    reminder_epoch_time=alert_time,
                    reason=reason,
                    message_url=ctx.message.jump_url
                )
                await ctx.channel.send(f'Will send reminder near <t:{alert_time}:f>')
            else:
                await ctx.channel.send(f'Will send reminder near <t:{alert_time}:f>')
                await asyncio.sleep(wait_time_s)
                await self.dm_reminder(ctx.message.author, reason, alert_time,
                                       ctx.message.jump_url)

    @tasks.loop(seconds=60)
    async def send_reminders(self):
        '''loop through db to see when to eject someone'''
        current_time = time.time()
        with db.bot_db:
            reminders = db.Reminder.select()
            for reminder in reminders:
                if current_time > reminder.reminder_epoch_time:
                    reminded_user = await self.client.fetch_user(reminder.user_id)
                    reason = str(reminder.reason) if reminder.reason else 'No Reason Provided'
                    await self.dm_reminder(reminded_user, reason, reminder.reminder_epoch_time,
                                           reminder.message_url)
                    reminder.delete_instance()

    async def dm_reminder(self, reminded_user: Union[discord.User, discord.Member],
                          reason: str, reminder_time: int, message_url: str) -> None:
        '''front-end for sending the reminder between reminders in or outside of db'''
        channel = await reminded_user.create_dm()
        embed = discord.Embed(color=discord.Colour.orange())
        embed.set_author(name="Reminder")
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Time", value=f'<t:{reminder_time}:f>')
        embed.add_field(name="Message link", value=str(message_url))
        try:
            await channel.send(embed=embed)
        except discord.errors.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        '''mostly to start task loop on bringup'''
        try:
            self.send_reminders.start()  # pylint: disable=no-member
        except RuntimeError:
            pass


class TeeTime(commands.Cog):
    """golf"""
    def __init__(self, client):
        self.client = client
        self.ping_channel_id = 234802192014508033  # kb-keyboards
        self.club_role_id = 1275305906946703443  # golf club

    def seconds_left_until_tee_time(self) -> int:
        """calculate seconds left until it is time to golf again"""
        week = 60 * 60 * 24 * 7
        offset = 444600  # tee time is at 8:30 pm PST
        current_time = int(time.time())
        time_since_last_golf = (current_time - offset) % week
        time_until_next_golf = week - time_since_last_golf
        return time_until_next_golf

    @commands.command()
    @commands.has_role(1275305906946703443)
    async def putt(self, ctx):
        """post when tee off is"""
        next_date = int(time.time()) + self.seconds_left_until_tee_time()
        await ctx.channel.send(
            f"Golf will happen at <t:{next_date}>")

    @tasks.loop(seconds=60)
    async def tee_off(self):
        """ping people for putt party"""
        if self.seconds_left_until_tee_time() < 60:
            guild = await util.fetch_primary_guild(self.client)
            ping_channel = guild.get_channel(self.ping_channel_id)
            await ping_channel.send(f"<@&{self.club_role_id}> it's time to tee up!")

    @commands.Cog.listener()
    async def on_ready(self):
        '''mostly to start task loop on bringup'''
        try:
            self.tee_off.start()  # pylint: disable=no-member
        except RuntimeError:
            pass


async def setup(client):
    '''setup'''
    await client.add_cog(RemindMe(client))
    await client.add_cog(TeeTime(client))
