'''
Scrape mechmarket using multireddit streaming for efficiency
'''
import asyncio
import logging
import os
import re
from collections import defaultdict

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
                    if flair_filter := FLAIR_FILTERS.get(subreddit_name):
                        if not self._matches_flair(submission, flair_filter):
                            continue
                    else:  # something from homelab sales, filter based on title
                        match subreddit_name:
                            case "homelabsales":
                                if not submission.title.startswith("[FS]"):
                                    continue
                            case _:
                                log.error("Avoiding processing post from r/%s, no filter defined", subreddit_name)
                                continue  # not within homelabsales, ignore

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
        # map user_id to list of matched query strings
        user_id_to_query_match = defaultdict(list)
        for market_query in market_queries:
            if self._matches_query(searchable_text, market_query.search_string):
                user_id_to_query_match[market_query.user_id].append(market_query.search_string)
        for user_id, matched_queries in user_id_to_query_match.items():
            if not matched_queries:
                continue
            try:
                reminded_user = await self.client.fetch_user(user_id)
                channel = await reminded_user.create_dm()
                text = (
                    f"## r/{market_name}: [{post_title}]({post_link})"
                    f"\n Match found for {len(matched_queries)} {'query' if len(matched_queries) == 1 else 'queries'}"
                )
                if timestamp:
                    text += f"\n - [Timestamp]({timestamp})"
                for query_string in matched_queries:
                    text += f"\n### {query_string}:\n{self._summarize_matches(searchable_text, query=query_string)}"
                await channel.send(text)
            except Exception:
                log.exception(f"Failed to notify user {user_id}")
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

    def _summarize_matches(self, input: str, query: str, space_to_retain: int = 40) -> str:  # noqa: PLR0912
        '''
        query modes:
        * ensure every word in a query appears in input, regardless of order
        * if in quotes, ensure that exact query appears in input
        '''
        keep_index = [False] * len(input)
        bold_index = [False] * len(input)
        # first part: build the index of characters to keep up
        # if we see a match, keep {space_to_retain} characters before/after, and bold the match itself
        if (query.startswith('"') and query.endswith('"')) or (query.startswith("'") and query.endswith("'")):
            reduced_query = query[1:-1]
            if not reduced_query:
                return ""  # this is a big error but we don't want to interrupt loop
            queries_to_search = [reduced_query]
        else:
            queries_to_search = query.split()
        for word in queries_to_search:
            for match in re.finditer(re.escape(word.lower()), input.lower()):
                # Keep context around the match
                for tru_idx in range(max(0, match.start() - space_to_retain),
                                        min(len(input), match.end() + space_to_retain)):
                    keep_index[tru_idx] = True
                # Bold the actual match
                for bold_idx in range(match.start(), match.end()):
                    bold_index[bold_idx] = True

        segments = []
        i = 0
        while i < len(input):
            if keep_index[i]:
                # Extract a continuous segment with its bold markers
                segment_parts = []
                in_bold = False

                while i < len(input) and keep_index[i]:
                    # Insert ** at bold state transitions
                    if bold_index[i] != in_bold:
                        segment_parts.append("**")
                        in_bold = bold_index[i]
                    segment_parts.append(input[i])
                    i += 1

                # Close any remaining bold tag
                if in_bold:
                    segment_parts.append("**")

                segments.append("".join(segment_parts))
            else:
                i += 1

        if not segments:
            return ""  # maybe should flag to user...
        joined_segments = " [...] ".join(segments)
        if not keep_index[0]:
            joined_segments = "[...] " + joined_segments
        if not keep_index[-1]:
            joined_segments += " [...]"
        return joined_segments

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
        dm_channel = await ctx.message.author.create_dm()
        query = ' '.join(ctx.message.content.split()[2:])
        if not query.strip():
            await dm_channel.send("Query cannot be empty")
            return
        with db.bot_db:
            db.MechmarketQuery.get_or_create(
                user_id=ctx.message.author.id,
                search_string=query
            )
        await dm_channel.send(f"Scraping reddit markets to look for `{query}`")

    @mechmarket.command()
    async def delete(self, ctx: commands.Context, *args):
        '''delete a MechmarketQuery'''
        if not isinstance(ctx.message.channel, discord.DMChannel):
            return
        queries_to_delete = []
        with db.bot_db:
            for reason_id in args:
                try:
                    row_id = int(reason_id)
                except ValueError:
                    continue
                query = db.MechmarketQuery.get_by_id(row_id)
                if query:
                    if query.user_id != ctx.message.author.id:
                        continue
                    queries_to_delete.append(f"{query.search_string}")
                    query.delete_instance()
        if queries_to_delete:
            await ctx.channel.send(
                f"Deleting running {'query' if len(queries_to_delete) > 2 else 'queries'}: "
                        f"```{'\n'.join(queries_to_delete)}```")

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
