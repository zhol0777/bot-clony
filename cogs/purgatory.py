'''
Handle purgatory role assignment requiring multiple helper votes and log the assignment
'''
import time
import logging
import os
from cogs.eject import ZHOLBOT_CHANNEL_ID
from discord.ext import commands
import db
import util

MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', '0'))
HELPER_ROLE_ID = int(os.getenv('HELPER_ROLE_ID', '0'))
ZHOLBOT_CHANNEL_ID = int(os.getenv('ZHOLBOT_CHANNEL_ID', '0'))
log = logging.getLogger(__name__)

REQUIRED_VOTES = 2

class Purgatory(commands.Cog):
    '''Place users in purgatory'''
    def __init__(self, client):
        self.client = client
        self.guild = None

    @commands.command()
    @commands.has_any_role(HELPER_ROLE_ID, MOD_ROLE_ID)
    async def purgatory(self, ctx: commands.Context, *args):
        f'''
        Usage: !purgatory [@ user tag] [reason...]
        [reply] !purgatory [reason...]
        Requires {REQUIRED_VOTES} helpers to vote before applying purgatory role
        '''
        if not ctx.guild:
            return

        helper_id = ctx.author.id
        current_time = int(time.time())

        if not args:
            if ctx.message.reference:
                await ctx.channel.send("Please provide a reason for purgatory.")
            else:
                await ctx.channel.send("Please provide a user to place in purgatory.")
            return


        if ctx.message.reference and ctx.message.reference.message_id:
            # replying to someone who is about to be placed in purgatory
            original_msg = await ctx.fetch_message(
                ctx.message.reference.message_id
            )
            purgatory_user = original_msg.author
            user_id = purgatory_user.id
            reason = ' '.join(args)
        else:
            # purgatory command was not a reply
            user_id = util.get_id_from_tag(args[0])
            reason = ' '.join(args[1:])

        purgatory_member = await ctx.guild.fetch_member(user_id)
        if not purgatory_member:
            return

        if not reason:
            await ctx.channel.send("Please provide a reason for purgatory.")
            return


        with db.bot_db:
            existing_vote = db.PurgatoryVote.get_or_none(helper_id=helper_id, user_id=user_id)
            if existing_vote:
                await ctx.channel.send("You have already voted to place this user in purgatory.")
                return

            db.PurgatoryVote.create(
                user_id=user_id,
                helper_id=helper_id,
                vote_epoch_time=current_time,
                reason=reason
            )

            vote_count = db.PurgatoryVote.select().where(db.PurgatoryVote.user_id == user_id).count()

            if vote_count >= REQUIRED_VOTES:
                await util.apply_role(purgatory_member, user_id, 'purgatory', reason)

                votes = db.PurgatoryVote.select().where(db.PurgatoryVote.user_id == user_id)

                reasons = "\n".join([f"- {vote.reason}" for vote in votes])

                await ctx.channel.send(
                    f"User <@{user_id}> has been placed in purgatory.\n"
                    f"Reasons:\n{reasons}"
                )

                db.PurgatoryVote.delete().where(db.PurgatoryVote.user_id == user_id).execute()

            else:
                votes_required_for_purgatory = REQUIRED_VOTES - vote_count
                await ctx.channel.send(f"Vote recorded. {votes_required_for_purgatory} more vote{'s' if votes_required_for_purgatory > 1 else ''} required to place user in purgatory")

async def setup(client):
    ''''setup'''
    await client.add_cog(Purgatory(client))
