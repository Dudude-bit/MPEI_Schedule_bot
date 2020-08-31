import os

import mysql.connector
import redis

import exceptions
import parsing


def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            passwd=os.getenv('passwd'),
            database='mpei_bot'
        )
        connection.autocommit = True
    except mysql.connector.Error as e :
        print(e)
    return connection


def get_or_create_schedule(connection: mysql.connector.connection.MySQLConnection, weekday, redis_obj: redis.Redis,
                           callback_query) :
    cursor = connection.cursor()
    groupoid = redis_obj.get(f'user_groupoid:{callback_query.from_user.id}').decode('utf8')
    print(groupoid)
    query = f"""
    SELECT num_object, auditory, object, slug FROM schedule WHERE groupoid = '{groupoid}' AND WeekDay = '{weekday}'
    """
    cursor.execute(query)
    schedule = cursor.fetchall()
    members_tuple = tuple(map(lambda x : x.decode('utf8'), redis_obj.smembers('has_schedule')))
    if schedule :
        return schedule
    elif groupoid in members_tuple :
        raise exceptions.MpeiBotException(message='Хмм... Походу ты отдыхаешь в этот день 😎')
    else :
        schedule = parsing.parsing_schedule(connection, groupoid, weekday, redis_obj)
        return schedule


def get_information_about_subject(connection, slug) :
    cursor = connection.cursor()
    query = f"""
    SELECT * FROM schedule WHERE slug = '{slug}'
    """
    cursor.execute(query)
    information = cursor.fetchall()
    return information
