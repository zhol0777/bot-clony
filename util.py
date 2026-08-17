'''
Utility functions shared across cogs
'''
import hashlib
import logging
import os
from mimetypes import guess_type
from typing import Optional, Union

import discord
from discord.ext import commands
from PIL.Image import registered_extensions

import db

log = logging.getLogger(__name__)

IGNORE_COMMAND_LIST = [
    'purge', 'purgelast', 'buy', 'eight', 'eject', 'google', 'groupbuy',
    'northfacing', 'oos', 'pins', 'spraylubing', 'vendors', 'fakelifealert',
    'lifealert', 'trade', 'vote', 'flashsales', 'help', 'rk61', ''
]

MECHMARKET_SCRAPE_HEADERS = {
    'authority': 'www.reddit.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,'
              'image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
}

_HASH_SALT: str | None = None


def _get_salt() -> str:
    global _HASH_SALT  # noqa: PLW0603
    if _HASH_SALT is None:
        _HASH_SALT = os.getenv('HASH_SALT', '')
    return _HASH_SALT


def hash_user_id(user_id: int) -> str:
    '''One-way SHA-256 hash of a user ID with a secret salt.'''
    return hashlib.sha256(f"{user_id}{_get_salt()}".encode()).hexdigest()


def is_opted_out(user_id: int) -> bool:
    '''Check if a user has opted out of sticky role / social credit tracking.'''
    hashed = hash_user_id(user_id)
    with db.bot_db:
        return db.OptOut.get_or_none(hashed_user_id=hashed) is not None


def supported_image_extensions() -> set[str]:
    '''
    this takes a second to run as pillow inits, caching out of paranoia
    '''
    return set(registered_extensions().keys())


def is_image(uri: str) -> bool:
    '''see if a URI directs to an image'''
    possible_ext = os.path.splitext(uri)[1].lower()
    try:
        if possible_ext and possible_ext in supported_image_extensions():
            return True
    except KeyError:
        pass
    return False


def is_video(uri: str) -> bool:
    '''see if a URI contains a video'''
    if guess := guess_type(uri)[0]:
        return 'video' in guess
    return False


def get_id_from_tag(tag: str) -> int:
    '''Convert <@2823848929872937942> to a regular ID'''
    return int(''.join([char for char in list(tag) if char.isdigit()]))


async def get_reply_message(message: discord.Message) -> discord.Message:
    '''Find the message that bot will reply to later'''
    if message.reference is not None and message.reference.message_id:
        message = await message.channel.fetch_message(message.reference.message_id)
    return message


# TODO: handle via role IDs
async def apply_role(member: discord.Member | discord.User, user_id: int,  # noqa: PLR0913,PLR0917
                     guild: discord.Guild, role_name: str, reason: Optional[str] = None,
                     enter_in_db: bool = True) -> None:
    '''Apply a role to a member, and mark it in db with hashed user ID'''
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        log.error("Cannot apply non-existent role %s", role_name)
        return
    # sometimes the user has bailed before role can be applied - we still log in db
    # in case they decide to come back
    if enter_in_db:
        if not is_opted_out(user_id):
            with db.bot_db:
                db.RoleAssignment.get_or_create(
                    hashed_user_id=hash_user_id(user_id),
                    role_name=role_name
                )
    if isinstance(member, discord.Member):
        await member.add_roles(role, reason=reason)


# TODO: handle via role IDs
async def remove_role(member: discord.Member, user_id: int,
                      role_name: str) -> None:
    '''Remove a role from a member, and remove it from db'''
    role = discord.utils.get(member.guild.roles, name=role_name)
    await member.remove_roles(role)  # ty: ignore[invalid-argument-type]
    with db.bot_db:
        db.RoleAssignment.delete().where(
            (db.RoleAssignment.hashed_user_id == hash_user_id(user_id)) &
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
        return bool(discord.utils.get(author.roles, id=role_id))  # ty: ignore[no-matching-overload]
    return False
