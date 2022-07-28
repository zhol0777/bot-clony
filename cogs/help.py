'''
Generic commands that provide simple responses
'''
import os

from discord.ext import commands
import discord

GENERAL_COMMANDS = '''
Generics:
  flashsales    apply/remove flash sales role
  lifealert     Alert the mods of something sus...
                Usage: !lifealert [reason...]
                       !lifealert [reason...] (as reply)
  fakelifealert Usage: !fakelifealert [reason...] ...
  map           Posts the link to mechmap
  pins          A recommendation on where to find information easily
  sanitize      Sanitize messages with URLs with trackers
                Usage: !sanitize [url1] [url2] ...
                       !sanitize (as reply)
  spraylubing   A guide to spray-lubing
  trade         Posts a warning against organizing trades on discord
  vendors       Posts the vendors list
  vote          add emotes implying a poll
                Usage: !vote [thing to vote over...]
  wiki          Provide link from community wiki
                Usage: !wiki [page name]
                       !wiki listall
  eight
  google
  groupbuy
  northfacing
  oos
  thock
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
  deport        Usage: !deport [@ user tag]
                       !deport (as reply)
  undeport      Usage: !undeport [@ user tag]
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
  purge         Delete the last [count] messages from channel it is invoked in
                Usage: !purge [count]
  purgelast     Scan [count] messages from each channel and delete messages
                from tagged user
                Usage: !purgelast [@ user tag] [count]
  reboot        Restart the bot
                Usage: !reboot
  update        Run git pull before restarting bot
                Usage: !update
'''


class Help(commands.Cog):
    '''Display help information per-function'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def help(self, ctx: commands.Context, *args):
        '''Help info'''
        if len(args) == 0:
            await ctx.channel.send(f'```{GENERAL_COMMANDS}```')
            if discord.utils.get(ctx.message.author.roles, name=os.getenv('HELPER_ROLE')) \
                    and ctx.message.channel.name == os.getenv('HELPER_CHAT'):
                await ctx.channel.send(f'```{HELPER_COMMANDS}```')
            if discord.utils.get(ctx.message.author.roles, name=os.getenv('MOD_ROLE')) \
                    and ctx.message.channel.name == os.getenv('MOD_CHAT'):
                await ctx.channel.send(f'```{MOD_COMMANDS}```')
            return
        command = args[0]
        help_msg = f'Help for {command}:\n'
        for line in GENERAL_COMMANDS.split('\n'):
            if command in line:
                help_msg += f'{line}\n'
        if discord.utils.get(ctx.message.author.roles, name=os.getenv('HELPER_ROLE')) \
                and ctx.message.channel.name == os.getenv('HELPER_CHAT'):
            for line in HELPER_COMMANDS.split('\n'):
                if command in line:
                    help_msg += f'{line}\n'
        if discord.utils.get(ctx.message.author.roles, name=os.getenv('MOD_ROLE')) \
                and ctx.message.channel.name == os.getenv('MOD_CHAT'):
            for line in MOD_COMMANDS.split('\n'):
                if command in line:
                    help_msg += f'{line}\n'
        await ctx.channel.send(f'```{help_msg}```')


def setup(client):
    '''setup'''
    client.add_cog(Help(client))
