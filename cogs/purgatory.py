'''
Handle purgatory role assignment requiring multiple helper votes and log the assignment
'''
import logging
import os

import discord
from discord.ext import commands

import util

MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
TOXIC_CONTAINMENT_CHANNEL = int(os.getenv('TOXIC_CONTAINMENT_CHANNEL', '0'))

log = logging.getLogger(__name__)
PURGE_HISTORY_LIMIT = 50
REQUIRED_VOTES = 2


class Purgatory(commands.Cog):
    '''Place users in purgatory'''
    def __init__(self, client: discord.Client):
        self.client = client
        self.vote_tracker: dict[int, list[dict[str, str | int]]] = {}
        # {
        #   261759221: [  # doomed user ID
        #       {
        #           'voter_id': '236537142',  # helper user ID
        #           'reason': 'he is stinky'
        #       },
        #       {
        #           'voter_id': '281502869',
        #           'reason': 'he has booger brain'
        #       },
        #   ],
        # }

    @commands.command()
    @commands.has_any_role(HELPER_ROLE_ID, MOD_ROLE_ID)
    async def purgatory(self, ctx: commands.Context, *args):  # pylint: disable=too-many-locals,too-many-branches
        '''
        Usage: !purgatory [@ user tag] [reason...]
        [reply] !purgatory [reason...]
        Requires 2 helpers to vote before applying purgatory role
        '''
        if not ctx.guild:
            return

        notification_channel = self.client.get_channel(TOXIC_CONTAINMENT_CHANNEL)
        if not notification_channel:
            return

        helper_id: int = ctx.author.id

        if not args:
            if ctx.message.reference:
                await util.handle_error(ctx, "Please provide a reason for purgatory.")
            else:
                await util.handle_error(ctx, "Please provide a user to place in purgatory.")
            return

        if ctx.message.reference and ctx.message.reference.message_id:
            # replying to someone who is about to be placed in purgatory
            original_msg = await ctx.fetch_message(
                ctx.message.reference.message_id
            )
            purgatory_user = original_msg.author
            purged_user_id = purgatory_user.id
            reason = ' '.join(args)
        else:
            # purgatory command was not a reply
            purged_user_id = util.get_id_from_tag(args[0])
            reason = ' '.join(args[1:])

        if not reason:
            await util.handle_error(ctx, "Must provide reason to put user in purgatory")
            return

        try:
            purgatory_member = await ctx.guild.fetch_member(purged_user_id)
        except discord.errors.NotFound:
            await util.handle_error(ctx, "Could not find guild member to throw into purgatory")
            return

        if ctx.author.id in [vote.get('voter_id') for vote in self.vote_tracker.get(purged_user_id, [])]:
            await util.handle_error(ctx, "You have already voted to place this user in purgatory")
            return

        if not self.vote_tracker.get(purged_user_id):  # TODO: defaultdict
            self.vote_tracker[purged_user_id] = []
        self.vote_tracker[purged_user_id].append({'voter_id': helper_id, 'reason': reason})

        vote_count = len(self.vote_tracker[purged_user_id])

        if vote_count >= REQUIRED_VOTES:
            await self.easy_purge(ctx.guild, purged_user_id)
            votes = self.vote_tracker.pop(purged_user_id)
            reasons = "\n".join([f"* {vote.get('reason')}" for vote in votes])

            embed = discord.Embed(color=discord.Colour.orange())
            embed.set_author(name="Hateful User Signal")
            embed.add_field(name="User", value=f'<@{purged_user_id}>')
            embed.add_field(name="Information", value='User has been given Razer Hate due to suspected hateful '
                                                      'messaging. Please check #deleted-messages to confirm.')
            embed.add_field(name="Reasons", value=reasons)  # type: ignore

            await util.apply_role(purgatory_member, purged_user_id, 'Razer Hate', reason)
            await notification_channel.send(content=content, embed=embed)  # type: ignore
        else:
            votes_required_for_purgatory = REQUIRED_VOTES - vote_count
            await ctx.channel.send(f"Vote recorded. {votes_required_for_purgatory} more vote"
                                    f"{'s' if votes_required_for_purgatory > 1 else ''} "
                                    "required to place user in purgatory")

    async def easy_purge(self, guild: discord.Guild, user_id):
        '''
        purge all messages from some user within some limit
        '''
        for channel in guild.channels:
            if not isinstance(channel, discord.TextChannel):
                continue
            try:
                async for message in channel.history(limit=PURGE_HISTORY_LIMIT):
                    if message.author.id == user_id:
                        try:
                            await message.delete()
                        except discord.NotFound:
                            pass  # hopefully already deleted?
            except discord.errors.Forbidden:
                pass
            except Exception as exc:  # pylint: disable=broad-exception-caught
                log.error("Cant purge from %s due to %s...", channel.name, exc)


async def setup(client):
    ''''setup'''
    await client.add_cog(Purgatory(client))
