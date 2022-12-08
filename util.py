'''
Utility functions shared across cogs
'''
from typing import Any, Tuple
import os

from discord.ext import commands
import validators
import discord

import db

BOT_SONY_COMMAND_LIST = [
    'purge', 'purgelast', 'buy', 'eight', 'eject', 'google', 'groupbuy',
    'northfacing', 'oos', 'pins', 'spraylubing', 'vendors', 'fakelifealert',
    'lifealert', 'trade', 'vote', 'flashsales', 'help', 'rk61'
]


def sanitize_message(args: Any) -> Tuple[str, bool]:
    '''
    :return: Message with every URL sanitized if necessary
    '''
    needs_sanitizing = False
    msg = ''.join(args).split()
    sanitized_msg_word_list = []

    for word in msg:
        if validators.url(word):
            new_word = word.split('?')[0]
            if 'aliexpress' in new_word and \
                    not new_word.startswith('https://www.aliexpress.com'):
                new_word = aliexpress_sanitize(new_word)
            if word != new_word:
                needs_sanitizing = True
                sanitized_msg_word_list.append(f'<{new_word}>')
            else:
                sanitized_msg_word_list.append(f'<{word}>')
        else:
            sanitized_msg_word_list.append(word)
    return ' '.join(sanitized_msg_word_list), needs_sanitizing


def aliexpress_sanitize(url: str) -> str:
    '''
    Convert bogus aliexpress url (which already has URL params *stripped*)
    https://aliexpress.ru/item/424380923490234098324.html or
    https://it.aliexpress.com/item/gabagoolmammamia.html
    to:
    https://www.aliexpress.com/item/3292032903290.html
    to prevent anyone who clicks on a link from having their language settings
    changed
    '''
    stripped_id = get_id_from_tag(url)
    return f'https://www.aliexpress.com/item/{stripped_id}.html'


def get_id_from_tag(tag: str) -> int:
    '''Convert <@2823848929872937942> to a regular ID'''
    return int(''.join([char for char in list(tag) if char.isdigit()]))


async def get_reply_message(ctx, original) -> discord.Message:
    '''Find the message that bot will reply to later'''
    if ctx.message.reference is not None:
        original = await ctx.fetch_message(ctx.message.reference.message_id)
    return original


# TODO: handle via role IDs
async def apply_role(member: discord.Member, user_id: int,
                     role_name: str, reason: str = None,
                     enter_in_db: bool = True) -> None:
    '''Apply a role to a member, and mark it in db'''
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role:
        await member.add_roles(role, reason=reason)
        if enter_in_db:
            with db.bot_db:
                db.RoleAssignment.create(
                    user_id=user_id,
                    role_name=role_name
                )


# TODO: handle via role IDs
async def remove_role(member: discord.Member, user_id: int,
                      role_name: str) -> None:
    '''Remove a role from a member, and remove it from db'''
    role = discord.utils.get(member.guild.roles, name=role_name)
    await member.remove_roles(role)  # type: ignore
    with db.bot_db:
        db.RoleAssignment.delete().where(
            (db.RoleAssignment.user_id == user_id) &
            (db.RoleAssignment.role_name == role_name)
        ).execute()


async def handle_error(ctx: commands.Context, error_message: str):
    '''send an error message to a user when they misuse a command'''
    channel = await ctx.message.author.create_dm()
    await channel.send(error_message)
    await ctx.message.delete()


async def get_guild(ctx: commands.Context, client):
    '''get primary guild needed by a cog based on OS environment'''
    dm_channel = await ctx.message.author.create_dm()
    try:
        await ctx.message.delete()
    except discord.errors.Forbidden:
        pass
    for guild in client.guilds:
        if guild.id == int(os.getenv('SERVER_ID', '0')):
            return guild, dm_channel
