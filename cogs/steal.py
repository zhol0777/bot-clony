'''
Command to steal emojis
'''
from discord.ext import commands
import discord
import requests


class Steal(commands.Cog):
    '''steal emojis'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def steal(self, ctx: commands.Context, emoji: discord.PartialEmoji, new_name):
        '''
        Usage: !steal [emoji] [alt_name]
        '''
        if not ctx.message.guild:
            return
        emoji_name = str(new_name) or emoji.name
        if not ctx.guild:
            return
        if emoji_name in [existing_emoji.name for existing_emoji in ctx.guild.emojis]:
            await ctx.message.channel.send(f"Emoji named {emoji_name} already exists in this server. "
                                           f"Maybe you can consider renaming it by running "
                                           f"`!steal [emoji] alternate-name`?")
            return
        img_request = requests.get(emoji.url, timeout=10)
        emoji = await ctx.message.guild.create_custom_emoji(name=emoji_name,  # type: ignore
                                                            image=img_request.content)
        await ctx.message.add_reaction(emoji)

    @commands.command()
    async def unsteal(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        '''
        Usage: !unsteal [emoji]
        '''
        try:
            await ctx.guild.delete_emoji(emoji)  # type: ignore
            await ctx.message.channel.send("farewell...")
        except Exception as e:
            await ctx.message.channel.send(f"error occured deleting emoji: `{e}`")


async def setup(client):
    '''setup'''
    await client.add_cog(Steal(client))
