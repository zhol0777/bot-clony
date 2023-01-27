'''
dec. 1 2022
1100 new users just joined
less than 100 have roles
these are all probably bots
time to die
'''
from collections import Counter
from datetime import datetime, date
import logging
import os
import time
import traceback

from discord.ext import commands, tasks  # type: ignore
import discord

import db
import util

log = logging.getLogger(__name__)
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
MOD_CHAT_ID = os.getenv('MOD_CHAT_ID')
DEFAULT_LIMIT = 1500
LOOP_TIME = 60
BOT_BIRTHDAY = datetime.fromordinal(date.fromisoformat('2022-09-01').toordinal())
MAX_KICKS_ALLOWED = 3
BAN_REASON = 'User is banned under suspicion of being a bot: ' \
             'Repeated server joins without passing verification'


class BotPurger(commands.Cog):
    '''kick every account younger than a month'''
    def __init__(self, client):
        self.client = client
        self.guild = None

    @commands.command()
    @commands.has_any_role(MOD_ROLE_ID)
    async def botpurge(self, ctx: commands.Context, *args):
        '''looks through past 1500 messages in the member-join-announcement channel to kick
        those suspected of being a bot'''
        if not ctx.guild:
            return
        dm_channel = await ctx.message.author.create_dm()
        status_message = await dm_channel.send("starting kicking...")
        count = 0
        message_count = 0
        botland_channel = self.client.get_channel(258268147486818304)
        if len(args) > 0:
            msg_limit = util.get_id_from_tag(args[0])
        else:
            msg_limit = DEFAULT_LIMIT
        async for message in botland_channel.history(limit=msg_limit):
            message_count += 1
            if message_count % 50 == 0:
                status_text = f'{message_count}/{msg_limit} joins analysed...'
                await status_message.edit(content=status_text)
            try:
                member = await ctx.guild.fetch_member(message.author.id)
                if member:
                    if not discord.utils.get(member.roles, name='Verified'):
                        if message.author.created_at.replace(tzinfo=None) > BOT_BIRTHDAY:
                            count += 1
                            await ctx.guild.kick(message.author)
                            with db.bot_db:
                                db.KickedUser.insert(
                                    user_id=message.author.id,
                                    kick_count=1
                                ).on_conflict(
                                    conflict_target=[db.KickedUser.user_id],
                                    update={db.KickedUser.kick_count: db.KickedUser.kick_count + 1}
                                ).execute()
            except discord.errors.NotFound:
                pass
            except Exception:  # pylint: disable=broad-except
                await util.handle_error(ctx, traceback.format_exc())
        await status_message.edit(content='BORN TO DIE\nSERVER IS A FUCK\n鬼神 Kick Em All 2022\n'
                                          f'I am trash man\n{count} KICKED BOTS')

    @commands.command()
    @commands.has_any_role(MOD_ROLE_ID)
    async def populatekickedusertable(self, ctx, *args):
        '''go through a bunch of messages and count how many times sus users have returned'''
        if not ctx.guild:
            return
        dm_channel = await ctx.message.author.create_dm()
        msg_limit = int(args[0]) if len(args) > 0 else DEFAULT_LIMIT
        status_message = await dm_channel.send("analyzing {msg_limit} joins to populate kickeduser table...")
        msg_count = 1
        arrival_counter = Counter()
        verified_user_ids = set()
        unverified_user_ids = set()
        try:
            async for message in self.client.get_channel(258268147486818304).history(limit=msg_limit):
                if message.author.id in verified_user_ids:
                    continue
                if msg_count % 50 == 0:
                    status_text = f'{msg_count}/{msg_limit} messages analysed...'
                    await status_message.edit(content=status_text)
                if message.author.created_at.replace(tzinfo=None) > BOT_BIRTHDAY:
                    msg_count += 1
                    try:
                        if message.author.id not in unverified_user_ids:
                            member = await ctx.guild.fetch_member(message.author.id)
                            if member and discord.utils.get(member.roles, name='Verified'):
                                verified_user_ids.add(message.author.id)
                                continue
                    except discord.errors.NotFound:
                        unverified_user_ids.add(message.author.id)
                    arrival_counter[message.author.id] += 1
            with db.bot_db:
                for user_id, kick_count in arrival_counter.items():
                    db.KickedUser.insert(
                        user_id=user_id,
                        kick_count=kick_count
                    ).on_conflict(
                        conflict_target=[db.KickedUser.user_id],
                        update={db.KickedUser.kick_count: max(db.KickedUser.kick_count, kick_count)}
                    ).execute()
        except Exception:  # pylint: disable=broad-except
            util.handle_error(ctx, traceback.format_exc())

    @commands.command()
    @commands.has_any_role((MOD_ROLE_ID))
    async def greatpurge(self, ctx, *args):  # pylint: disable=unused-argument
        '''ban any account that has rejoined after being kicked a certain number of times'''
        kick_limit = int(args[0]) if len(args) > 0 else DEFAULT_LIMIT
        dm_channel = await ctx.message.author.create_dm()
        status_message = await dm_channel.send(f"banning any account created after {str(BOT_BIRTHDAY)} "
                                               f"with more than {kick_limit} kicks")
        ban_count = 0
        confirmed_banned_user_ids = set()
        with db.bot_db:
            for banned_user in db.BannedUser.select():
                confirmed_banned_user_ids.add(banned_user.user_id)
            kicked_users = db.KickedUser.select().where(db.KickedUser.kick_count >= kick_limit)
            total_ban_count = kicked_users.count()
            for kicked_user in kicked_users:  # pylint: disable=not-an-iterable
                # BAN TIME
                ban_count += 1
                if ban_count % 50 == 0:
                    await status_message.edit(content=f'{ban_count}/{total_ban_count} users to ban handled')
                banned_user = await self.client.fetch_user(kicked_user.user_id)
                try:
                    await ctx.guild.fetch_ban(banned_user)
                    confirmed_banned_user_ids.add(kicked_user.user_id)
                    kicked_user.delete_instance()
                    continue
                except discord.errors.NotFound:
                    pass
                except discord.errors.Forbidden:
                    await util.handle_error(ctx, 'Bot does not have ban privilege')
                await ctx.guild.ban(banned_user, reason=BAN_REASON, delete_message_days=7)
                confirmed_banned_user_ids.add(kicked_user.user_id)
                kicked_user.delete_instance()
            db.BannedUser.insert_many(list(confirmed_banned_user_ids),
                                      fields=[db.BannedUser.user_id]).on_conflict_ignore().execute()
        await status_message.edit(content=f'{ban_count} users banned')

    @commands.command()
    @commands.has_any_role((MOD_ROLE_ID))
    async def greatpurge2(self, ctx, *args):  # pylint: disable=unused-argument,too-many-locals,too-many-branches
        '''re-attempt great purge, fewer awaits'''
        if not ctx.guild:
            return
        msg_limit = int(args[0]) if len(args) > 0 else DEFAULT_LIMIT
        arrival_counter = Counter()
        confirmed_banned_user_ids = set()
        verified_member_ids = set()
        unverified_member_ids = set()
        msg_count = 0
        with db.bot_db:
            for banned_user in db.BannedUser.select():
                confirmed_banned_user_ids.add(banned_user.user_id)
        dm_channel = await ctx.message.author.create_dm()
        status_message = await dm_channel.send(f"banning any account created after {str(BOT_BIRTHDAY)} "
                                               f"with more than {MAX_KICKS_ALLOWED} re-joins")
        async for message in self.client.get_channel(258268147486818304).history(limit=msg_limit):
            msg_count += 1
            if msg_count % 50 == 0:
                await status_message.edit(content=f'{msg_count}/{msg_limit} messages processed...')
            if message.author.id in confirmed_banned_user_ids or message.author.id in verified_member_ids:
                continue
            if message.author.created_at.replace(tzinfo=None) > BOT_BIRTHDAY:
                try:
                    await ctx.guild.fetch_ban(message.author)
                    confirmed_banned_user_ids.add(message.author.id)
                    continue  # ignore every user already banned
                except discord.errors.NotFound:
                    pass
                except discord.errors.Forbidden:
                    await util.handle_error(ctx, 'Bot does not have ban privilege')
                    return
                try:
                    if message.author.id not in unverified_member_ids:
                        member = await ctx.guild.fetch_member(message.author.id)
                        if member and discord.utils.get(member.roles, name='Verified'):
                            verified_member_ids.add(message.author.id)
                            continue
                except discord.errors.NotFound:
                    unverified_member_ids.add(message.author.id)
                arrival_counter[message.author.id] += 1
        status_message = await dm_channel.send(f"looking through {len(arrival_counter)} accounts for bans...")
        ban_count = 0
        for user_id, arrival_count in arrival_counter.items():
            if arrival_count >= MAX_KICKS_ALLOWED:
                ban_count += 1
                suspicious_user = await self.client.fetch_user(user_id)
                await ctx.guild.ban(suspicious_user, reason=BAN_REASON)
                confirmed_banned_user_ids.add(user_id)
        await status_message.edit(content=f'{ban_count} accounts banned')
        with db.bot_db:
            db.BannedUser.insert_many(
                list(confirmed_banned_user_ids),
                fields=[db.BannedUser.user_id]
            ).on_conflict_ignore().execute()
            for user_id, kick_count in arrival_counter.items():
                db.KickedUser.insert(
                    user_id=user_id,
                    kick_count=kick_count
                ).on_conflict(
                    conflict_target=[db.KickedUser.user_id],
                    update={db.KickedUser.kick_count: max(db.KickedUser.kick_count, kick_count)}
                ).execute()

    @commands.Cog.listener()
    async def on_ready(self):
        '''mostly to start task loop on bringup'''
        try:
            self.guild = await util.fetch_primary_guild(self.client)
            self.purge_loop_function.start()  # pylint: disable=no-member
        except RuntimeError:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        '''add suspiciously new account to monitoring database'''
        if member.created_at.replace(tzinfo=None) > BOT_BIRTHDAY:
            with db.bot_db:
                possibly_kicked_user = db.KickedUser.get_or_none(user_id=member.id)
                if possibly_kicked_user:
                    if possibly_kicked_user.kick_count >= MAX_KICKS_ALLOWED:
                        await member.ban(reason=BAN_REASON)
                        possibly_kicked_user.delete_instance()
                        return
                db.SuspiciousUser.create(
                    user_id=member.id,
                    join_epoch_time=int(time.time())
                )

    @tasks.loop(seconds=LOOP_TIME)
    async def purge_loop_function(self):
        '''iterate through db of suspicious users and delete monitoring if they verify, kick if not'''
        current_time = int(time.time())
        with db.bot_db:
            suspicious_users = db.SuspiciousUser.select()
            for s_u in suspicious_users:
                if (current_time - s_u.join_epoch_time) < 1200:
                    continue
                try:
                    user_to_kick = await self.guild.fetch_member(s_u.user_id)
                    if discord.utils.get(user_to_kick.roles, name='Verified'):
                        s_u.delete_instance()
                        continue
                    try:
                        with db.bot_db:
                            db.KickedUser.insert(
                                user_id=user_to_kick.id,
                                kick_count=1
                            ).on_conflict(
                                conflict_target=[db.KickedUser.user_id],
                                update={db.KickedUser.kick_count: db.KickedUser.kick_count + 1}
                            ).execute()
                            if db.KickedUser.get_or_none(user_id=user_to_kick.id).kick_count >= MAX_KICKS_ALLOWED:
                                await user_to_kick.ban(reason=BAN_REASON)
                            else:
                                await user_to_kick.kick(reason="Account is suspiciously young, "
                                                               "not verifying within 15 minutes")
                    except discord.errors.NotFound:
                        pass
                except Exception:  # pylint: disable=broad-except
                    pass
                s_u.delete_instance()


async def setup(client):
    '''setup'''
    await client.add_cog(BotPurger(client))
