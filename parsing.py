import re
import redis
import requests
import datetime
import exceptions
import services


def parsing_schedule(connection, groupoid, redis_obj: redis.Redis):
    num_dayweek_to_string = {
        1: 'Понедельник',
        2: 'Вторник',
        3: 'Среда',
        4: 'Четверг',
        5: 'Пятница',
        6: 'Суббота',
        7: 'Воскресенье'
    }
    redis_obj.sadd('has_schedule', groupoid)
    url = f'http://ts.mpei.ru/api/schedule/group/{groupoid}'
    today = datetime.datetime.now()
    monday_of_this_week = today + datetime.timedelta(days=-today.weekday())
    monday_of_next_week = monday_of_this_week + datetime.timedelta(weeks=1)
    saturday_of_this_week = monday_of_this_week + datetime.timedelta(days=6)
    saturday_of_next_week = monday_of_next_week + datetime.timedelta(days=6)
    start_string_this_week = f'{monday_of_this_week.year}.{monday_of_this_week.month // 10}{monday_of_this_week.month % 10}.{monday_of_this_week.day // 10}{monday_of_this_week.day % 10}'
    start_string_next_week = f'{monday_of_next_week.year}.{monday_of_next_week.month // 10}{monday_of_next_week.month % 10}.{monday_of_next_week.day // 10}{monday_of_next_week.day % 10}'
    finish_string_this_week = f'{saturday_of_this_week.year}.{saturday_of_this_week.month // 10}{saturday_of_this_week.month % 10}.{saturday_of_this_week.day // 10}{saturday_of_this_week.day % 10}'
    finish_string_next_week = f'{saturday_of_next_week.year}.{saturday_of_next_week.month // 10}{saturday_of_next_week.month % 10}.{saturday_of_next_week.day // 10}{saturday_of_next_week.day % 10}'
    json_obj_this_week = requests.get(url, params={
        'start': start_string_this_week,
        'finish': finish_string_this_week
    }).json()
    json_obj_next_week = requests.get(url, params={
        'start': start_string_next_week,
        'finish': finish_string_next_week
    }).json()
    with connection as conn:
        with conn.cursor() as cursor:
            for item in json_obj_this_week:
                WeekDay = num_dayweek_to_string[item['dayOfWeek']]
                num_object = item['lessonNumberStart']
                auditory = item['auditorium']
                teacher = item['lecturer']
                obj = item['discipline']
                object_type = item['kindOfWork']
                slug = services.generate_slug(redis_obj)
                week = int(redis_obj.get('current_week').decode('utf8'))
                query = f"""
                INSERT INTO schedule(WeekDay, num_object, groupoid, auditory, teacher, object, object_type, slug, week) VALUES {WeekDay, num_object, groupoid, auditory, teacher, obj, object_type, slug, week}
                """
                cursor.execute(query)
            for item in json_obj_next_week:
                WeekDay = num_dayweek_to_string[item['dayOfWeek']]
                num_object = item['lessonNumberStart']
                auditory = item['auditorium']
                teacher = item['lecturer']
                obj = item['discipline']
                object_type = item['kindOfWork']
                slug = services.generate_slug(redis_obj)
                week = int(redis_obj.get('current_week').decode('utf8')) + 1
                query = f"""
                INSERT INTO schedule(WeekDay, num_object, groupoid, auditory, teacher, object, object_type, slug, week) VALUES {WeekDay, num_object, groupoid, auditory, teacher, obj, object_type, slug, week}
                """
                cursor.execute(query)


def get_groupoid_or_raise_exception(group, redis_obj):
    groupoid = redis_obj.get(f'group:{group}')
    if groupoid:
        return int(groupoid.decode('utf8'))
    url = requests.get(f'http://mpei.ru/Education/timetable/Pages/default.aspx?group={group}').url
    try:
        groupoid = re.findall(r'groupoid=(\d+)', url)[0]
    except IndexError:
        raise exceptions.MpeiBotException(
            f'Похоже группы, которую Вы ввели, не существует  😰')
    redis_obj.set(f'groupoid:{groupoid}', group)
    redis_obj.set(f'group:{group}', groupoid)
    return groupoid
