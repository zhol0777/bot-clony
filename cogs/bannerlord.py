'''
automate making server banners
'''

import os

from discord.ext import commands
import discord
import requests
import validators

import db
import util

BANNERLORD_ROLE = os.getenv('BANNERLORD_ROLE', 'bannerlord')
BANNERLORD_CHANNEL = os.getenv('BANNERLORD_CHANNEL', 'kb-show-and-tell')
VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')

BAD_MESSAGE_TEXT = '''
kb-show-and-tell messages should contain attachments of pictures of keyboards.
Please create a thread to add comments to someone's build.
If you believe this message was sent in error, please contact <@688959322708901907>
to fix it.'''


class Bannerlord(commands.Cog):
    '''banner-ify a message'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(BANNERLORD_ROLE)
    async def banner(self, ctx: commands.Context,  *args):
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
        await ctx.guild.edit(banner=image_req.content)
        await ctx.message.delete()
        await original_msg.pin()
        with db.bot_db:
            pins = db.BannerPost.select()
            for pin in pins:
                message_id = pin.message_id
                pin_msg = await ctx.fetch_message(message_id)
                if pin_msg:
                    await pin_msg.unpin()
                pin.delete_instance()
            db.BannerPost.create(message_id=ctx.message.reference.message_id)

    @commands.Cog.listener()
    async def on_message(self, message):
        '''delete any bunk message in bannerlord channel'''
        if message.channel.name != BANNERLORD_CHANNEL:
            return
        if message.attachments:
            return
        for word in message.content.split():
            if validators.url(word):
                return
        if discord.utils.get(message.author.roles, name=BANNERLORD_ROLE):
            return
        dm_channel = await message.author.create_dm()
        await dm_channel.send(BAD_MESSAGE_TEXT)
        await message.delete()


async def setup(client):
    '''setup'''
    await client.add_cog(Bannerlord(client))
