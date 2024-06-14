'''
Command to steal emojis
'''
from discord.ext import commands
import discord
import requests
import validators


class Steal(commands.Cog):
    '''steal emojis'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def steal(self, ctx: commands.Context):
        '''
        Usage: !steal [emoji] [alt_name]
        '''
        if not ctx.guild:
            return
        words = ctx.message.content.split()
        emoji = words[1]
        emoji_name = words[2] if len(words) > 2 else None
        # is url
        if emoji.startswith('<') and emoji.endswith('>'):  # uses embedded emoji
            found_emoji = discord.PartialEmoji.from_str(emoji)
            emoji_url = found_emoji.url
            emoji_name = emoji_name or found_emoji.name
        elif validators.url(emoji):
            emoji_url = emoji
            if not emoji_name:
                await ctx.channel.send("Direct URL to emoji requires naming. Maybe try "
                                       "`!steal [emoji url] [emoji name]`?")
                return
        if emoji_name in [existing_emoji.name for existing_emoji in ctx.guild.emojis]:
            await ctx.channel.send(f"Emoji named `{emoji_name}` already exists in this server. "
                                   "Maybe you can consider renaming it by running "
                                   "`!steal [emoji] alternate-name`?")
            return
        img_request = requests.get(emoji_url, timeout=10)
        created_emoji = await ctx.message.guild.create_custom_emoji(name=emoji_name,  # type: ignore
                                                                    image=img_request.content)
        await ctx.message.add_reaction(created_emoji)

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
