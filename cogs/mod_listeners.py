'''
Listeners for events that deserve moderation
'''
import logging
import sys
import traceback
from typing import Any

from discord.ext import commands

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
                _ = ctx.message.content.strip(self.client.command_prefix).split()[0]
            except IndexError:
                return  # message with single exclamation mark or whatever prefix you use
            return
            log.exception('Exception in command %s:', ctx.command)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


async def setup(client):
    '''setup'''
    await client.add_cog(ModListeners(client))
