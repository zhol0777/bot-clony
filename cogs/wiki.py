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

HELPER_ROLE = os.getenv('HELPER_ROLE')
MOD_ROLE = os.getenv('MOD_ROLE')


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
        reply_message = await util.get_reply_message(ctx, ctx.message)

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

    @wiki.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def define(self, ctx: commands.context, *args):
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
                    update={db.WikiPage.page: page}
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

    @wiki.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def delete(self, ctx: commands.context, shortname: str):
        '''
        Usage: !wiki delete [shortname]
        Delete wiki pages by shortname
        '''
        with db.bot_db:
            db_page = db.WikiPage.get(db.WikiPage.shortname == shortname)
            if db_page:
                db_page.delete_instance()
                await ctx.channel.send(f"Page {shortname} deleted from BotDB")

    @wiki.command()
    async def listall(self, ctx: commands.context):
        '''
        Usage: !wiki listall
        List all available wiki pages
        '''
        with db.bot_db:
            pages = db.WikiPage.select()
            page_listing = '\n'.join(sorted(p.shortname for p in pages))
            await ctx.channel.send(
                "```"
                "Usage: !wiki [page]\n\n"
                "Available pages:\n"
                f"{page_listing}\n"
                "```"
            )


async def setup(client):
    '''add cog'''
    await client.add_cog(Wiki(client))
