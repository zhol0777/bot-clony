"""
break out sanitizer functions to here so that backmerging changes is less annoying between branches
"""

from typing import Tuple
from urllib.parse import urlparse

import requests
from urlextract import URLExtract

import consts
import util

# si (source identifier) is a tracking param but people kept whining
ALLOWED_PARAMS = ['t', 'variant', 'sku', 'defaultSelectionIds', 'q', 'v', 'id', 'tk', 'topic',
                  'quality', 'size', 'width', 'height', 'feature', 'p', 'l', 'board', 'c',
                  'route', 'product', 'path', 'product_id', 'idx', 'list', 'page', 'sort',
                  'iframe_url_utf8', 'si', 'gcode', 'url', 'h', 'w', 'hash', 'm', 'dl', 'th',
                  'language', 'k', 'm', 's', 'key']


DOMAINS_TO_FIX = {
    # 'www.tiktok.com': 'proxitok.pussthecat.org',
    'www.tiktok.com': 'vxtiktok.com',
    'twitter.com': 'fxtwitter.com',
    'x.com': 'fixupx.com',
    'instagram.com': 'ddinstagram.com',
    'www.instagram.com': 'ddinstagram.com'
}


WHITELISTED_DOMAINS = ['youtube.com', 'www.youtube.com', 'youtu.be', 'open.spotify.com', *DOMAINS_TO_FIX.values()]


DOMAINS_TO_REDIRECT = ['a.aliexpress.com', 'vm.tiktok.com', 'a.co']


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


def handle_redirect(url: str) -> str:
    '''redirect URLs that are hiding trackers in them'''
    if urlparse(url).netloc in DOMAINS_TO_REDIRECT:
        try:
            req = requests.get(url, headers=REDIRECT_HEADERS, timeout=10)
            if req.status_code == consts.HTTP_OK and not req.url.endswith('errors/500'):
                return req.url
        except Exception:  # pylint: disable=broad-except
            pass
    return url


def proxy_if_necessary(url: str) -> Tuple[str, bool]:
    '''
    mostly fix embeds for discord
    :return the sanitized url, bool implying whether or not to keep embed
    '''
    netloc = urlparse(url).netloc
    if netloc in DOMAINS_TO_FIX.keys():  # pylint: disable=consider-iterating-dictionary
        url = url.replace(netloc, DOMAINS_TO_FIX[netloc], 1)
        return url, True
    return url, False


def proxy_url(url: str) -> Tuple[str, bool]:
    '''
    just proxy a URL on demand
    :return: sanitized url, bool implying whether or not to keep embed
    '''
    sanitized_url = handle_redirect(url)
    sanitized_url, keep_embed = proxy_if_necessary(sanitized_url)
    return sanitized_url if sanitized_url != url else url, keep_embed


def sanitize_message(message_content: str) -> Tuple[str, bool, bool]:
    '''
    :return: Response content, needs sanitizing bool, warning suffix bool
    '''
    needs_sanitizing = False
    post_warning = False
    sanitized_msg_word_list = []

    for url in URLExtract().gen_urls(message_content):
        if urlparse(url).netloc in WHITELISTED_DOMAINS:
            continue

        sanitized_url, keep_embed = proxy_url(url)
        sanitized_url = sanitize_url(sanitized_url)
        if sanitized_url != url:
            # this was proxied, check for liveness
            if keep_embed:
                try:
                    req = requests.get(sanitized_url, timeout=10)
                except requests.exceptions.ReadTimeout:
                    continue  # he's dead jim
                if 'mp4' in req.text:
                    sanitized_msg_word_list.append(sanitized_url)
                    needs_sanitizing = True
                    post_warning = False
                    continue
            else:
                needs_sanitizing, post_warning = True, True
                sanitized_msg_word_list.append(f"<{sanitized_url}>")

    return '\n'.join(sanitized_msg_word_list), needs_sanitizing, post_warning


def sanitize_url(url: str) -> str:
    '''remove unnecessary url parameters from a url'''
    new_word = url.split('?')[0]

    # do not sanitize image embeds
    if util.is_image(new_word):
        return url

    url_params = []
    if len(url.split('?')) > 1:
        url_params = url.split('?')[1].split('&')
    if 'amazon.' in new_word:
        new_word = new_word.split('ref=')[0]
    url_params[:] = [param for param in url_params if valid_param(param)]
    if len(url_params) > 0:
        new_word = new_word + '?' + '&'.join(url_params)
    return url if url.endswith('?') else new_word


def valid_param(param: str) -> bool:
    '''checks url query parameter against hard list of valid ones'''
    for allowed_param in ALLOWED_PARAMS:
        if param.startswith(f'{allowed_param}='):
            return True
    return False
