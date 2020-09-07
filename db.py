import os

import psycopg2
import redis

import exceptions
import parsing


def create_connection():
    return psycopg2.connect(dbname='mpei_bot', user='mpei_bot_user', password=os.getenv('passwd'), host='localhost')


def get_or_create_schedule(connection, weekday, redis_obj: redis.Redis,
                           callback_query, week_num):
    groupoid = redis_obj.get(f'user_groupoid:{callback_query.from_user.id}').decode('utf8')
    query = f"""
    SELECT num_object, auditory, object, slug FROM schedule WHERE groupoid = '{groupoid}' AND WeekDay = '{weekday}' AND week = '{week_num}'
    """
    with connection as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
    schedule = cursor.fetchall()
    members_tuple = tuple(map(lambda x: x.decode('utf8'), redis_obj.smembers('has_schedule')))
    if schedule:
        return schedule
    elif groupoid in members_tuple:
        raise exceptions.MpeiBotException(message='Хмм... Походу Вы отдыхаете в этот день 😎')
    else:
        parsing.parsing_schedule(connection, groupoid, redis_obj)
        query = f"""
        SELECT num_object, auditory, object, slug FROM schedule WHERE groupoid = '{groupoid}' AND WeekDay = '{weekday}' AND week = '{week_num}'
        """
        with connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                schedule = cursor.fetchall()
        if schedule:
            return schedule
        raise exceptions.MpeiBotException(message='Хмм... Походу Вы отдыхаете в этот день 😎')


def get_information_about_subject(connection, slug):
    with connection as conn:
        with conn.cursor() as cursor:
            query = f"""
            SELECT * FROM schedule WHERE slug = '{slug}'
            """
            cursor.execute(query)
            information = cursor.fetchall()
    return information
