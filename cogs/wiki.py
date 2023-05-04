'''
Cog to allow users to link pages in community wiki
and allow helpers to define page links in community wiki
'''
from urllib.parse import urljoin
import os

from discord.ext import commands
import validators

import db
import util

HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
ZHOLBOT_CHANNEL_ID = int(os.getenv('ZHOLBOT_CHANNEL_ID', '0'))
HELPER_CHAT_ID = int(os.getenv('HELPER_CHAT_ID', '0'))


class Wiki(commands.Cog):
    '''command'''
    def __init__(self, client):
        self.client = client

    @commands.group()
    async def wiki(self, ctx: commands.Context):
        '''
        Usage: !wiki [page name]
        Grab a link to some community wiki page
        '''
        if ctx.invoked_subcommand and \
                ctx.invoked_subcommand.name in ['define', 'listall', 'delete']:
            return
        reply_message = await util.get_reply_message(ctx.message)

        # avoid reply being pinged twice
        if reply_message != ctx.message:
            await ctx.message.delete()

        if len(ctx.message.content.split()) < 2:
            await self.listall(ctx)
            return

        page_name = ctx.message.content.split()[1]
        with db.bot_db:
            wiki_page = db.WikiPage.get_or_none(shortname=page_name)

            if not wiki_page:
                await ctx.channel.send(f"Page {page_name} does not exist!",
                                       reference=reply_message)
                await self.listall(ctx)
                return
            if wiki_page.goes_to_root_domain:
                wiki_domain = db.WikiRootUrl.get_or_none(indicator='primary')
                if not wiki_domain:
                    await ctx.channel.send("Wiki domain root is undefined")
                    return
                url = urljoin(wiki_domain.domain, wiki_page.page)
                await ctx.channel.send(f"{url}", reference=reply_message)
            else:
                await ctx.channel.send(wiki_page.page, reference=reply_message)

    @wiki.command()  # type: ignore
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def define(self, ctx: commands.Context, *args):
        '''
        Usage: !wiki define page [shortname] [url/subdirectory]
               !wiki define wiki_domain_root [url]
        Define individual wiki page locations
        If page is defined as a full URL, shortname points to URL
        If page is recognized as URL subdirectory, it is appended
        to wiki_domain_root page
        '''
        sub_sub_command = args[0]
        with db.bot_db:
            if sub_sub_command == 'page':
                shortname, page = args[1], args[2]
                if validators.url(page):
                    goes_to_root_domain = False
                else:
                    goes_to_root_domain = True
                db.WikiPage.insert(
                    shortname=shortname,
                    page=page,
                    goes_to_root_domain=goes_to_root_domain
                ).on_conflict(
                    conflict_target=[db.WikiPage.shortname],
                    update={db.WikiPage.page: page,
                            db.WikiPage.goes_to_root_domain: goes_to_root_domain}
                ).execute()
                await ctx.channel.send(
                    f"!wiki {shortname} -> <{page}>")
                return
            if sub_sub_command == 'root':
                root_url = args[1]
                db.WikiRootUrl.insert(
                    indicator='primary',
                    domain=root_url
                ).on_conflict(
                    conflict_target=[db.WikiRootUrl.indicator],
                    update={db.WikiRootUrl.domain: root_url}
                ).execute()
                await ctx.channel.send(f"Root wiki made: <{root_url}>")
                return

    @wiki.command()  # type: ignore
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def delete(self, ctx: commands.Context, shortname: str):
        '''
        Usage: !wiki delete [shortname]
        Delete wiki pages by shortname
        '''
        with db.bot_db:
            db_page = db.WikiPage.get(db.WikiPage.shortname == shortname)
            if db_page:
                db_page.delete_instance()
                await ctx.channel.send(f"Page {shortname} deleted from BotDB")

    @wiki.command()  # type: ignore
    async def listall(self, ctx: commands.Context):
        '''
        Usage: !wiki listall
        List all available wiki pages
        '''
        with db.bot_db:
            pages = db.WikiPage.select()
            page_listing = '\n'.join(sorted(p.shortname for p in pages))
            await ctx.message.channel.send(
                "```"
                "Usage: !wiki [page]\n\n"
                "Available pages:\n"
                f"{page_listing}\n"
                "```"
            )


class Silly(commands.Cog):
    '''command'''
    def __init__(self, client):
        self.client = client

    @commands.group()
    async def silly(self, ctx: commands.Context):
        "like wiki, but dumber"
        if ctx.invoked_subcommand and \
                ctx.invoked_subcommand.name in ['define', 'listall', 'delete']:
            return

        shortname = ctx.message.content.split()[1]
        with db.bot_db:
            if silly_page := db.SillyPage.get_or_none(shortname=shortname):
                await ctx.channel.send(silly_page.response_text)

    @silly.command()  # type: ignore
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def define(self, ctx: commands.Context, *args):
        '''
        Usage: !silly define [shortname] [response text]
        Define individual silly responses
        '''
        try:
            shortname, response_text = args[0], ' '.join(args[1:])
        except IndexError:
            await ctx.channel.send("Shortname and/or response text not provided in definition command")
            return
        with db.bot_db:
            db.SillyPage.insert(
                shortname=shortname,
                response_text=response_text
            ).on_conflict(
                conflict_target=[db.SillyPage.shortname],
                update={db.SillyPage.response_text: response_text}
            ).execute()
            await ctx.channel.send(
                f"!silly {shortname} -> {response_text}"
            )

    @silly.command()  # type: ignore
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def delete(self, ctx: commands.Context, shortname: str):
        '''
        Usage: !silly delete [shortname]
        Delete silly responses by shortname
        '''
        with db.bot_db:
            db_page = db.SillyPage.get(db.WikiPage.shortname == shortname)
            if db_page:
                db_page.delete_instance()
                await ctx.channel.send(f"Response {shortname} deleted from BotDB")

    @silly.command()  # type: ignore
    @commands.has_any_role(MOD_ROLE_ID, HELPER_ROLE_ID)
    async def listall(self, ctx: commands.Context):
        '''
        Usage: !silly listall
        List all available programmable joke responses
        '''
        if util.user_has_role_from_id(ctx.message.author, HELPER_ROLE_ID):
            if ctx.message.channel.id in [HELPER_CHAT_ID, ZHOLBOT_CHANNEL_ID]:
                with db.bot_db:
                    pages = db.SillyPage.select()
                    page_listing = '\n'.join(sorted(p.shortname for p in pages))
                    await ctx.message.channel.send(
                        "```"
                        "Usage: !silly [page]\n\n"
                        "Available pages:\n"
                        f"{page_listing}\n"
                        "```"
                    )


async def setup(client):
    '''add cog'''
    await client.add_cog(Wiki(client))
    await client.add_cog(Silly(client))
