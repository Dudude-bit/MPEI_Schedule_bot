from bs4 import BeautifulSoup
import requests
import re
import exceptions

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
    template_dict = {
        'name': 'Отдых',
        'teacher': ' ',
        'room': 'Дом',
        'num': '1',
        'type': ' '
    }
    ls_for_schedule = {'Понедельник' : [template_dict],
                       'Вторник' : [template_dict],
                       'Среда' : [template_dict],
                       'Четверг' : [template_dict],
                       'Пятница' : [template_dict],
                       'Суббота' : [template_dict],
                       }
    for i in all_weekdays :
        ls_for_schedule[week_dict[regexp.findall(i.text)[0]]] = []
        tr = i.find_next_sibling()
        while True :
            subject_dict = {}
            try :
                subject_dict['name'] = tr.find(class_='mpei-galaktika-lessons-grid-name').text
                subject_dict['teacher'] = tr.find(class_='mpei-galaktika-lessons-grid-pers').text
                subject_dict['room'] = tr.find(class_='mpei-galaktika-lessons-grid-room').text
                subject_dict['num'] = time_subj_num[tr.find(class_='mpei-galaktika-lessons-grid-time').text]
                subject_dict['type'] = tr.find(class_='mpei-galaktika-lessons-grid-type').text
                ls_for_schedule[week_dict[regexp.findall(i.text)[0]]].append(subject_dict)
                tr = tr.find_next_sibling()
                if regexp.match(tr.text) :
                    break
            except AttributeError:
                break
    for item in ls_for_schedule :
        for subject in ls_for_schedule[item] :
            query = f"""
            INSERT INTO schedule(WeekDay, num_object, groupoid, auditory, teacher, object, object_type) 
            VALUES 
            {item, subject['num'], groupoid, subject['room'], subject['teacher'], subject['name'], subject['type']};
            """
            cursor.execute(query)
    query = f"""
        SELECT num_object, auditory, object, id FROM schedule WHERE groupoid = '{groupoid}' AND WeekDay = '{weekday}'
        """
    cursor.execute(query)
    schedule = cursor.fetchall()
    return schedule


def get_groupoid_or_raise_exception(group, redis_obj) :
    groupoid = redis_obj.get(f'group:{group}')
    if groupoid :
        return int(groupoid.decode('utf8'))
    url = requests.get(f'http://mpei.ru/Education/timetable/Pages/default.aspx?group={group}').url
    try :
        groupoid = re.findall(r'groupoid=(\d+)', url)[0]
    except IndexError :
        raise exceptions.MpeiBotException(
            f'Похоже группы, которую ты ввел, не существует  😰')
    redis_obj.set(f'groupoid:{groupoid}', group)
    redis_obj.set(f'group:{group}', groupoid)
    return groupoid
