'''
Listeners for events that deserve moderation
'''
from urllib.parse import urljoin
import logging
import os
import sys
import traceback

from discord.ext import commands

import db
import util

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
MOD_CHAT_CHANNEL_NAME = os.getenv('MOD_CHAT')
# TODO: handle via role IDs
MONITORED_ROLES = ['ejected', 'evicted', 'deported', 'Razer Hate']


class ModListeners(commands.Cog):
    '''Cog to provide very generic accounts'''
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        '''mostly reapply roles to returning users'''
        with db.bot_db:
            former_role_assignments = db.RoleAssignment.select().where(
                db.RoleAssignment.user_id == member.id
            )
            # pylint: disable=not-an-iterable
            for r_a in former_role_assignments:
                await util.apply_role(member, member.id, r_a.role_name)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        '''mostly for eject role monitoring, can be expanded to other roles'''

        removed_roles = set(before.roles) - set(after.roles)
        added_roles = set(after.roles) - set(before.roles)
        # TODO: handle via role IDs
        with db.bot_db:
            for role in removed_roles:
                if role.name in MONITORED_ROLES:
                    db.RoleAssignment.delete().where(
                        (db.RoleAssignment.user_id == after.id) &
                        (db.RoleAssignment.role_name == role.name)
                    ).execute()
            for role in added_roles:
                if role.name in MONITORED_ROLES:
                    db.RoleAssignment.create(
                        user_id=after.id,
                        role_name=role.name
                    )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):  # pylint: disable=unused-argument
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
            command = ctx.message.content.strip(self.client.command_prefix)
            # avoid running with bot-sony
            if command in util.BOT_SONY_COMMAND_LIST:
                return
            with db.bot_db:
                wiki_page = db.WikiPage.get_or_none(shortname=command)
                if not wiki_page:
                    return
                if wiki_page.goes_to_root_domain:
                    wiki_domain = db.WikiRootUrl.get_or_none(indicator='primary')
                    if not wiki_domain:
                        return
                    url = urljoin(wiki_domain.domain, wiki_page.page)
                    await ctx.channel.send(f"{url}")
                else:
                    await ctx.channel.send(wiki_page.page)
            return
        log.exception('Exception in command %s:', ctx.command)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


async def setup(client):
    '''setup'''
    await client.add_cog(ModListeners(client))
