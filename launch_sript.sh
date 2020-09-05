source /mpei_bot/mpei_bot_env/bin/activate;
echo 'VENV ACTIVATED';
python /mpei_bot/main_dir/MPEI_Schedule_bot/pass_errors.py;
echo 'PASSED ERRORS'
python /mpei_bot/main_dir/MPEI_Schedule_bot/delete_schedule.py;
echo 'SCHEDULE DELETED'
python /mpei_bot/main_dir/MPEI_Schedule_bot/main.py;
