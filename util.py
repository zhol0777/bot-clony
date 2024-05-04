'''
Utility functions shared across cogs
'''

from functools import cache
import os

from discord.ext import commands
from PIL.Image import registered_extensions

ALLOWED_PARAMS = ['t', 'variant', 'sku', 'defaultSelectionIds', 'q', 'v', 'id', 'tk', 'topic',
                  'quality', 'size', 'width', 'height', 'feature', 'p', 'l', 'board', 'c',
                  'route', 'product', 'path', 'product_id', 'idx', 'list', 'page', 'sort']


async def handle_error(ctx: commands.Context, error_message: str):
    '''send an error message to a user when they misuse a command'''
    channel = await ctx.message.author.create_dm()
    await channel.send(error_message)
    await ctx.message.delete()


def sanitize_word(word: str) -> str:
    '''remove unnecessary url parameters from a url'''
    new_word = word.split('?')[0]
    url_params = []
    if len(word.split('?')) > 1:
        url_params = word.split('?')[1].split('&')
    if 'amazon.' in new_word:
        new_word = new_word.split('ref=')[0]
    url_params[:] = [param for param in url_params if valid_param(param)]
    if len(url_params) > 0:
        new_word = new_word + '?' + '&'.join(url_params)
    return word if word.endswith('?') else new_word


def valid_param(param: str) -> bool:
    '''checks url query parameter against hard list of valid ones'''
    for allowed_param in ALLOWED_PARAMS:
        if param.startswith(f'{allowed_param}='):
            return True
    return False


@cache
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
