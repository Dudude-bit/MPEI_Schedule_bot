#!/bin/sh
source /root/mpei_bot/mpei_bot_env/bin/activate
cd /root/mpei_bot/MPEI_Schedule_bot && git pull
python /root/mpei_bot/MPEI_Schedule_bot/delete_schedule.py
python /root/mpei_bot/MPEI_Schedule_bot/main.py
