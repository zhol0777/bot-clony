'''
Utility functions shared across cogs
'''

from discord.ext import commands


async def handle_error(ctx: commands.Context, error_message: str):
    '''send an error message to a user when they misuse a command'''
    channel = await ctx.message.author.create_dm()
    await channel.send(error_message)
    await ctx.message.delete()
