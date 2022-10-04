'''
DM a user a reminder of something they needed to be reminded of
'''
import os
import time

from discord.ext import commands, tasks
import discord

import db
import util

LOOP_TIME = 60
MOD_ROLE = os.getenv('MOD_ROLE')


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
            if wait_time.endswith('h'):
                wait_time_s *= (60 * 60)
            elif wait_time.endswith('d'):
                wait_time_s *= (60 * 60 * 24)
            elif wait_time.endswith('w'):
                wait_time_s *= (60 * 60 * 24 * 7)
            elif wait_time.endswith('y'):  # thanks jymv
                wait_time_s *= (60 * 60 * 24 * 365)

            alert_time = int(time.time()) + wait_time_s

            db.Reminder.create(
                user_id=ctx.message.author.id,
                reminder_epoch_time=alert_time,
                reason=' '.join(args),
                message_url=ctx.message.jump_url
            )
            await ctx.channel.send(f'Will send reminder on <t:{alert_time}:f>')

    # TODO: make loop start commands generic through util function
    @commands.command()
    @commands.has_any_role(MOD_ROLE)
    async def startreminderloop(self, ctx):  # pylint: disable=unused-argument
        '''start uneject loop'''
        dm_channel = await ctx.message.author.create_dm()
        await ctx.message.delete()
        try:
            self.send_reminders.start()  # pylint: disable=no-member
            await dm_channel.send('reminder monitoring loop start')
        except RuntimeError:
            await dm_channel.send('reminder monitoring loop already started')

    @tasks.loop(seconds=60)
    async def send_reminders(self):
        '''loop through db to see when to eject someone'''
        current_time = time.time()
        with db.bot_db:
            reminders = db.Reminder.select()
            for reminder in reminders:
                if current_time > reminder.reminder_epoch_time:
                    reminded_user = await self.client.fetch_user(reminder.user_id)
                    channel = await reminded_user.create_dm()
                    embed = discord.Embed(color=discord.Colour.orange())
                    embed.set_author(name="Reminder")
                    reason = str(reminder.reason) if reminder.reason else 'No Reason Provided'
                    embed.add_field(name="Reason", value=reason)
                    embed.add_field(name="Time", value=f'<t:{reminder.reminder_epoch_time}:f>')
                    embed.add_field(name="Message link", value=str(reminder.message_url))
                    await channel.send(embed=embed)
                    reminder.delete_instance()


async def setup(client):
    '''setup'''
    await client.add_cog(RemindMe(client))
