from bs4 import BeautifulSoup
import requests
import re


def parsing_schedule(connection, groupoid, weekday) :
    url = 'https://mpei.ru/Education/timetable/Pages/table.aspx'
    html = requests.get(url, params={
        'groupoid': groupoid,
        'start': '2020.05.25'
    }).text
    r = BeautifulSoup(html, 'lxml')
    tr = r.find_all(class_='mpei-galaktika-lessons-grid-tbl').find('tbody')



def get_groupoid(connection, group_of_user) :
    cursor = connection.cursor()
    query = f"""
    SELECT groupoid FROM group_name_groupoid WHERE group_name = '{group_of_user}'
    """
    cursor.execute(query)
    groupoid = cursor.fetchall()
    if groupoid :
        return groupoid[0][0]
    url = requests.get(f'http://mpei.ru/Education/timetable/Pages/default.aspx?group={group_of_user}').url
    groupoid = re.findall(r'groupoid=(\d+)', url)[0]
    query = f"""
    INSERT INTO group_name_groupoid(group_name, groupoid) VALUES ('{group_of_user}', '{groupoid}')
    """
    cursor.execute(query)
    return groupoid

