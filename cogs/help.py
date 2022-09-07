'''
Generic commands that provide simple responses
'''
import os

from discord.ext import commands
import discord

GENERAL_COMMANDS = '''
Generics:
  help2         Posts all this
  sanitize      Sanitize messages with URLs with trackers
                Usage: !sanitize [url1] [url2] ...
                       !sanitize (as reply)
  newvendors       Posts the vendors list
  wiki          Provide link from community wiki
                Usage: !wiki [page name]
                       !wiki listall
'''

HELPER_COMMANDS = '''
Helper Commands:
  eject         Usage: !eject [@ user tag] [reason...]
                       !eject [reason...] (as reply)
  uneject       Usage: !uneject [@ user tag]
  tempeject     Usage: !tempeject [@ user tag] [time] [reason...]
  ejectwarn     Usage: !ejectwarn [@ user tag] [reason...]
                       !ejectwarn [reason...] (as reply)
                       !ejectwarn list [@ user tag]
                       !ejectwarn delete [reason ID]
  slowmode      Activate slowmode in help channels
                Usage: !slowmode [interval]
  wiki          Usage: Define a wiki page by a shortcut:
                       !wiki define page [shortname] [url]
                       Define the wiki root domain:
                       !wiki define root [url]
                       Delete a wiki page
                       !wiki delete [shortname]
'''

MOD_COMMANDS = '''
Mod Commands:
  reboot        Restart the bot
                Usage: !reboot
  update        Run git pull before restarting bot
                Usage: !update
  banner        Make the picture in a kb-show-and-tell message banner
'''


class Help(commands.Cog):
    '''Display help information per-function'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def help2(self, ctx: commands.Context, *args):
        '''Help info'''
        if len(args) == 0:
            await ctx.channel.send(f'```{GENERAL_COMMANDS}```')
            if discord.utils.get(ctx.message.author.roles, name=os.getenv('HELPER_ROLE')) \
                    and ctx.message.channel.id == int(os.getenv('HELPER_CHAT_ID', '0')):
                await ctx.channel.send(f'```{HELPER_COMMANDS}```')
            if discord.utils.get(ctx.message.author.roles, name=os.getenv('MOD_ROLE')) \
                    and ctx.message.channel.id == int(os.getenv('MOD_CHAT_ID', '0')):
                await ctx.channel.send(f'```{MOD_COMMANDS}```')
            return
        command = args[0]
        help_msg = f'Help for {command}:\n'
        for line in GENERAL_COMMANDS.split('\n'):
            if command in line:
                help_msg += f'{line}\n'
        if discord.utils.get(ctx.message.author.roles, name=os.getenv('HELPER_ROLE')) \
                and ctx.message.channel.id == int(os.getenv('HELPER_CHAT_ID', '0')):
            for line in HELPER_COMMANDS.split('\n'):
                if command in line:
                    help_msg += f'{line}\n'
        if discord.utils.get(ctx.message.author.roles, name=os.getenv('MOD_ROLE')) \
                and ctx.message.channel.id == int(os.getenv('MOD_CHAT_ID', '0')):
            for line in MOD_COMMANDS.split('\n'):
                if command in line:
                    help_msg += f'{line}\n'
        await ctx.channel.send(f'```{help_msg}```')


async def setup(client):
    '''setup'''
    await client.add_cog(Help(client))
