'''
analyze who get channel lockdown role
'''
from collections import Counter
import logging
import os
import traceback

from discord.ext import commands  # type: ignore

import util

log = logging.getLogger(__name__)
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))


class RegularAnalyzer(commands.Cog):
    '''see whos a regular'''
    def __init__(self, client):
        self.client = client
        self.guild = None

    @commands.command()
    @commands.has_any_role(MOD_ROLE_ID)
    async def reganalyze(self, ctx: commands.Context):
        '''sees whos active in customs'''
        if not ctx.guild:
            return
        dm_channel = await ctx.message.author.create_dm()
        await dm_channel.send("analyzing...")
        botland_channel = self.client.get_channel(719746702986313738)
        msg_limit = 38000
        count_index: Counter = Counter()
        async for message in botland_channel.history(limit=msg_limit):
            try:
                full_username = f'{message.author.name}#{message.author.discriminator}'
                count_index[full_username] += 1

            except Exception:  # pylint: disable=broad-except
                await util.handle_error(ctx, traceback.format_exc())
        for item_combo in sorted(count_index.items(), key=lambda i: i[1], reverse=True):
            await dm_channel.send(str(item_combo))


async def setup(client):
    '''setup'''
    await client.add_cog(RegularAnalyzer(client))
