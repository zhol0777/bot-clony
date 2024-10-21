'''
Module to handle the few DB operations we have
'''
import peewee

bot_db = peewee.SqliteDatabase('bot.db')


class BaseModel(peewee.Model):
    '''base model to connect to single database'''
    class Meta:  # pylint: disable=too-few-public-methods
        '''connects model to db'''
        database = bot_db

class PurgatoryVote(BaseModel):
    '''
    tracking votes for putting a user in purgatory
    requires multiple helpers to agree before applying role
    '''
    user_id = peewee.IntegerField()
    helper_id = peewee.IntegerField()
    vote_epoch_time = peewee.BigIntegerField()
    reason = peewee.CharField()


class WarningMemberReason(BaseModel):
    '''
    tracking every instance a user gave a mod a reason to give them a ban/eject
    '''
    user_id = peewee.IntegerField()
    reason = peewee.CharField()
    message_url = peewee.CharField()  # url pointing to sus message
    for_eject = peewee.BooleanField()  # if reason comes from helper
    for_ban = peewee.BooleanField()  # if reason comes from mod


class RoleAssignment(BaseModel):
    '''assignment of role to user to track for re-joins'''
    user_id = peewee.IntegerField()
    role_name = peewee.CharField()


class WikiPage(BaseModel):
    '''pages for community wikis
    :param page: page/link posted
    :param shortname: sub-command used to invoke posting the page,
                      ex. !wiki stabs -> https://mechkeys.me/STABILIZERS.html
    :param goes_to_root_domain: if True, then append page field to WikiRootUrl
                                if False, then post page field as-is
    '''
    page = peewee.CharField()  # STABILIZERS.html/https://docs.google.com/...
    shortname = peewee.CharField(unique=True)  # stabs or switches
    goes_to_root_domain = peewee.BooleanField()


class SillyPage(BaseModel):
    '''pages for silly text responses that aren't technically wiki pages
    :param page: page/link posted
    :param shortname: sub-command used to invoke posting the page,
                      ex. !silly foo -> "bar"
    '''
    response_text = peewee.CharField()  # haha heres a funny response
    shortname = peewee.CharField(unique=True)  # stabs or switches


class WikiRootUrl(BaseModel):
    '''table to define the domain for the community wiki
    :param indicator: indicates which row is the true root domain
                      NOTE: wiki.py filters for true root domain by finding
                            row with indicator=='primary'
    :param domain: the URL pointing to the community wiki
    '''
    indicator = peewee.CharField(unique=True)  # primary
    domain = peewee.CharField()  # https://mechkeys.me/


class UnejectTime(BaseModel):
    '''basic entry for a user ID and when they will be unejected
       so that instead of running async waits, loop through db entries
       every minute'''
    user_id = peewee.BigIntegerField()
    uneject_epoch_time = peewee.BigIntegerField()


class BannerPost(BaseModel):
    '''simple way to track message pinned for banner so it can be unpinned later'''
    message_id = peewee.BigIntegerField()


class SocialCredit(BaseModel):
    '''tracking social credit for a user'''
    user_id = peewee.BigIntegerField()
    credit_amount = peewee.FloatField()


class Reminder(BaseModel):
    '''tracking a reminder and when to send'''
    user_id = peewee.BigIntegerField()
    reminder_epoch_time = peewee.BigIntegerField()
    reason = peewee.CharField()
    message_url = peewee.BigIntegerField()


class SuspiciousUser(BaseModel):
    '''tracking bogus user'''
    user_id = peewee.BigIntegerField()
    join_epoch_time = peewee.BigIntegerField()


class KickedUser(BaseModel):
    '''tracking user that has been kicked three times for suspicious behavior'''
    user_id = peewee.BigIntegerField()
    kick_count = peewee.BigIntegerField()


class BannedUser(BaseModel):
    '''tracking user banned by botpurge functionality to prevent fetch_ban() lookup'''
    user_id = peewee.BigIntegerField(unique=True)


class SanitizedChannel(BaseModel):
    '''only channel ID is tracked if auto-sanitizer should be run there'''
    channel_id = peewee.BigIntegerField()


class ThockTrackingChannel(BaseModel):
    '''only channel ID is tracked if thock tracker should be run there'''
    channel_id = peewee.BigIntegerField()
    counter = peewee.BigIntegerField()


class MechmarketPost(BaseModel):
    '''every reddit post gets a unique ID?'''
    post_id = peewee.CharField()


class MechmarketQuery(BaseModel):
    '''basic search to run through page content to look for a match'''
    user_id = peewee.BigIntegerField()
    search_string = peewee.CharField()


class StupidMessage(BaseModel):
    '''part of a message you do not want to see anymore'''
    message_text = peewee.CharField()
    response_text = peewee.CharField()


class MessageIdentifier(BaseModel):
    '''
    messages are identified based of content hashed, and message author
    one cog will see if they are fired in multiple channels in short
    succession in case there is a bot that needs to be muted
    '''
    message_hash = peewee.CharField()
    user_id = peewee.BigIntegerField()
    created_at = peewee.DateTimeField()
    instance_count = peewee.BigIntegerField()

    # if instance count exceeds some threshold, we send some message to
    # a bot channel or something to explain to user and mods why they
    # they got muted
    tracking_message_id = peewee.CharField(null=True)


def create_tables():
    '''Re-create tables when DB is fresh'''
    with bot_db:
        bot_db.create_tables([RoleAssignment, WikiRootUrl,
                              WikiPage, WarningMemberReason,
                              UnejectTime, BannerPost,
                              SocialCredit, Reminder,
                              SuspiciousUser, KickedUser,
                              BannedUser, SanitizedChannel,
                              SillyPage, ThockTrackingChannel,
                              MechmarketPost, MechmarketQuery,
                              StupidMessage, MessageIdentifier,
                              PurgatoryVote])
        if not WikiRootUrl.select():
            WikiRootUrl.get_or_create(
                indicator='primary',
                domain='https://mechkeys.me/'
            )
