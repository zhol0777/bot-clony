'''
Scrape mechmarket using multireddit streaming for efficiency
'''
from asyncpraw.models.reddit.submission import Submission
import asyncio
import logging
import os
import re
from functools import lru_cache

import asyncpraw
import discord
from asyncpraw import models as praw_models
from discord.ext import commands
from tabulate import tabulate
from urlextract import URLExtract

import db
import util

MECHMARKET_BASE_URL = 'https://old.reddit.com/r/mechmarket'
BACKOFF_TIME_MS = 10000

SUBREDDITS = ['mechmarket', 'hardwareswap', 'homelabsales']

# Flair filters for each subreddit
FLAIR_FILTERS = {
    'mechmarket': 'Selling',
    'hardwareswap': 'SELLING',
    # 'homelabsales': '[FS]'  # this is in the title
}

EXPLANATION = '''
mechmarket:
  mechmarket        Searches for something for sale on mechmarket/hws/hls
                    Usage: !mechmarket
                           !mechmarket qk65
  mechmarket add    Adds a query for something on the markets to message you when a new posting is found
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
    '''scrape mechmarket posts from reddit using multireddit streaming'''
    def __init__(self, client: discord.Client):
        self.client = client
        self.reddit = None
        self.stream_tasks = []
        self._shutdown_event = asyncio.Event()
        self.extractor = URLExtract()

    @commands.Cog.listener()
    async def on_ready(self):
        '''initialize reddit client and start subreddit streaming'''
        try:
            self.reddit = asyncpraw.Reddit(
                username=os.getenv('REDDIT_USERNAME', ''),
                password=os.getenv('REDDIT_PASSWORD', ''),
                client_id=os.getenv('REDDIT_CLIENT_ID', ''),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET', ''),
                user_agent=util.MECHMARKET_SCRAPE_HEADERS['user-agent']
            )
            self.reddit.read_only = True

            # Start streaming task for each subreddit
            for subreddit_name in SUBREDDITS:
                task = asyncio.create_task(
                    self._stream_subreddit(subreddit_name),
                    name=f"stream_{subreddit_name}"
                )
                self.stream_tasks.append(task)

            log.info(f"Started streaming for {len(SUBREDDITS)} subreddits")

        except Exception:
            log.exception("Failed to initialize mechmarket scraper")

    async def cog_unload(self):
        '''graceful shutdown'''
        self._shutdown_event.set()

        # Cancel all stream tasks
        for task in self.stream_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if self.reddit:
            try:
                await self.reddit.close()
            except Exception:
                log.exception("Error closing reddit client")

    async def _stream_subreddit(self, subreddit_name: str):
        '''stream posts from a single subreddit'''
        while not self._shutdown_event.is_set():
            if not self.reddit:
                log.error("Reddit client not initialized")
                await asyncio.sleep(BACKOFF_TIME_MS / 1000)
                continue

            try:
                subreddit = await self.reddit.subreddit(subreddit_name)
                log.info(f"Starting stream for r/{subreddit_name}")

                async for submission in subreddit.stream.submissions(skip_existing=True):
                    if self._shutdown_event.is_set():
                        break

                    # Check if post matches flair filter
                    flair_filter = FLAIR_FILTERS.get(subreddit_name)
                    if flair_filter and not self._matches_flair(submission, flair_filter):
                        continue

                    # Process the post
                    log.info("Processing reddit market post ID %s from r/%s", submission.id, subreddit_name)
                    await self._process_post(submission, subreddit_name)

            except asyncio.CancelledError:
                log.info(f"Stream for r/{subreddit_name} cancelled")
                raise
            except Exception:
                log.exception("Error in stream for r/%s, restarting...", subreddit_name)
                await asyncio.sleep(BACKOFF_TIME_MS / 1000)

    def _matches_flair(self, submission: praw_models.Submission, flair_filter: str) -> bool:
        '''check if submission matches the expected flair'''
        # For homelabsales, check if title contains [FS]
        if flair_filter == '[FS]':
            return '[FS]' in submission.title

        # Get flair text from submission
        flair_text = ""
        if hasattr(submission, 'link_flair_text') and submission.link_flair_text:
            flair_text = submission.link_flair_text

        # Check if flair text contains filter
        return flair_filter.lower() in flair_text.lower()

    async def _process_post(self, submission: praw_models.Submission, market_name: str):
        '''process a single reddit post against all user queries'''
        post_id = submission.id
        post_link = submission.url
        post_title = submission.title

        # Check if already processed
        with db.bot_db:
            if db.MechmarketPost.get_or_none(post_id=post_id):
                return

        # Extract post text and timestamp
        post_text = ""
        if hasattr(submission, 'selftext') and submission.selftext:
            post_text = submission.selftext.replace('\n', ' ')

        # Combine title and text for searching
        searchable_text = f"{post_title} {post_text}"

        # Try to extract timestamp URL
        timestamp = None
        urls = self.extractor.find_urls(post_text)
        if urls:
            timestamp = urls[0]

        # Match against all queries
        with db.bot_db:
            market_queries: list[db.MechmarketQuery] = list(db.MechmarketQuery.select())
        for market_query in market_queries:
            if self._matches_query(searchable_text, market_query.search_string):
                try:
                    reminded_user = await self.client.fetch_user(market_query.user_id)
                    channel = await reminded_user.create_dm()
                    text = (
                        f"Match found for query: {market_query.search_string}\n"
                        f"r/{market_name}: [{post_title}]({post_link})\n"
                    )
                    if timestamp:
                        text += f" - [Timestamp]({timestamp})"
                    await channel.send(text)
                except Exception:
                    log.exception(f"Failed to notify user {market_query.user_id}")
        with db.bot_db:
            # Mark as processed
            db.MechmarketPost.insert(post_id=post_id).execute()

    def _matches_query(self, text: str, query: str) -> bool:
        '''check if text matches a search query'''
        # Check for exact search if enclosed in quotes
        if query.startswith('"') and query.endswith('"'):
            return query[1:-1].lower() in text.lower()

        # Check if all words are present (AND logic)
        if all(word.lower() in text.lower() for word in query.split()):
            return True
        # check for text as regex
        regex = self.regex_compilation_cached(query)
        return regex.search(text) is not None

    @lru_cache
    def regex_compilation_cached(self, query_text: str) -> re.Pattern:
        return re.compile(query_text)

    @commands.group()
    async def mechmarket(self, ctx: commands.Context):
        '''response for people who will not do price checks themselves'''
        if ctx.invoked_subcommand and \
                ctx.invoked_subcommand.name in {'add', 'list', 'delete', 'help'}:
            return
        response_text = MECHMARKET_BASE_URL
        args = ctx.message.content.split()[1:]
        if len(args) > 0:
            search_string = "%20".join(args)
            response_text = f"<{MECHMARKET_BASE_URL}/search/?q=flair%3Aselling%20" + \
                            f"{search_string}&sort=new&restrict_sr=on>"
        await ctx.message.channel.send(response_text)

    @mechmarket.command()
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
        await dm_channel.send(f"Scraping reddit markets to look for `{query}`")

    @mechmarket.command()
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

    @mechmarket.command()
    async def list(self, ctx: commands.Context):
        '''list mechmarket queries'''
        if not isinstance(ctx.message.channel, discord.DMChannel):
            return
        dm_channel = await ctx.message.author.create_dm()
        with db.bot_db:
            queries = list(db.MechmarketQuery.select().where(db.MechmarketQuery.user_id == ctx.message.author.id))
        table = [[query.id, query.search_string] for query in queries]
        msg_text = f"```{tabulate(table, headers=['query_id', 'query string'])}```"
        await dm_channel.send(msg_text)

    @mechmarket.command()
    async def help(self, ctx: commands.Context):
        '''explain set of mechmarket commands'''
        if not isinstance(ctx.message.channel, discord.DMChannel):
            return
        await ctx.message.channel.send(f'```{EXPLANATION}```')


async def setup(client):
    '''setup'''
    await client.add_cog(MechmarketScraper(client))
