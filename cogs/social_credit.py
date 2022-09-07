'''social credit application'''
import os

from discord.ext import commands

import db
import util

HELPER_ROLE = os.getenv('HELPER_ROLE')
MOD_ROLE = os.getenv('MOD_ROLE')


class SocialCredit(commands.Cog):
    '''social credit class'''

    def __init__(self, client):
        self.client = client

    # this is all spaghetti code because command groups weren't working for
    # some inexplicable reason. my apologies to anyone who has to read this
    # later. -zhol
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def socialcredit(self, ctx, *args):
        '''
        general socialcredit operations: read, add, remove
        Usage:         !socialcredit [user tag]
               [reply] !socialcredit

                       !socialcredit add [user tag] [amount]
               [reply] !socialcredit add [amount]

                       !socialcredit remove [user tag] [amount]
               [reply] !socialcredit remove [amount]
        '''
        amount = 0
        if len(args) > 0 and args[0] in ['add', 'remove']:
            # it's a subcommand
            if ctx.message.reference is not None:
                # replying to someone who is about to be ejected
                original_msg = await ctx.fetch_message(
                    ctx.message.reference.message_id)
                relevant_user = original_msg.author
                user_id = relevant_user.id
                amount = int(args[1])
            else:
                user_id = util.get_id_from_tag(args[1])
                amount = int(args[2])
        else:
            if ctx.message.reference is not None:
                # replying to someone who is about to be ejected
                original_msg = await ctx.fetch_message(
                    ctx.message.reference.message_id)
                relevant_user = original_msg.author
                user_id = relevant_user.id
            else:
                user_id = util.get_id_from_tag(args[0])
        with db.bot_db:
            credit_entry = db.SocialCredit.get_or_none(user_id=user_id)
            if not credit_entry:
                credit_entry = db.SocialCredit.create(user_id=user_id,
                                                      credit_amount=0)
            if amount != 0:
                if args[0] == 'add':
                    db.SocialCredit.update(
                        credit_amount=db.SocialCredit.credit_amount + amount).where(
                            db.SocialCredit.user_id == user_id
                        ).execute()
                elif args[0] == 'remove':
                    db.SocialCredit.update(
                        credit_amount=db.SocialCredit.credit_amount - amount).where(
                            db.SocialCredit.user_id == user_id
                        ).execute()
                credit_entry = db.SocialCredit.get_or_none(user_id=user_id)
        await ctx.channel.send(f'Social credit for user <@{user_id}> is '
                               f'{credit_entry.credit_amount} credits!')


async def setup(client):
    '''setup'''
    await client.add_cog(SocialCredit(client))
