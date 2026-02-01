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


class Reminder(BaseModel):
    '''tracking a reminder and when to send'''
    user_id = peewee.BigIntegerField()
    reminder_epoch_time = peewee.BigIntegerField()
    reason = peewee.CharField()
    message_url = peewee.BigIntegerField()


def create_tables():
    '''Re-create tables when DB is fresh'''
    with bot_db:
        bot_db.create_tables([Reminder,])
