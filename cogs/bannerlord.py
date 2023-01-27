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

BANNERLORD_ROLE_ID = int(os.getenv('BANNERLORD_ROLE_ID', '0'))
BANNERLORD_CHANNEL_ID = int(os.getenv('BANNERLORD_CHANNEL_ID', '0'))
VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')
MAX_IMAGE_SIZE = (1024 * 1024 * 10)

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
    @commands.has_any_role(BANNERLORD_ROLE_ID)
    async def banner(self, ctx: commands.Context, *args):
        '''
        make the message this replies to banner!
        usage: [as a reply] !banner [# picture in reply message]
        '''
        dm_channel = await ctx.message.author.create_dm()
        status_message = await dm_channel.send('Starting banner upload process!')
        if ctx.channel.id != BANNERLORD_CHANNEL_ID:
            await util.handle_error(ctx, '!banner can only be used in banner channel')
            return
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
            attachment_url = attachment.url
            if not attachment_url.lower().endswith(VALID_IMAGE_EXTENSIONS):
                await util.handle_error(ctx,
                                        f'intended image name {attachment_url} does not '
                                        'end in {VALID_IMAGE_EXTENSIONS}')
        await status_message.edit(content="found banner! downloading...")
        image_req = requests.get(str(attachment_url), timeout=30)
        await status_message.edit(content="banner should be downloaded now!")
        if image_req.status_code != 200:
            await util.handle_error(ctx, 'Attempt to download {attachment_url} '
                                         'resulted in HTTP {image_req.status_code}')
            return
        image_content = image_req.content
        if image_size_needs_reduction(image_content):
            await status_message.edit(content='shrinking image down for banner, please wait a moment')
            image_content = reduced_image(image_content)

        await status_message.edit(content='banner uploading...')
        await ctx.guild.edit(banner=image_content, splash=image_content,  # type: ignore
                             discovery_splash=image_content)
        await status_message.edit(content='banner uploaded! have a nice day!')
        await ctx.message.delete()
        with db.bot_db:
            await self.clear_old_banner_pins(ctx)
            db.BannerPost.create(message_id=ctx.message.reference.message_id)
        await original_msg.pin()

    async def clear_old_banner_pins(self, ctx: commands.Context):
        '''
        latest bannered board gets pinned, and pin is tracked in BannerPost table
        on new banner, go through old pinned post(s) to un-pin
        '''
        pins = db.BannerPost.select()
        for pin in pins:
            message_id = pin.message_id
            pin.delete_instance()
            try:
                pin_msg = await ctx.fetch_message(message_id)
                await pin_msg.unpin()
            except discord.errors.NotFound:
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        '''delete any bunk message in bannerlord channel'''
        if isinstance(message.channel, (discord.DMChannel, discord.Thread)):
            # avoid error messages caused by DM responses or etc.
            return
        if message.channel.id != BANNERLORD_CHANNEL_ID:
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
        if util.user_has_role_from_id(message.author, BANNERLORD_ROLE_ID):
            # bannerlord is announcing banner of the day
            return
        try:
            dm_channel = await message.author.create_dm()
            await dm_channel.send(BAD_MESSAGE_TEXT)
        except AttributeError:
            pass
        except discord.errors.Forbidden:
            pass  # user won't accept message from bot
        await message.delete()


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
        image_obj = image_obj.resize((int(width * 0.7), int(height * 0.7)), Image.LANCZOS)
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
