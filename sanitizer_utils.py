"""
break out sanitizer functions to here so that backmerging changes is less annoying between branches
"""

import logging
import os
import pickle
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from urlextract import URLExtract

import consts
import util

ALLOWED_PARAMS_FILE = os.getenv('ALLOWED_PARAMS_FILE', '')
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# si (source identifier) is a tracking param but people kept whining
ALLOWED_PARAMS = {
    "board",
    "c",
    "defaultSelectionIds",
    "dl",
    "feature",
    "gcode",
    "h",
    "hash",
    "height",
    "id",
    "idx",
    "iframe_url_utf8",
    "k",
    "key",
    "l",
    "language",
    "list",
    "m",
    "p_id",
    "p",
    "page",
    "path",
    "product_id",
    "product",
    "q",
    "quality",
    "route",
    "s",
    "si",
    "size",
    "sku",
    "sort",
    "t",
    "th",
    "tk",
    "topic",
    "url",
    "v",
    "variant",
    "w",
    "width",
}


DOMAINS_TO_FIX = {
    "vm.tiktok.com": "tnktok.com",
    "www.tiktok.com": "tnktok.com",
    "vt.tiktok.com": "tnktok.com",
    "twitter.com": "fxtwitter.com",
    "x.com": "fixupx.com",
    "instagram.com": "instagramez.com",
    "www.instagram.com": "instagramez.com",
}


WHITELISTED_DOMAINS = [
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "open.spotify.com",
    "cdn.discordapp.com",
    *DOMAINS_TO_FIX.values(),
]


DOMAINS_TO_REDIRECT = ["a.aliexpress.com", "a.co", "s.click.aliexpress.com"]  # "vm.tiktok.com",


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
    """redirect URLs that are hiding trackers in them"""
    if urlparse(url).netloc in DOMAINS_TO_REDIRECT:
        try:
            req = requests.get(url, headers=REDIRECT_HEADERS, timeout=10)
            if req.status_code == consts.HTTP_OK and not req.url.endswith("errors/500"):
                return req.url
        except Exception:  # pylint: disable=broad-except
            pass
    return url


def proxy_if_necessary(url: str) -> Tuple[str, bool]:
    """
    mostly fix embeds for discord
    :return the sanitized url, bool implying whether or not to keep embed
    """
    netloc = urlparse(url).netloc
    if netloc in DOMAINS_TO_FIX.keys():  # pylint: disable=consider-iterating-dictionary
        url = url.replace(netloc, DOMAINS_TO_FIX[netloc], 1)
        return url, True
    return url, False


def proxy_url(url: str) -> Tuple[str, bool]:
    """
    just proxy a URL on demand
    :return: sanitized url, bool implying whether or not to keep embed
    """
    sanitized_url = handle_redirect(url)
    sanitized_url, keep_embed = proxy_if_necessary(sanitized_url)
    return sanitized_url if sanitized_url != url else url, keep_embed


def sanitize_message(message_content: str) -> Tuple[str, bool, bool]:
    """
    :return: Response content, needs sanitizing bool, warning suffix bool
    """
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
                    if requests.get(sanitized_url, timeout=10).ok:
                        sanitized_msg_word_list.append(sanitized_url)
                        needs_sanitizing = True
                        post_warning = False
                    continue
                except requests.exceptions.ReadTimeout:
                    continue  # he's dead jim
            else:
                needs_sanitizing, post_warning = True, True
                sanitized_msg_word_list.append(f"<{sanitized_url}>")

    return "\n".join(sanitized_msg_word_list), needs_sanitizing, post_warning


def sanitize_url(url: str) -> str:
    """remove unnecessary url parameters from a url"""
    new_word = url.split("?")[0]

    # do not sanitize image embeds
    if util.is_image(new_word) or util.is_video(new_word):
        return url

    url_params = []
    if len(url.split("?")) > 1:
        url_params = url.split("?")[1].split("&")
    if "amazon." in new_word:
        new_word = new_word.split("ref=")[0]
    url_params[:] = [param for param in url_params if valid_param(param)]
    if len(url_params) > 0:
        new_word = new_word + "?" + "&".join(url_params)
    return url if url.endswith("?") else new_word


# TODO: cache this function and discover why function would not cache in test
def get_allowed_params(allowed_params_file: Optional[str] = '') -> set:
    """merge hardcoded allowed params with those from"""
    params_in_file = {}
    if allowed_params_file and os.path.exists(allowed_params_file):
        try:
            with open(allowed_params_file, 'rb') as _file:
                params_in_file = pickle.load(_file)
        except pickle.UnpicklingError:
            log.error("%s is not pickled properly, please investigate", allowed_params_file)
    return ALLOWED_PARAMS.union(params_in_file)


def valid_param(param: str) -> bool:
    """checks url query parameter against hard list of valid ones"""
    for allowed_param in get_allowed_params(ALLOWED_PARAMS_FILE):
        if param.startswith(f"{allowed_param}="):
            return True
    return False
