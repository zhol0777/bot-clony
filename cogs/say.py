'''
turn said text into request to play correctly formatted TTS url
'''
from urllib.parse import urlencode

from discord.ext import commands


class Say(commands.Cog):
    '''something i'm giving up on you'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def say(self, ctx: commands.Context):
        '''
        Usage: !say hello world
        '''
        url_params = urlencode({
            'text': ctx.message.content
        })
        await ctx.channel.send(f"!play https://api.flowery.pw/v1/tts?{url_params}")


async def setup(client):
    '''setup'''
    await client.add_cog(Say(client))
