'''
Utility functions shared across cogs
'''
from typing import Any, Tuple, Optional, Union
import os

from discord.ext import commands
import validators
import discord

import db

IGNORE_COMMAND_LIST = [
    'purge', 'purgelast', 'buy', 'eight', 'eject', 'google', 'groupbuy',
    'northfacing', 'oos', 'pins', 'spraylubing', 'vendors', 'fakelifealert',
    'lifealert', 'trade', 'vote', 'flashsales', 'help', 'rk61'
]

ALLOWED_PARAMS = ['t', 'variant', 'sku', 'defaultSelectionIds', 'q', 'v', 'id', 'tk', 'topic']


def sanitize_message(args: Any) -> Tuple[str, bool]:
    '''
    :return: Message with every URL sanitized if necessary
    '''
    needs_sanitizing = False
    msg = ''.join(args).split()
    sanitized_msg_word_list = []

    for word in msg:
        if validators.url(word):
            sanitized_word = sanitize_word(word)
            if sanitized_word != word:
                needs_sanitizing = True
            sanitized_msg_word_list.append(sanitized_word)
        else:
            sanitized_msg_word_list.append(word)
    return ' '.join(sanitized_msg_word_list), needs_sanitizing


def sanitize_word(word: str) -> str:
    '''remove unnecessary url parameters from a url'''
    new_word = word.split('?')[0]
    url_params = []
    if len(word.split('?')) > 1:
        url_params = word.split('?')[1].split('&')
    if 'amazon.' in new_word:
        new_word = new_word.split('ref=')[0]
    for param in url_params:
        for allowed_param in ALLOWED_PARAMS:
            if param.startswith(f'{allowed_param}='):
                if not new_word.endswith('?'):
                    new_word += '?'
                new_word = f'{new_word}{param}'
    # TODO: domain specific sanitizing to retain necessary params, like ex. google
    if word != new_word and (word.endswith('?') or (len(url_params) == 1)):
        return word
    return new_word


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


async def get_reply_message(message: discord.Message) -> discord.Message:
    '''Find the message that bot will reply to later'''
    if message.reference is not None and message.reference.message_id:
        message = await message.channel.fetch_message(message.reference.message_id)
    return message


# TODO: handle via role IDs
async def apply_role(member: discord.Member, user_id: int,
                     role_name: str, reason: Optional[str] = None,
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


async def handle_error(ctx: commands.Context, error_message: Optional[str]):
    '''send an error message to a user when they misuse a command'''
    if error_message:
        channel = await ctx.message.author.create_dm()
        await channel.send(error_message)
        await ctx.message.delete()


async def fetch_primary_guild(client: discord.Client):
    '''get the guild the bot is supposed to be running on primarily'''
    guild_id = int(os.getenv('SERVER_ID', '0'))
    guild = await client.fetch_guild(guild_id, with_counts=False)
    if guild:
        return guild


def user_has_role_from_id(author: Union[discord.Member, discord.abc.User],
                          role_id: int) -> bool:
    '''determine if message author has corresponding role ID'''
    if hasattr(author, 'roles'):
        return bool(discord.utils.get(author.roles, id=role_id))
    return False
