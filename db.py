import mysql.connector
import os
import parsing
import os


def create_connection():
    connection = None
    try :
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


def get_or_create_schedule(connection: mysql.connector.connection.MySQLConnection , weekday, redis_obj, callback_query):
    cursor = connection.cursor()
    groupoid = redis_obj.get(f'user_groupoid:{callback_query.from_user.id}').decode('utf8')
    print(groupoid)
    query = f"""
    SELECT num_object, auditory, object, id FROM schedule WHERE groupoid = '{groupoid}' AND WeekDay = '{weekday}'
    """
    cursor.execute(query)
    schedule = cursor.fetchall()
    if schedule:
        return schedule
    else:
        schedule = parsing.parsing_schedule(connection, groupoid, weekday)
        return schedule


def get_information_about_subject(connection, id):
    cursor = connection.cursor()
    query = f"""
    SELECT * FROM schedule WHERE id = {id}
    """
    cursor.execute(query)
    information = cursor.fetchall()
    return information


