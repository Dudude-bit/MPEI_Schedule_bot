import mysql.connector


def create_connection():
    connection = None
    try :
        connection = mysql.connector.connect(
            host='eu-cdbr-west-03.cleardb.net',
            user='b792e6d9b972c5',
            passwd='5619ff16',
            database='heroku_61c7527e4590fca'
        )
        connection.autocommit = True
    except mysql.connector.Error as e :
        print(e)
    return connection