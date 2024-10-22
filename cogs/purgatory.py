'''
Handle purgatory role assignment requiring multiple helper votes and log the assignment
'''
import logging
import os

import asyncio
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

import util

MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
TOXIC_CONTAINMENT_CHANNEL = int(os.getenv('TOXIC_CONTAINMENT_CHANNEL', '0'))

log = logging.getLogger(__name__)
PURGE_COUNT = 80
PURGE_HISTORY_LIMIT = 400
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
            await self.easy_purge(ctx.guild, purged_user_id, ctx.channel)
            votes = self.vote_tracker.pop(purged_user_id)
            reasons = "\n".join([f"* {vote.get('reason')}" for vote in votes])

            embed = discord.Embed(color=discord.Colour.orange())
            embed.set_author(name="Hateful User Signal")
            embed.add_field(name="User", value=f'<@{purged_user_id}>')
            embed.add_field(name="Information", value='User has been given Razer Hate due to suspected hateful '
                                                      'messaging. Please check #deleted-messages to confirm.')
            embed.add_field(name="Reasons", value=reasons)  # type: ignore

            await util.apply_role(purgatory_member, purged_user_id, 'Razer Hate', reason)
            await notification_channel.send(embed=embed)  # type: ignore
        else:
            votes_required_for_purgatory = REQUIRED_VOTES - vote_count
            await ctx.channel.send(f"Vote recorded. {votes_required_for_purgatory} more vote"
                                    f"{'s' if votes_required_for_purgatory > 1 else ''} "
                                    "required to place user in purgatory")

    async def easy_purge(self, guild: discord.Guild, user_id: int, command_channel: discord.TextChannel):
        '''
        Purge messages from a specific user across all text channels
        '''
        total_deleted = 0
        messages_to_delete = []

        member = guild.get_member(user_id)

        # list of channels to purge, beginning with the one where the command was sent
        channels_to_purge = [command_channel] + [
            channel for channel in guild.channels
            if isinstance(channel, discord.TextChannel)
            and channel != command_channel
            and channel.permissions_for(member).send_messages
        ]
        # only messages younger than 14 days can be purged
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=14)

        for channel in channels_to_purge:
            print(f"Checking channel {channel.name}")
            print(channel.permissions_for(member))
            if total_deleted >= PURGE_COUNT:
                break
            try:
                async for message in channel.history(limit=PURGE_HISTORY_LIMIT):
                    if message.author.id == user_id and message.created_at > cutoff_time:
                        messages_to_delete.append(message)
                        if len(messages_to_delete) >= PURGE_COUNT - total_deleted:
                            break

                if messages_to_delete:
                    await channel.delete_messages(messages_to_delete)
                    batch_count = len(messages_to_delete)
                    total_deleted += batch_count
                    log.info("Purged %s messages in channel #%s for user %s. Total: %s",
                             batch_count, channel, user_id, total_deleted)
                    messages_to_delete.clear()



            except discord.errors.Forbidden:
                continue  # hopefully already deleted?
            except discord.errors.HTTPException as exc:
                log.error("Rate-limited during purge in #%s: %s", channel.name, exc)
                await asyncio.sleep(5)  # wait if rate-limited (i don't think this applies because i changed the logic)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                log.error("Error purging messages in #%s: %s", channel.name, exc)

        log.info("Total messages purged for user %s: %s", user_id, total_deleted)
        return total_deleted


async def setup(client):
    ''''setup'''
    await client.add_cog(Purgatory(client))
