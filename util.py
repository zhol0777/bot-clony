'''
Utility functions shared across cogs
'''
from typing import Any, Tuple, Optional, Union
from urllib.parse import urlparse
import mimetypes
import os

from discord.ext import commands
import validators
import requests
import discord

# si (source identifier) is a tracking param but people kept whining
ALLOWED_PARAMS = ['t', 'variant', 'sku', 'defaultSelectionIds', 'q', 'v', 'id', 'tk', 'topic',
                  'quality', 'size', 'width', 'height', 'feature', 'p', 'l', 'board', 'c',
                  'route', 'product', 'path', 'product_id', 'idx', 'list', 'page', 'sort',
                  'iframe_url_utf8', 'si', 'gcode', 'url', 'h', 'w', 'hash', 'm']


DOMAINS_TO_FIX = {
    # 'www.tiktok.com': 'proxitok.pussthecat.org',
    'www.tiktok.com': 'vxtiktok.com',
    'twitter.com': 'fxtwitter.com',
    'x.com': 'fixupx.com',
    # 'instagram.com': 'ddinstagram.com',
    # 'www.instagram.com': 'ddinstagram.com'
}

DOMAINS_TO_REDIRECT = ['a.aliexpress.com', 'vm.tiktok.com', 'a.co']

SCRAPE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Dnt": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
}

mimetypes.init()


def proxy_url(url: str) -> Tuple[str, bool]:
    '''
    just proxy a URL on demand
    :return: sanitized url, bool implying whether or not to keep embed
    '''
    sanitized_url = handle_redirect(url)
    sanitized_url, keep_embed = proxy_if_necessary(sanitized_url)
    return sanitized_url if sanitized_url != url else url, keep_embed


def sanitize_message(args: Any) -> Tuple[str, bool, bool]:
    '''
    :return: Message with every URL sanitized if necessary
    '''
    needs_sanitizing = False
    post_warning = True
    msg = ''.join(args).split()
    sanitized_msg_word_list = []

    for word in msg:
        # remove carats that disable embed but can also stop url from
        # being recognized as link
        if word.startswith('<') and word.endswith('>'):
            word = word[1:-1]
        if validators.url(word):
            sanitized_url = handle_redirect(word)
            sanitized_url, keep_embed = proxy_url(sanitized_url)
            sanitized_url = sanitize_word(sanitized_url)
            if sanitized_url != word:
                needs_sanitizing = True
                if not keep_embed:
                    sanitized_msg_word_list.append(f"<{sanitized_url}>")
                else:
                    sanitized_msg_word_list.append(sanitized_url)
                    post_warning = False
        # else:
        #     sanitized_msg_word_list.append(word)
    return '\n'.join(sanitized_msg_word_list), needs_sanitizing, post_warning


def is_image(uri: str) -> bool:
    '''see if a URI directs to an image'''
    possible_ext = os.path.splitext(uri)[1].lower()
    try:
        if possible_ext and mimetypes.types_map[possible_ext].startswith('image'):
            return True
    except KeyError:
        pass
    return False


def sanitize_word(word: str) -> str:
    '''remove unnecessary url parameters from a url'''
    new_word = word.split('?')[0]

    # do not sanitize image embeds
    if is_image(word):
        return word

    url_params = []
    if len(word.split('?')) > 1:
        url_params = word.split('?')[1].split('&')
    if 'amazon.' in new_word:
        new_word = new_word.split('ref=')[0]
    url_params[:] = [param for param in url_params if valid_param(param)]
    if len(url_params) > 0:
        new_word = new_word + '?' + '&'.join(url_params)
    return word if word.endswith('?') else new_word


def handle_redirect(url: str) -> str:
    '''redirect URLs that are hiding trackers in them'''
    try:
        for domain in DOMAINS_TO_REDIRECT:
            if domain == urlparse(url).netloc:
                req = requests.get(url, headers=SCRAPE_HEADERS, timeout=10)
                if req.status_code == 200 and not req.url.endswith('errors/500'):
                    return req.url
    except Exception:  # pylint: disable=broad-except
        pass
    return url


def proxy_if_necessary(url: str) -> Tuple[str, bool]:
    '''
    mostly fix embeds for discord
    :return the sanitized url, bool implying whether or not to keep embed
    '''
    for bad_domain, better_domain in DOMAINS_TO_FIX.items():
        if urlparse(url).netloc == bad_domain:
            url = url.replace(bad_domain, better_domain, 1)
            return url, True
    return url, False


def valid_param(param: str) -> bool:
    '''checks url query parameter against hard list of valid ones'''
    for allowed_param in ALLOWED_PARAMS:
        if param.startswith(f'{allowed_param}='):
            return True
    return False


# TODO: deprecate
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
