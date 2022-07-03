'''
Listeners for events that deserve moderation
'''
import os

from discord.ext import commands
import discord

import db
import util

MOD_CHAT_CHANNEL_NAME = os.getenv('MOD_CHAT')
VERIFIED_ROLE_NAME = os.getenv('VERIFIED_ROLE_NAME')
VERIFICATION_CHANNEL_NAME = os.getenv('VERIFICATION_CHANNEL_NAME')
VERIFICATION_PW = os.getenv('VERIFICATION_PW')
NO_NO_WORD_LIST = os.getenv('NO_NO_WORD_LIST', '').split(',')
REGION_ROLE_MESSAGE_REACTION_ID = os.getenv('REGION_ROLE_MESSAGE_REACTION_ID')

REGION_ROLE_DICT = {
    '!US': 'United States',
    '!CAN': 'Canada',
    '!MEXICO': 'Mexico',
    '!SA': 'Central/South America',
    '!EU': 'Europe',
    '!UK': 'UK',
    '!OCE': 'Oceania',
    '!ASIA': 'Asia',
    '!SEA': 'South East Asia',
    '!ME': 'Middle East',
    '!AFRICA': 'Africa'
}


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
    async def on_message(self, message):
        '''verify users, check for no-no words, apply region roles'''
        # verification
        if message.channel.name == VERIFICATION_CHANNEL_NAME:
            if message.content == VERIFICATION_PW:
                verified_member = \
                    await message.author.guild.fetch_member(message.author.id)
                await util.apply_role(verified_member, message.author.id,
                                      VERIFIED_ROLE_NAME, enter_in_db=False)
                return

        # region role channel
        if message.channel.name == 'region-roles':
            region_role = REGION_ROLE_DICT.get(message.content)
            if region_role:
                member = \
                    await message.author.guild.fetch_member(message.author.id)
                await util.apply_role(member, message.author.id, region_role,
                                      enter_in_db=False)
                return

        # ping modchat for no-no words
        for word in NO_NO_WORD_LIST:
            mod_chat_channel = discord.utils.get(message.author.guild.channels,
                                                 name=MOD_CHAT_CHANNEL_NAME)
            if word in message.content:
                embed = discord.Embed(colour=discord.Colour.red())
                embed.set_author(name="No-No Word Watch")
                embed.add_field(name="Author", value=message.author)
                embed.add_field(name="Message", value=message.content)
                embed.add_field(name="Word Matched", value=word)
                embed.add_field(name="Channel", value=message.channel.name)
                embed.add_field(name="Link", value=message.jump_url)
                await mod_chat_channel.send(embed=embed)
                return


def setup(client):
    '''setup'''
    client.add_cog(ModListeners(client))
