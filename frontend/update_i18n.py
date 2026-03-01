import json
import os
import glob

locales_dir = 'src/locales'
for path in glob.glob(f'{locales_dir}/*/translation.json'):
    print(f'Loading {path}...')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    lang = path.split(os.extsep)[0].split(os.sep)[-2]  # fixes the split
    if 'src\\locales\\' in path or 'src/locales/' in path:
        lang = path.replace('\\', '/').split('/')[-2]
    
    # Defaults
    t_hr = 'リマインド（稽古のN時間前）'
    t_hr_help = '稽古時間の何時間前に出欠の自動リマインダーを送信するかを指定します。'
    t_dl = 'リマインド（回答締切のN時間前）'
    t_dl_help = '出欠の回答締切の何時間前に自動リマインダーを送信するかを指定します。'
    
    if lang == 'en':
        t_hr = 'Reminder (Hours before rehearsal)'
        t_hr_help = 'Specify how many hours before the rehearsal to send the automatic attendance reminder.'
        t_dl = 'Reminder (Hours before deadline)'
        t_dl_help = 'Specify how many hours before the RSVP deadline to send an automatic reminder.'
    elif lang == 'ko':
        t_hr = '리마인드 (연습 N시간 전)'
        t_hr_help = '연습 시작 몇 시간 전에 자동 출석 리마인더를 보낼지 지정합니다.'
        t_dl = '리마인드 (마감 N시간 전)'
        t_dl_help = '응답 마감 몇 시간 전에 자동 리마인더를 보낼지 지정합니다.'
    elif lang == 'zhHans':
        t_hr = '提醒（排练前N小时）'
        t_hr_help = '指定在排练开始前几小时发送自动出勤提醒。'
        t_dl = '提醒（截止前N小时）'
        t_dl_help = '指定在回复截止期限前几小时发送自动提醒。'
    elif lang == 'zhHant':
        t_hr = '提醒（排練前N小時）'
        t_hr_help = '指定在排練開始前幾小時發送自動出勤提醒。'
        t_dl = '提醒（截止前N小時）'
        t_dl_help = '指定在回覆截止期限前幾小時發送自動提醒。'

    if 'project' not in data: data['project'] = {}
    if 'settings' not in data['project']: data['project']['settings'] = {}
    if 'form' not in data['project']['settings']: data['project']['settings']['form'] = {}
    
    data['project']['settings']['form']['attendanceReminderHours'] = t_hr
    data['project']['settings']['form']['attendanceReminderHoursHelper'] = t_hr_help
    data['project']['settings']['form']['attendanceDeadlineReminderHours'] = t_dl
    data['project']['settings']['form']['attendanceDeadlineReminderHoursHelper'] = t_dl_help
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Updated {lang}")
