'''
Module to handle the few DB operations we have
'''
import os
import sys

try:
    from playhouse.sqlcipher_ext import SqlCipherDatabase
except ImportError:
    SqlCipherDatabase = None  # fallback: defined below if needed

import peewee

PASSPHRASE = os.getenv('DATABASE_PASSPHRASE', '')
DB_PATH = 'encrypted.db'

# Encryption-at-rest is required. Never silently fall back to a plaintext DB.
if SqlCipherDatabase is None:
    print("FATAL: SQLCipher support not available (install 'sqlcipher3'). "
          "Refusing to run with an unencrypted database.", file=sys.stderr)
    sys.exit(1)
if not PASSPHRASE:
    print("FATAL: DATABASE_PASSPHRASE environment variable is not set.", file=sys.stderr)
    sys.exit(1)
bot_db = SqlCipherDatabase(DB_PATH, passphrase=PASSPHRASE)

bot_db.execute_sql('PRAGMA journal_mode=WAL;')


class BaseModel(peewee.Model):
    '''base model to connect to single database'''
    class Meta:  # pylint: disable=too-few-public-methods
        '''connects model to db'''
        database = bot_db


class RoleAssignment(BaseModel):
    '''assignment of role to user, keyed by hashed user ID for privacy'''
    hashed_user_id = peewee.CharField()
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


class Reminder(BaseModel):
    '''tracking a reminder and when to send'''
    user_id = peewee.BigIntegerField()
    reminder_epoch_time = peewee.BigIntegerField()
    reason = peewee.CharField()
    message_url = peewee.BigIntegerField()


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
    # todo: migrate this to IntegerField
    tracking_message_id = peewee.CharField(null=True)
    class Meta:
        indexes = (
            (('message_hash', 'user_id'), True),  # unique composite key
        )


class OptOut(BaseModel):
    '''users who opted out of sticky role tracking'''
    hashed_user_id = peewee.CharField(unique=True)


def create_tables():
    '''Re-create tables when DB is fresh'''
    with bot_db:
        bot_db.create_tables([RoleAssignment, WikiRootUrl,
                              WikiPage,
                              UnejectTime, BannerPost,
                              Reminder,
                              SanitizedChannel,
                              SillyPage, ThockTrackingChannel,
                              MechmarketPost, MechmarketQuery,
                              MessageIdentifier, OptOut])
        if not WikiRootUrl.select():
            WikiRootUrl.get_or_create(
                indicator='primary',
                domain='https://mechkeys.me/'
            )
