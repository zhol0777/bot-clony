'''
Listeners for events that deserve moderation
'''
import logging
import os
import sys
import traceback
from typing import Any
from urllib.parse import urljoin

import discord
from discord.ext import commands

from cogs.verify import VERIFY_CHANNEL_ID, REGION_ROLE_CHANNEL_ID
import db
import util

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
MOD_CHAT_ID = int(os.getenv('MOD_CHAT_ID', '0'))
DELETED_MESSAGE_CHANNEL_ID = int(os.getenv('DELETED_MESSAGE_CHANNEL_ID', '0'))
# TODO: handle via role IDs
MONITORED_ROLES = ['ejected', 'evicted', 'deported', 'Razer Hate', 'embed fail']


class ModListeners(commands.Cog):
    '''Cog to provide very generic accounts'''
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        '''mostly reapply roles to returning users'''
        # finlacoin compromised accounts
        if member.display_name.lower() == 'finlacoin':
            channel = self.client.get_channel(MOD_CHAT_ID)
            await channel.send("finlacoin account detected, please check #botland")

        if util.is_opted_out(member.id):
            return

        with db.bot_db:
            former_role_assignments = db.RoleAssignment.select().where(
                db.RoleAssignment.hashed_user_id == util.hash_user_id(member.id)
            )
            # pylint: disable=not-an-iterable
            for r_a in former_role_assignments:
                await util.apply_role(member, member.id, member.guild, r_a.role_name,
                                      enter_in_db=False)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        '''mostly for eject role monitoring, can be expanded to other roles'''

        removed_roles = set(before.roles) - set(after.roles)
        added_roles = set(after.roles) - set(before.roles)

        if util.is_opted_out(after.id):
            with db.bot_db:
                for role in removed_roles:
                    if role.name in MONITORED_ROLES:
                        db.RoleAssignment.delete().where(
                            (db.RoleAssignment.hashed_user_id == util.hash_user_id(after.id)) &
                            (db.RoleAssignment.role_name == role.name)
                        ).execute()
            return

        with db.bot_db:
            for role in removed_roles:
                if role.name in MONITORED_ROLES:
                    db.RoleAssignment.delete().where(
                        (db.RoleAssignment.hashed_user_id == util.hash_user_id(after.id)) &
                        (db.RoleAssignment.role_name == role.name)
                    ).execute()
            for role in added_roles:
                if role.name in MONITORED_ROLES:
                    db.RoleAssignment.create(
                        hashed_user_id=util.hash_user_id(after.id),
                        role_name=role.name
                    )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Any):
        '''
        quiet logging on any cmd that doesn't exist or is handled elsewhere
        cribbed from https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612
        '''
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound, )
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            # may be possible to just reference wiki page
            # TODO: a lot of this is just copied-pasted from cogs/wiki.py, should
            # be made more modular
            try:
                command = ctx.message.content.strip(self.client.command_prefix).split()[0]
            except IndexError:
                return  # message with single exclamation mark or whatever prefix you use
            # avoid running with bot-sony
            if command in util.IGNORE_COMMAND_LIST:
                return
            if ctx.channel.id in {VERIFY_CHANNEL_ID, REGION_ROLE_CHANNEL_ID}:  # ignore region role, verify channels
                return
            with db.bot_db:
                if wiki_page := db.WikiPage.get_or_none(shortname=command):
                    if wiki_page.goes_to_root_domain:
                        wiki_domain = db.WikiRootUrl.get_or_none(indicator='primary')
                        if not wiki_domain:
                            return
                        url = urljoin(wiki_domain.domain, wiki_page.page)
                        await ctx.channel.send(f"{url}")
                    else:
                        await ctx.channel.send(wiki_page.page)
                if silly_page := db.SillyPage.get_or_none(shortname=command):
                    await ctx.channel.send(silly_page.response_text)
            return
        log.exception('Exception in command %s:', ctx.command)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_deleted_message_channel(self) -> discord.TextChannel | None:
        '''Resolve the deleted-message log channel lazily, since the cache is
        not populated when the cog is loaded.'''
        channel = self.client.get_channel(DELETED_MESSAGE_CHANNEL_ID)
        if not channel:
            log.error("DELETED_MESSAGE_CHANNEL_ID is not set or channel not found!")
            return
        if not isinstance(channel, discord.TextChannel):
            log.error("Deleted message channel should be a TextChannel, not %s", type(channel))
            return
        return channel

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        '''Log edited messages to the mod log channel'''
        if before.content == after.content:
            # embed unfurls, pins, etc. - nothing the user typed has changed
            return
        channel = self.get_deleted_message_channel()
        if not channel:
            return
        embed = discord.Embed(
            title="Edited Message",
            color=discord.Color.blue()
        )
        embed.add_field(name="User", value=f'<@{before.author.id}>')
        embed.add_field(name="ID", value=before.author.id)
        embed.add_field(name="Time", value=f'<t:{int(discord.utils.utcnow().timestamp())}:t>')
        embed.add_field(name="Message Before",
                        value=util.truncate_for_embed(before.clean_content or "NO MESSAGE"))
        embed.add_field(name="Message After",
                        value=util.truncate_for_embed(after.clean_content or "NO MESSAGE"))
        embed.add_field(name="Has Attachments", value=bool(before.attachments))
        embed.add_field(name="Jump Link", value=before.jump_url)
        after_urls = {at.url for at in after.attachments}
        attachments = ' '.join(
            attachment.url for attachment in before.attachments if attachment.url not in after_urls)
        await channel.send(content=attachments or None, embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        '''Log deleted messages to the mod log channel'''
        channel = self.get_deleted_message_channel()
        if not channel:
            return
        if message.channel.id in {VERIFY_CHANNEL_ID, REGION_ROLE_CHANNEL_ID}:  # ignore region role, verify channels
            return
        embed = discord.Embed(
            title="Deleted Message",
            color=discord.Color.red()
        )
        embed.add_field(name="User", value=f'<@{message.author.id}>')
        embed.add_field(name="ID", value=message.author.id)
        embed.add_field(name="Time", value=f'<t:{int(discord.utils.utcnow().timestamp())}:t>')
        embed.add_field(name="Message Content",
                        value=util.truncate_for_embed(message.clean_content or "NO MESSAGE"))
        embed.add_field(name="Jump Link", value=message.jump_url)
        attachments = ' '.join(attachment.url for attachment in message.attachments)
        await channel.send(content=attachments or None, embed=embed)


async def setup(client):
    '''setup'''
    await client.add_cog(ModListeners(client))
