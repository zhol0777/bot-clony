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


def create_tables():
    '''Re-create tables when DB is fresh'''
    with bot_db:
        bot_db.create_tables([RoleAssignment, WikiRootUrl,
                              WikiPage, WarningMemberReason,
                              UnejectTime, BannerPost])
        WikiRootUrl.get_or_create(
            indicator='primary',
            domain='https://mechkeys.me/'
        )
