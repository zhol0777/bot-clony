'''
automate making server banners
'''

from io import BytesIO
import logging
import os

from discord.ext import commands
from PIL import Image
import discord
import requests
import validators

import db
import util

BANNERLORD_ROLE = os.getenv('BANNERLORD_ROLE', 'bannerlord')
BANNERLORD_CHANNEL = os.getenv('BANNERLORD_CHANNEL', 'kb-show-and-tell')
VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')
MAX_IMAGE_SIZE = (10240 * 1024)

BAD_MESSAGE_TEXT = '''
kb-show-and-tell messages should contain attachments of pictures of keyboards.
Please create a thread to add comments to someone's build.
If you believe this message was sent in error, please contact <@688959322708901907>
to debug it.'''

log = logging.getLogger(__name__)


class Bannerlord(commands.Cog):
    '''banner-ify a message'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(BANNERLORD_ROLE)
    async def banner(self, ctx: commands.Context, *args):
        '''
        make the message this replies to banner!
        usage: [as a reply] !banner [# picture in reply message]
        '''
        # TODO: handle with channel ID
        if ctx.channel.name != BANNERLORD_CHANNEL:
            await util.handle_error(ctx, f'!banner can only be used in {BANNERLORD_CHANNEL}')
            return
        attachment_index = 0 if len(args) < 1 else (int(args[0]) - 1)
        if ctx.message.reference is None:
            await util.handle_error(ctx,
                                    '!banner must be used as a reply')
            return
        original_msg = await ctx.fetch_message(
            ctx.message.reference.message_id)
        if not original_msg.attachments:
            # odd chance they're using an image embed?
            words = original_msg.content.split()
            image_url_list = []
            for word in words:
                if validators.url(word) and \
                        word.lower().endswith(VALID_IMAGE_EXTENSIONS):
                    image_url_list.append(word)
            attachment_url = image_url_list[attachment_index]
            if image_url_list:
                await util.handle_error(ctx,
                                        'no valid attachments for banner found')
                return
        else:
            attachment = original_msg.attachments[attachment_index]
            attachment_url = attachment.url
            if not attachment_url.lower().endswith(VALID_IMAGE_EXTENSIONS):
                await util.handle_error(ctx,
                                        f'intended image name {attachment_url} does not '
                                        'end in {VALID_IMAGE_EXTENSIONS}')
        image_req = requests.get(attachment_url, timeout=30)
        if image_req.status_code != 200:
            await util.handle_error(ctx, 'Attempt to download {attachment_url} '
                                         'resulted in HTTP {image_req.status_code}')
            return
        image_content = reduce_image_size_if_necessary(image_req.content)

        await ctx.guild.edit(banner=image_content)
        await ctx.message.delete()
        await original_msg.pin()
        with db.bot_db:
            await self.clear_old_banner_pins(ctx)
            db.BannerPost.create(message_id=ctx.message.reference.message_id)

    async def clear_old_banner_pins(self, ctx: commands.Context):
        '''
        latest bannered board gets pinned, and pin is tracked in BannerPost table
        on new banner, go through old pinned post(s) to un-pin
        '''
        pins = db.BannerPost.select()
        for pin in pins:
            message_id = pin.message_id
            pin_msg = await ctx.fetch_message(message_id)
            if pin_msg:
                await pin_msg.unpin()
            pin.delete_instance()

    @commands.Cog.listener()
    async def on_message(self, message):
        '''delete any bunk message in bannerlord channel'''
        if isinstance(message.channel, discord.DMChannel):
            # avoid error messages caused by DM responses
            return
        if message.channel.name != BANNERLORD_CHANNEL:
            return
        if message.type == discord.MessageType.thread_created:
            # ignore thread creation
            return
        if message.attachments:
            # ignore messages with attachments
            return
        for word in message.content.split():
            if validators.url(word):
                return
        if discord.utils.get(message.author.roles, name=BANNERLORD_ROLE):
            # bannerlord is announcing banner of the day
            return
        dm_channel = await message.author.create_dm()
        await dm_channel.send(BAD_MESSAGE_TEXT)
        await message.delete()


def reduce_image_size_if_necessary(image_content: bytes) -> bytes:
    '''
    discord API sets a limit for 1MB for image for the banner
    I am too lazy to write something that does the math on how much an image
    should be shrunk while retaining maximum resolution, so instead we can
    recursively shrink the image until it reaches a reasonable size
    0.7 is a nice number, close to (1/math.sqrt(2)), halves total number of
    pixels in the image for each passthrough to keep number of reductions
    fairly reasonable without overkilling resolution
    '''
    if len(image_content) >= MAX_IMAGE_SIZE:
        image_obj = Image.open(BytesIO(image_content))
        width, height = image_obj.size
        image_obj = image_obj.resize((int(width * 0.7), int(height * 0.7)), Image.LANCZOS)
        buf = BytesIO()
        image_obj.save(buf, format='JPEG')
        image_content = buf.getvalue()
        return reduce_image_size_if_necessary(image_content)
    return image_content


async def setup(client):
    '''setup'''
    await client.add_cog(Bannerlord(client))
