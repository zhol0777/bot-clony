'''
automate making server banners
'''

from io import BytesIO
import logging
import os

from discord.ext import commands
from PIL import Image
import requests

import util

BANNERLORD_ROLE_ID = int(os.getenv('BANNERLORD_ROLE_ID', '0'))
VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')
MAX_IMAGE_SIZE = 1024 * 1024 * 10

log = logging.getLogger(__name__)


class Bannerlord(commands.Cog):
    '''banner-ify a message'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(BANNERLORD_ROLE_ID)
    async def banner(self, ctx: commands.Context, *args):
        '''
        make the message this replies to banner!
        usage: [as a reply] !banner [# picture in reply message]
        '''
        dm_channel = await ctx.message.author.create_dm()
        status_message = await dm_channel.send('Starting banner upload process!')
        attachment_index = 0 if len(args) < 1 else (int(args[0]) - 1)
        if ctx.message.reference is None or ctx.message.reference.message_id is None:
            await util.handle_error(ctx, '!banner must be used as a reply')
            return
        original_msg = await ctx.fetch_message(
            ctx.message.reference.message_id)
        if not original_msg.attachments:
            await status_message.edit(content='No attachments found searching embeds for image...')
            image_url_list = []
            for embed in original_msg.embeds:
                if embed.thumbnail and str(embed.thumbnail.url).lower().endswith(VALID_IMAGE_EXTENSIONS):
                    image_url_list.append(embed.thumbnail.url)
                else:
                    if embed.image and embed.image.url and \
                            embed.image.url.lower().endswith(VALID_IMAGE_EXTENSIONS):
                        image_url_list.append(embed.image.url)
            try:
                attachment_url = image_url_list[attachment_index]
            except IndexError:
                await util.handle_error(ctx,
                                        'no valid attachments for banner found with that index')
        else:
            try:
                attachment = original_msg.attachments[attachment_index]
            except IndexError:
                await util.handle_error(ctx,
                                        'no valid attachments for banner found with that index')
            attachment_url = attachment.url.split('?')[0]
            if not util.is_image(attachment_url):
                log.error("attachment_url %s is not known to be image?", attachment_url)
                await util.handle_error(ctx,
                                        f'intended image name {attachment_url} does not '
                                        f'end in {VALID_IMAGE_EXTENSIONS}')
        await status_message.edit(content="found banner! downloading...")
        image_req = requests.get(str(attachment.url), timeout=30)
        await status_message.edit(content="banner should be downloaded now!")
        if image_req.status_code != 200:
            log.error("attempting to download %s results in %s", attachment.url, image_req.status_code)
            await util.handle_error(ctx, f'Attempt to download {attachment.url} '
                                         f'resulted in HTTP {image_req.status_code}')
            return
        image_content = image_req.content
        if image_size_needs_reduction(image_content):
            await status_message.edit(content='shrinking image down for banner, please wait a moment')
            image_content = reduced_image(image_content)

        await status_message.edit(content='banner uploading...')
        await ctx.guild.edit(banner=image_content, splash=image_content,  # type: ignore
                             discovery_splash=image_content)
        await status_message.edit(content='banner uploaded! have a nice day!')


def image_size_needs_reduction(image_content: bytes) -> bool:
    '''return true if image is too big to be banner'''
    return len(image_content) >= MAX_IMAGE_SIZE


def reduced_image(image_content: bytes) -> bytes:
    '''
    discord API sets a limit for 1MB for image for the banner
    I am too lazy to write something that does the math on how much an image
    should be shrunk while retaining maximum resolution, so instead we can
    recursively shrink the image until it reaches a reasonable size
    0.7 is a nice number, close to (1/math.sqrt(2)), halves total number of
    pixels in the image for each passthrough to keep number of reductions
    fairly reasonable without overkilling resolution
    '''
    if image_size_needs_reduction(image_content):
        image_obj = Image.open(BytesIO(image_content))
        width, height = image_obj.size
        image_obj = image_obj.resize((int(width * 0.7), int(height * 0.7)), Image.LANCZOS)  # pylint: disable=no-member
        buf = BytesIO()
        try:
            image_obj.save(buf, format='JPEG')
        except (KeyError, OSError):
            # OSError: cannot write mode RGBA as JPEG
            image_obj = image_obj.convert('RGB')
            image_obj.save(buf, format='JPEG')
        image_content = buf.getvalue()
        return reduced_image(image_content)
    return image_content


async def setup(client):
    '''setup'''
    await client.add_cog(Bannerlord(client))
