from bs4 import BeautifulSoup
import requests
import re


def parsing_schedule(connection=None, groupoid=None, weekday=None) :
    week_dict = {
        'Пн' : 'Понедельник',
        'Вт' : 'Вторник',
        'Ср' : 'Среда',
        'Чт' : 'Четверг',
        'Пт' : 'Пятница'
    }
    url = 'https://mpei.ru/Education/timetable/Pages/table.aspx'
    html = requests.get(url, params={
        'groupoid' : groupoid,
        'start' : '2020.08.31'
    }).text
    r = BeautifulSoup(html, 'lxml')
    regexp = re.compile(r'(^\D{2}), \d{1,2}')
    all_weekdays = r.find('table').find_all('tr', text=regexp)
    ls_for_schedule = {}
    for i in all_weekdays :
        ls_for_schedule[week_dict[regexp.findall(i.text)[0]]] = []
        tr = i.find_next_sibling()
        while True :
            try :
                ls_for_schedule[week_dict[regexp.findall(i.text)[0]]].append(
                    tr.find(class_='mpei-galaktika-lessons-grid-name').text)
                tr = tr.find_next_sibling()
                if regexp.match(tr.text) :
                    break
            except AttributeError as e:
                print(e)
                break
    print(ls_for_schedule)



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
