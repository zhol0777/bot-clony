'''
Listeners for events that deserve moderation
'''
import os

from discord.ext import commands

import db
import util

MOD_CHAT_CHANNEL_NAME = os.getenv('MOD_CHAT')


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


async def setup(client):
    '''setup'''
    await client.add_cog(ModListeners(client))
