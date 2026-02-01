'''
Listeners for events that deserve moderation
'''
import logging
import sys
import traceback
from typing import Any
from urllib.parse import urljoin

from discord.ext import commands

import db
import util

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class ModListeners(commands.Cog):
    '''Cog to provide very generic accounts'''
    def __init__(self, client):
        self.client = client

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


async def setup(client):
    '''setup'''
    await client.add_cog(ModListeners(client))
