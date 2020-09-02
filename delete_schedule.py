import redis
import requests
from bs4 import BeautifulSoup

from db import create_connection

redis_obj = redis.Redis()


def delete_schedule():
    connection = create_connection()
    cursor = connection.cursor()
    query = """
    DELETE FROM schedule
    """
    cursor.execute(query)
    redis_obj.delete('has_schedule')
    redis_obj.delete('slug_set')
    html = requests.get('https://mpei.ru/Education/timetable/Pages/default.aspx').text
    soup = BeautifulSoup(html, 'lxml')
    current_week = soup.find('div', class_='nb-week').text
    redis_obj.set('current_week', current_week)
    connection.close()


def main():
    delete_schedule()


if __name__ == '__main__':
    main()
