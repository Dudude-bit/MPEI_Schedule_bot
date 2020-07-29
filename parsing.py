from bs4 import BeautifulSoup
import requests
import re


def parsing_schedule(connection, groupoid, weekday) :
    cursor = connection.cursor()
    week_dict = {
        'Пн' : 'Понедельник',
        'Вт' : 'Вторник',
        'Ср' : 'Среда',
        'Чт' : 'Четверг',
        'Пт' : 'Пятница'
    }
    time_subj_num = {
        '09:20 - 10:55' : 1,
        '11:10 - 12:45' : 2,
        '13:45 - 15:20' : 3,
        '15:35 - 17:10' : 4
    }
    url = 'https://mpei.ru/Education/timetable/Pages/table.aspx'
    with open('q.html', 'r', encoding='utf8') as f :
        html = f.read()
    r = BeautifulSoup(html, 'lxml')
    regexp = re.compile(r'(^\D{2}), \d{1,2}')
    all_weekdays = r.find('table').find_all('tr', text=regexp)
    ls_for_schedule = {}
    for i in all_weekdays :
        ls_for_schedule[week_dict[regexp.findall(i.text)[0]]] = []
        tr = i.find_next_sibling()
        while True :
            try :
                subject_name = tr.find(class_='mpei-galaktika-lessons-grid-name').text
                teacher_name = tr.find(class_='mpei-galaktika-lessons-grid-pers').text
                auditory = tr.find(class_='mpei-galaktika-lessons-grid-room').text
                time = tr.find(class_='mpei-galaktika-lessons-grid-time').text
                object_type = tr.find(class_='mpei-galaktika-lessons-grid-type').text
                ls_for_schedule[week_dict[regexp.findall(i.text)[0]]].append(
                    (time_subj_num[time], subject_name, auditory, teacher_name, object_type))
                tr = tr.find_next_sibling()
                if regexp.match(tr.text) :
                    break
            except AttributeError as e :
                break
    for weekday in ls_for_schedule :
        for subject in ls_for_schedule[weekday] :
            query = f"""
            INSERT INTO schedule(WeekDay, num_object, groupoid, auditory, teacher, object, object_type) VALUES {weekday, subject[0], groupoid, subject[2], subject[3], subject[1], subject[4]};
            """
            cursor.execute(query)



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
