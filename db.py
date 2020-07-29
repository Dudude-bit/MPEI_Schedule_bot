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


def get_or_create_schedule(connection: mysql.connector.connection.MySQLConnection , group_of_user, weekday):
    cursor = connection.cursor()
    groupoid = parsing.get_groupoid(connection, group_of_user)
    query = f"""
    SELECT num_object, auditory, object FROM schedule WHERE groupoid = '{groupoid}' AND WeekDay = '{weekday}'
    """
    cursor.execute(query)
    schedule = cursor.fetchall()
    if schedule:
        print('уже есть расписисание')
        return schedule
    else:
        print('расписание нету')
        schedule = parsing.parsing_schedule(connection, groupoid, weekday)
        return schedule


