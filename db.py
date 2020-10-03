import os

import psycopg2
from psycopg2.extras import NamedTupleCursor
import redis

import exceptions
import parsing


def create_connection():
    return psycopg2.connect(user='postgres', dbname='mpei_bot',password=os.getenv('passwd'), host='db_postgres')


def get_or_create_schedule(connection, weekday, redis_obj: redis.Redis,
                           callback_query, week_num):
    groupoid = redis_obj.get(f'user_groupoid:{callback_query.from_user.id}').decode('utf8')
    query = f"""
        SELECT num_object, auditory, object, slug FROM schedule WHERE groupoid = '{groupoid}' AND WeekDay = '{weekday}' AND week = '{week_num}' ORDER BY num_object
        """
    with connection as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(query)
            schedule = cursor.fetchall()
    members_tuple = tuple(map(lambda x: x.decode('utf8'), redis_obj.smembers('has_schedule')))
    if schedule:
        return schedule
    elif groupoid in members_tuple:
        raise exceptions.MpeiBotException(message='Хмм... Походу Вы отдыхаете в этот день 😎')
    else:
        parsing.parsing_schedule(connection, groupoid, redis_obj)
        with connection as conn:
            with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
                cursor.execute(query)
                schedule = cursor.fetchall()
        if schedule:
            return schedule
        raise exceptions.MpeiBotException(message='Хмм... Походу Вы отдыхаете в этот день 😎')


def get_information_about_subject(connection, slug):
    with connection as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
            query = f"""
            SELECT * FROM schedule WHERE slug = '{slug}'
            """
            cursor.execute(query)
            information = cursor.fetchall()
    return information
