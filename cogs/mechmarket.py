'''
Scrape mechmarket periodically
'''
import logging

import os
import re

import asyncpraw
import discord
from discord.ext import commands, tasks  # ignore
from tabulate import tabulate

import db
import util


MECHMARKET_RSS_FEED = 'https://www.reddit.com/r/mechmarket/search.rss?q=flair%3Aselling&restrict_sr=on&sort=new&t=all'
MECHMARKET_BASE_URL = 'https://old.reddit.com/r/mechmarket'
# SELLING_FLAIR_SPAN = '<span class="linkflairlabel " title="Selling">Selling</span>'
LOOP_TIME = 60
BACKOFF_TIME_MS = 10000

EXPLANATION = '''
mechmarket:
  mechmarket        Searches for something for sale on mechmarket
                    Usage: !mechmarket
                           !mechmarket qk65
  mechmarket add    Adds a query for something on mechmarket to message you when a new posting is found
                    Usage: !mechmarket add gmk umbra
  mechmarket list   Lists all running queries a user has made by ID
                    Usage: !mechmarket list
  mechmarket delete
                    Delete a user's own running mechmarket queries based on IDs
                    Usage: !mechmarket delete 1 2 3
'''


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] [%(asctime)s] %(message)s')
log = logging.getLogger(__name__)


class MechmarketScraper(commands.Cog):
    '''scrape mechmarket posts from reddit feed'''
    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=LOOP_TIME)
    # pylint: disable=too-many-locals,too-many-branches
    async def scrape(self):
        '''run periodic scrape'''
        reddit = asyncpraw.Reddit(
            username=os.getenv('REDDIT_USERNAME', ''),
            password=os.getenv('REDDIT_PASSWORD', ''),
            client_id=os.getenv('REDDIT_CLIENT_ID', ''),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET', ''),
            user_agent=util.MECHMARKET_SCRAPE_HEADERS['user-agent']
        )
        mechmarket = await reddit.subreddit('mechmarket')
        async for post in mechmarket.search('flair:"Selling"', sort='new', limit=25):
            post_id = post.id
            post_link = post.url
            with db.bot_db:
                if db.MechmarketPost.get_or_none(post_id=post_id):
                    continue  # post has been processed

            timestamp = None
            post_text = post.selftext.replace('\n', ' ')
            urls = re.findall(r"(?P<url>https?://[^\s]+)", post_text)
            if urls:
                timestamp = urls[0]  # pray that it's the first link that's the timestamp

            with db.bot_db:
                for market_query in db.MechmarketQuery.select():
                    matches = True
                    # with basic search, content to match every word in query
                    for word_that_needs_to_be_found in market_query.search_string.split():
                        # strip html tags out
                        found_word = word_that_needs_to_be_found.lower() in post_text.lower()
                        matches = matches and found_word
                    # check for exact search if necessary
                    if market_query.search_string.startswith('"') and market_query.search_string.endswith('"'):
                        matches = market_query.search_string[1:-1].lower() in post_text.lower()
                    matches = matches or re.match(market_query.search_string.lower(), post_text.lower())
                    if not matches:
                        continue
                    reminded_user = await self.client.fetch_user(market_query.user_id)
                    channel = await reminded_user.create_dm()
                    text = f"Match found for following query: {market_query.search_string}\n{post.title}" + \
                           f"\n{post_link} - {timestamp}"
                    await channel.send(text)
                db.MechmarketPost.insert(post_id=post_id).execute()  # pylint: disable=no-value-for-parameter
        await reddit.close()

    @commands.group()
    async def mechmarket(self, ctx: commands.Context):
        '''response for people who will not do price checks themselves'''
        if ctx.invoked_subcommand and \
                ctx.invoked_subcommand.name in ['add', 'list', 'delete', 'help']:
            return
        response_text = MECHMARKET_BASE_URL
        args = ctx.message.content.split()[1:]
        if len(args) > 0:
            search_string = "%20".join(args)
            response_text = f"<{MECHMARKET_BASE_URL}/search/?q=flair%3Aselling%20" + \
                            f"{search_string}&sort=new&restrict_sr=on>"
        await ctx.message.channel.send(response_text)

    @mechmarket.command()  # type: ignore
    async def add(self, ctx: commands.Context):
        '''add a mechmarketquery'''
        if not isinstance(ctx.message.channel, discord.DMChannel):
            return
        query = ' '.join(ctx.message.content.split()[2:])
        with db.bot_db:
            db.MechmarketQuery.get_or_create(
                user_id=ctx.message.author.id,
                search_string=query
            )
        dm_channel = await ctx.message.author.create_dm()
        await dm_channel.send(f"Scraping mechmarket to look for `{query}`")

    @mechmarket.command()  # type: ignore
    async def delete(self, ctx: commands.Context, *args):
        '''delete a MechmarketQuery'''
        if not isinstance(ctx.message.channel, discord.DMChannel):
            return
        with db.bot_db:
            for reason_id in args:
                try:
                    row_id = int(reason_id)
                except ValueError:
                    continue
                query = db.MechmarketQuery.get_by_id(row_id)
                if query:
                    if query.user_id != ctx.message.author.id:
                        await ctx.channel.send("Cannot delete other users query")
                        return
                    await ctx.channel.send(f"Deleting running query for `{query.search_string}`")
                    query.delete_instance()

    @mechmarket.command()  # type: ignore
    async def list(self, ctx: commands.Context):
        '''list mechmarket queries'''
        if not isinstance(ctx.message.channel, discord.DMChannel):
            return
        with db.bot_db:
            dm_channel = await ctx.message.author.create_dm()
            queries = db.MechmarketQuery.select().where(db.MechmarketQuery.user_id == ctx.message.author.id)
            # pylint: disable=not-an-iterable
            table = []
            for query in queries:
                table.append([query.id, query.search_string])
            msg_text = f"```{tabulate(table, headers=['query_id', 'query string'])}```"
            await dm_channel.send(msg_text)

    @mechmarket.command()  # type: ignore
    async def help(self, ctx: commands.Context):
        '''explain set of mechmarket commands'''
        if not isinstance(ctx.message.channel, discord.DMChannel):
            return
        await ctx.message.channel.send(f'```{EXPLANATION}```')

    @commands.Cog.listener()
    async def on_ready(self):
        '''mostly to start task loop on bringup'''
        try:
            self.scrape.start()  # pylint: disable=no-member
        except RuntimeError:
            pass


async def setup(client):
    '''setup'''
    await client.add_cog(MechmarketScraper(client))
