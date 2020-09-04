import re

import redis
import requests
from bs4 import BeautifulSoup

import exceptions
import services


def parsing_schedule(connection, groupoid, weekday, redis_obj: redis.Redis) :
    cursor = connection.cursor()
    week_dict = {
        'Пн': 'Понедельник',
        'Вт': 'Вторник',
        'Ср': 'Среда',
        'Чт': 'Четверг',
        'Пт': 'Пятница',
        'Сб': 'Суббота'
    }
    time_subj_num = {
        '09:20 - 10:55': 1,
        '11:10 - 12:45': 2,
        '13:45 - 15:20': 3,
        '15:35 - 17:10': 4,
        '17:20 - 18:50': 5,
        '18:55 - 20:25': 6
    }
    current_week = int(redis_obj.get('current_week').decode('utf8'))
    url = 'https://mpei.ru/Education/timetable/Pages/table.aspx'
    html = requests.get(url, params={
        'groupoid': groupoid
    }).text
    r = BeautifulSoup(html, 'lxml')
    regexp = re.compile(r'(^\D{2}), \d{1,2}')
    all_weekdays = r.find('table').find_all('tr', text=regexp)
    ls_for_schedule = {}
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
                subject_dict['slug'] = services.generate_slug(redis_obj)
                ls_for_schedule[week_dict[regexp.findall(i.text)[0]]].append(subject_dict)
                tr = tr.find_next_sibling()
                if regexp.match(tr.text):
                    break
            except AttributeError :
                break
    redis_obj.sadd('has_schedule', groupoid)
    for item in ls_for_schedule :
        for subject in ls_for_schedule[item] :
            print(subject)
            query = f"""
            INSERT INTO schedule(WeekDay, num_object, groupoid, auditory, teacher, object, object_type, slug, week) 
            VALUES 
            {item, subject['num'], groupoid, subject['room'], subject['teacher'], subject['name'], subject['type'], subject['slug'], current_week};
            """
            cursor.execute(query)
    try :
        schedule = ls_for_schedule[weekday]
    except KeyError as e:
        raise exceptions.MpeiBotException('Хмм... Походу Вы отдыхаете в этот день 😎')
    ################  NEXT WEEK  ################
    link_for_next_week = r.find('span', 'mpei-galaktika-lessons-grid-nav').find_all('a')[1].href
    html = requests.get(link_for_next_week, params={
        'groupoid' : groupoid
    }).text
    r = BeautifulSoup(html, 'lxml')
    regexp = re.compile(r'(^\D{2}), \d{1,2}')
    all_weekdays = r.find('table').find_all('tr', text=regexp)
    ls_for_schedule = {}
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
                subject_dict['slug'] = services.generate_slug(redis_obj)
                ls_for_schedule[week_dict[regexp.findall(i.text)[0]]].append(subject_dict)
                tr = tr.find_next_sibling()
                if regexp.match(tr.text) :
                    break
            except AttributeError :
                break
    redis_obj.sadd('has_schedule', groupoid)
    for item in ls_for_schedule :
        for subject in ls_for_schedule[item] :
            print(subject)
            query = f"""
                INSERT INTO schedule(WeekDay, num_object, groupoid, auditory, teacher, object, object_type, slug, week) 
                VALUES 
                {item, subject['num'], groupoid, subject['room'], subject['teacher'], subject['name'], subject['type'], subject['slug'], current_week + 1};
                """
            cursor.execute(query)
    return services.normalize_schedule(schedule)


def get_groupoid_or_raise_exception(group, redis_obj) :
    groupoid = redis_obj.get(f'group:{group}')
    if groupoid :
        return int(groupoid.decode('utf8'))
    url = requests.get(f'http://mpei.ru/Education/timetable/Pages/default.aspx?group={group}').url
    try :
        groupoid = re.findall(r'groupoid=(\d+)', url)[0]
    except IndexError :
        raise exceptions.MpeiBotException(
            f'Похоже группы, которую Вы ввели, не существует  😰')
    redis_obj.set(f'groupoid:{groupoid}', group)
    redis_obj.set(f'group:{group}', groupoid)
    return groupoid
