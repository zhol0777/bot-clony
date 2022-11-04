'''
Generic commands that provide simple responses
'''
import re
import os

from discord.ext import commands
import discord

import util

GENERAL_COMMANDS = '''
Generics:
  help2         Posts all this
  sanitize      Sanitize messages with URLs with extra URL parameters
                Usage: !sanitize [url1] [url2] ...
                       !sanitize (as reply)
  newvendors       Posts the vendors list
  wiki          Provide link from community wiki
                Usage: !wiki [page name]
                       !wiki listall
  remindme      Reminds a user at a later time of something
                Usage: !remindme [time] [reason]
                   ex. !remindme 1850300 fumo sale
'''

HELPER_COMMANDS = '''
Helper Commands:
  eject         Usage:  !eject [@ user tag] [reason...]
                        !eject [reason...] (as reply)
  uneject       Usage:  !uneject [@ user tag]
  tempeject     Usage:  !tempeject [@ user tag] [time] [reason...]
  ejectwarn     Usage:  !ejectwarn [@ user tag] [reason...]
                        !ejectwarn [reason...] (as reply)
                        !ejectwarn list [@ user tag]
                        !ejectwarn delete [reason ID]
  unejectloopstart
                Start async time monitoring loop for unejects
                Usage:  !unejectloopstart
  slowmode      Activate slowmode in help channels
                Usage:  !slowmode [interval]
  socialcredit
                Social credit adding or removing from users
                Usage:  !socialcredit [user tag]
                [reply] !socialcredit

                        !socialcredit add [user tag] [amount]
                [reply] !socialcredit add [amount]

                        !socialcredit remove [user tag] [amount]
                [reply] !socialcredit remove [amount]
  wiki          Usage:  Define a wiki page by a shortcut:
                        !wiki define page [shortname] [url]
                        Define the wiki root domain:
                        !wiki define root [url]
                        Delete a wiki page
                        !wiki delete [shortname]
  forcegoogle   Usage:  [reply] !forcegoogle
'''

MOD_COMMANDS = '''
Mod Commands:
  reboot        Restart the bot
                Usage: !reboot
  update        Run git pull before restarting bot
                Usage: !update
  banner        Make the picture in a kb-show-and-tell message banner
  unejectloopstart
                Restarts temp eject monitoring task loop
  startreminderloop
                Restarts/starts reminder task loop
'''

HELPER_ROLE = os.getenv('HELPER_ROLE')
MOD_ROLE = os.getenv('MOD_ROLE')
ZHOLBOT_CHANNEL_ID = int(os.getenv('ZHOLBOT_CHANNEL_ID', '0'))
MOD_CHAT_ID = int(os.getenv('MOD_CHAT_ID', '0'))
HELPER_CHAT_ID = int(os.getenv('HELPER_CHAT_ID', '0'))


class Help(commands.Cog):
    '''Display help information per-function'''
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def help2(self, ctx: commands.Context, *args):
        '''Help info'''
        print(ctx.message.channel.id)
        if len(args) == 0:
            await ctx.channel.send(f'```{GENERAL_COMMANDS}```')
            if discord.utils.get(ctx.message.author.roles, name=HELPER_ROLE) \
                    and ctx.message.channel.id in [HELPER_CHAT_ID,
                                                   ZHOLBOT_CHANNEL_ID]:
                await ctx.channel.send(f'```{HELPER_COMMANDS}```')
            if discord.utils.get(ctx.message.author.roles, name=MOD_ROLE) \
                    and ctx.message.channel.id == MOD_CHAT_ID:
                await ctx.channel.send(f'```{MOD_COMMANDS}```')
            return
        command = args[0]
        help_msg = f'Help for {command}:\n'
        for line in GENERAL_COMMANDS.split('\n'):
            if command in line:
                help_msg += f'{line}\n'
        if discord.utils.get(ctx.message.author.roles, name=HELPER_ROLE) \
                and ctx.message.channel.id in [HELPER_CHAT_ID,
                                               ZHOLBOT_CHANNEL_ID]:
            for line in HELPER_COMMANDS.split('\n'):
                if command in line:
                    help_msg += f'{line}\n'
        if discord.utils.get(ctx.message.author.roles, name=MOD_ROLE) \
                and ctx.message.channel.id == MOD_CHAT_ID:
            for line in MOD_COMMANDS.split('\n'):
                if command in line:
                    help_msg += f'{line}\n'
        await ctx.channel.send(f'```{help_msg}```')

    @commands.command(aliases=['lmgtfy'])
    @commands.has_any_role(HELPER_ROLE, MOD_ROLE)
    async def forcegoogle(self, ctx: commands.Context):
        '''passive aggressive reminder that some questions can be answered with google'''
        source = 'https://google.com/search?q='
        await self.force_search(ctx, source)

    @commands.command()
    @commands.has_any_role(HELPER_ROLE, MOD_ROLE)
    async def forceduckduckgo(self, ctx: commands.Context):
        '''passive aggressive reminder that some questions can be answered with duckduckgo'''
        source = 'https://duckduckgo.com/?q='
        await self.force_search(ctx, source)

    async def force_search(self, ctx, source):
        '''make search force-search commands generic'''
        if ctx.message.reference:
            await ctx.message.delete()
            reply_message = await util.get_reply_message(ctx, ctx.message)
            reply_message_content = reply_message.content
        else:
            reply_message = ctx.message
            reply_message_content = ' '.join(ctx.message.content.split()[1:])
        reply_message_content = re.sub(r'[^ \w+]', '', reply_message_content)  # thanks powwu
        search_string = '+'.join(reply_message_content.split())
        send_msg_content = f'<{source}{search_string}>'
        await ctx.channel.send(send_msg_content, reference=reply_message)


async def setup(client):
    '''setup'''
    await client.add_cog(Help(client))
