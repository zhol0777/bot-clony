'''
dec. 1 2022
1100 new users just joined
less than 100 have roles
these are all probably bots
time to die
'''
from datetime import datetime, timedelta
import asyncio
import logging
import os

from discord.ext import commands
import discord

log = logging.getLogger(__name__)
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
MOD_CHAT_ID = os.getenv('MOD_CHAT_ID')
LIMIT = 1500


class BotPurger(commands.Cog):
    '''kick every account younger than a month'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(MOD_ROLE_ID)
    async def botpurge(self, ctx: commands.Context):
        '''looks through past 1500 messages in the member-join-announcement channel to kick
        those suspected of being a bot'''
        if not ctx.guild:
            return
        dm_channel = await ctx.message.author.create_dm()
        status_message = await dm_channel.send("starting kicking...")
        count = 0
        message_count = 0
        botland_channel = self.client.get_channel(258268147486818304)
        async for message in botland_channel.history(limit=LIMIT):
            message_count += 1
            if message_count % 50 == 0:
                status_text = f'{message_count}/{LIMIT} joins analysed...'
                await status_message.edit(content=status_text)
            account_age = datetime.today() - message.author.created_at.replace(tzinfo=None)
            try:
                member = await ctx.guild.fetch_member(message.author.id)
                if member:
                    if not discord.utils.get(member.roles, name='Verified'):
                        if account_age < timedelta(days=62):
                            count += 1
                            await ctx.guild.kick(message.author)
            except discord.errors.NotFound:
                pass
            except Exception:  # pylint: disable=broad-except
                log.exception("something went wrong here")
        await status_message.edit(content='BORN TO DIE\nSERVER IS A FUCK\n鬼神 Kick Em All 2022\n'
                                          f'I am trash man\n{count} KICKED BOTS')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        '''kick suspiciously new account if it cannot verify within 30 minutes'''
        account_age = datetime.today() - member.created_at.replace(tzinfo=None)
        if account_age < timedelta(days=62):
            await asyncio.sleep(1200)
            if not discord.utils.get(member.roles, name='Verified'):
                await member.kick(reason="Account is suspiciously young, not verifying within 1 hour")


async def setup(client):
    '''setup'''
    await client.add_cog(BotPurger(client))
