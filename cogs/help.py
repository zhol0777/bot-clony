'''
Generic commands that provide simple responses
'''
import os
import re

from discord.ext import commands

import util

GENERAL_COMMANDS = '''
Generics:
  help2         Posts all this
  sanitize      Usage: !sanitize [url1] [url2] ...
                       !sanitize (as reply)
  newvendors    Posts the vendors list
  wiki          Provide link from community wiki
                Usage: !wiki [page name]
                       ![page name]
                       !wiki listall
  remindme      Reminds a user at a later time of something
                Usage: !remindme [time h:hour m:minute d:day w:week M:month y:year] [reason]
                   ex. !remindme 1850300 fumo sale
                       !remindme 30d develop better help messages
  channeldescription
                Posts channel description
  thock         provide a count of total usage of 'thock' as well as local channel usage
  mechmarket    Usage: !mechmarket [query...]           # search reddit for sales
                       !mechmarket add [query...]       # ping you when mechmarket scraper matches
                       !mechmarket list                 # list all queries by ID and string
                       !mechmarket delete [query_id]    # stop responding to matches
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
  socialcredit
                Usage:  !socialcredit [user tag]
                [reply] !socialcredit
                        !socialcredit add [user tag] [amount]
                [reply] !socialcredit add [amount]

                        !socialcredit remove [user tag] [amount]
                [reply] !socialcredit remove [amount]
  wiki          Usage:  !wiki define page [shortname] [url]
                        !wiki define root [url]
                        !wiki delete [shortname]
                        !wiki listall
  silly         Usage:  !silly define [shortname] [text...]
                        !silly delete [shortname]
                        !silly listall
  forcegoogle   Usage:  [reply] !forcegoogle
                                !lmgtfy
  decide        Usage:  !decide sonnet75 obliterated75 gmmkpro q1 m1
  autosanitize  Usage:  !autosanitize true
                        !autosanitize false
  slowmode      Usage:  !slowmode [interval]  # only for help/buying advice
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
  countthock    Enable thock-counting in channel:
                !countthock true
                Use false to disable counting
'''

MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
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
        if len(args) == 0:
            await ctx.channel.send(f'```{GENERAL_COMMANDS}```')
            if util.user_has_role_from_id(ctx.message.author, HELPER_ROLE_ID) \
                    and ctx.message.channel.id in {HELPER_CHAT_ID,
                                                   ZHOLBOT_CHANNEL_ID}:
                await ctx.channel.send(f'```{HELPER_COMMANDS}```')
            if util.user_has_role_from_id(ctx.message.author, MOD_ROLE_ID) \
                    and ctx.message.channel.id == MOD_CHAT_ID:
                await ctx.channel.send(f'```{MOD_COMMANDS}```')
            return
        command = args[0]
        help_msg = f'Help for {command}:\n'
        for line in GENERAL_COMMANDS.split('\n'):
            if command in line:
                help_msg += f'{line}\n'
        if not hasattr(ctx.message.author, 'roles'):
            return
        if util.user_has_role_from_id(ctx.message.author, HELPER_ROLE_ID) \
                and ctx.message.channel.id in {HELPER_CHAT_ID,
                                               ZHOLBOT_CHANNEL_ID}:
            for line in HELPER_COMMANDS.split('\n'):
                if command in line:
                    help_msg += f'{line}\n'
        if util.user_has_role_from_id(ctx.message.author, MOD_ROLE_ID) \
                and ctx.message.channel.id == MOD_CHAT_ID:
            for line in MOD_COMMANDS.split('\n'):
                if command in line:
                    help_msg += f'{line}\n'
        await ctx.channel.send(f'```{help_msg}```')

    @commands.command(aliases=['lmgtfy'])
    @commands.has_any_role(HELPER_ROLE_ID, MOD_ROLE_ID)
    async def forcegoogle(self, ctx: commands.Context):
        '''passive aggressive reminder that some questions can be answered with google'''
        source = 'https://google.com/search?q='
        await self.force_search(ctx, source)

    @commands.command()
    @commands.has_any_role(HELPER_ROLE_ID, MOD_ROLE_ID)
    async def forceduckduckgo(self, ctx: commands.Context):
        '''passive aggressive reminder that some questions can be answered with duckduckgo'''
        source = 'https://duckduckgo.com/?q='
        await self.force_search(ctx, source)

    async def force_search(self, ctx, source):
        '''make search force-search commands generic'''
        if ctx.message.reference:
            await ctx.message.delete()
            reply_message = await util.get_reply_message(ctx.message)
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
