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

import db

IGNORE_COMMAND_LIST = [
    'purge', 'purgelast', 'buy', 'eight', 'eject', 'google', 'groupbuy',
    'northfacing', 'oos', 'pins', 'spraylubing', 'vendors', 'fakelifealert',
    'lifealert', 'trade', 'vote', 'flashsales', 'help', 'rk61', ''
]

# si (source identifier) is a tracking param but people kept whining
ALLOWED_PARAMS = ['t', 'variant', 'sku', 'defaultSelectionIds', 'q', 'v', 'id', 'tk', 'topic',
                  'quality', 'size', 'width', 'height', 'feature', 'p', 'l', 'board', 'c',
                  'route', 'product', 'path', 'product_id', 'idx', 'list', 'page', 'sort',
                  'iframe_url_utf8', 'si', 'gcode', 'url', 'h', 'w', 'hash', 'm', 'dl', 'th',
                  'language', ]


DOMAINS_TO_FIX = {
    # 'www.tiktok.com': 'proxitok.pussthecat.org',
    'www.tiktok.com': 'vxtiktok.com',
    'twitter.com': 'fxtwitter.com',
    'x.com': 'fixupx.com',
    'instagram.com': 'ddinstagram.com',
    'www.instagram.com': 'ddinstagram.com'
}

DOMAINS_TO_REDIRECT = ['a.aliexpress.com', 'vm.tiktok.com', 'a.co']

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

REDIRECT_HEADERS = {
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
    img_extensions = {k for k, v in mimetypes.types_map.items() if 'image' in v}
    try:
        if possible_ext and possible_ext in img_extensions:
            return True
    except KeyError:
        pass
    return False


def sanitize_word(word: str) -> str:
    '''remove unnecessary url parameters from a url'''
    new_word = word.split('?')[0]

    # do not sanitize image embeds
    if is_image(new_word):
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
                req = requests.get(url, headers=REDIRECT_HEADERS, timeout=10)
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
                query = db.RoleAssignment.select().where(
                    (db.RoleAssignment.user_id == user_id) &
                    (db.RoleAssignment.role_name == role_name)
                )
                if not query.exists():
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
