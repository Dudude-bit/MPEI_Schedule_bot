import redis

from db import create_connection

redis_obj = redis.Redis()


def delete_schedule():
    cursor = create_connection().cursor()
    query = """
    DELETE FROM schedule
    """
    cursor.execute(query)
    redis_obj.delete('has_schedule')
