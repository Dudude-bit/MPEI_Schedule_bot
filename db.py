import mysql.connector
import parsing
import os

def create_connection():
    connection = None
    try :
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            passwd=os.getenv('passwd'),
            database='heroku_61c7527e4590fca'
        )
        connection.autocommit = True
    except mysql.connector.Error as e :
        print(e)
    return connection


def get_or_create_schedule(connection: mysql.connector.connection.MySQLConnection , group_of_user, weekday):
    cursor = connection.cursor()
    groupoid = parsing.get_groupoid(connection, group_of_user)
    query = f"""
    SELECT * FROM schedule WHERE groupoid = '{groupoid}' AND WeekDay = '{weekday}'
    """
    cursor.execute(query)
    schedule = cursor.fetchall()
    if schedule:
        return schedule
    else:
        return parsing.parsing_schedule(connection, groupoid, weekday)


#get_or_create_schedule(create_connection(), 'ТФ-14-19', 'Понедельник')
