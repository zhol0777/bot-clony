'''
Utility functions shared across cogs
'''
import os
from typing import Optional, Union

import discord
from discord.ext import commands
from PIL.Image import registered_extensions


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


async def get_reply_message(message: discord.Message) -> discord.Message:
    '''Find the message that bot will reply to later'''
    if message.reference is not None and message.reference.message_id:
        message = await message.channel.fetch_message(message.reference.message_id)
    return message


async def handle_error(ctx: commands.Context, error_message: Optional[str]):
    '''send an error message to a user when they misuse a command'''
    if error_message:
        channel = await ctx.message.author.create_dm()
        await channel.send(error_message)
        await ctx.message.delete()


def user_has_role_from_id(author: Union[discord.Member, discord.abc.User],
                          role_id: int) -> bool:
    '''determine if message author has corresponding role ID'''
    if hasattr(author, 'roles'):
        return bool(discord.utils.get(author.roles, id=role_id))
    return False
