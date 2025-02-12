import json
import re
from datetime import datetime, timedelta

from config import PLANNER_PATH


TASK_STYLE = "{num}. {text}\n" \
          "{sign} Deadline: {date} (progress: {prog})"

#     The message style:

#     <TOPIC>:
#     1. <text>
#     🔥 needs to be finished before *<date>* (progress right now: <progress>)

#     ==⚠️========⚠️==          # if the task marked important
#     2. <text>
#     *  needs to be finished before <date> (progress right now: <progress>)
#     ================

#     3. <text>
#     *  doesn't have a deadline (progress right now: <progress>)


def get_to_do(person_id):
    with open(f"{PLANNER_PATH}/to_do.json", "r", encoding='utf-8') as file:
        all_planners = json.load(file)

    planner = all_planners.get(str(person_id))
    if not planner:
        return False

    message_list = {}
    for i in range(len(planner)):
        task = planner[i]
        time_left = None

        task_list = message_list.get(task['topic'])
        if task_list is None:
            task_list = message_list[task['topic']] = []

        # Check how much time is left
        if task['date'] != "<no_deadline>":
            time_left = datetime.strptime(task['date']+f".{datetime.now().year}", '%d.%m.%Y') - datetime.now()
            if time_left < timedelta(days=0):
                remove_task(person_id, i+1)         # if the deadline for task has passed, delete task
                continue

        sign, date = ('🔥', f"🚨 {task['date']} 🚨") if time_left and time_left < timedelta(days=2) else ('*', task['date'])
        message = TASK_STYLE.format(num=i + 1, text=task['text'], sign=sign, date=date, prog=task['progress'])

        if task['important']:
            message = f"==⚠️========⚠️==\n" \
                      f"{message}\n" \
                      f"================"
        task_list.append(message)

    # key represents TOPIC and after that all the task follow
    message_list_str = "Your To-Do List:\n\n" +\
                       "\n\n".join(key.upper()+":\n"+'\n'.join(message_list[key]) for key in message_list.keys())

    return message_list_str


def get_to_do_important(person_id):
    with open(f"{PLANNER_PATH}/to_do.json", "r", encoding='utf-8') as file:
        all_planners = json.load(file)

    planner = all_planners.get(str(person_id))
    if not planner:
        return False

    important = []
    close_date = []
    for i in range(len(planner)):
        task = planner[i]
        time_left = None

        if task['date'] != "<no_deadline>":
            time_left = datetime.strptime(task['date']+f".{datetime.now().year}", '%d.%m.%Y') - datetime.now()
            if time_left < timedelta(days=0):
                remove_task(person_id, i+1)         # if the deadline for task has passed, delete task
                continue
        # print(time_left)

        # the representation differs if the task is close to deadline
        sign, date = ('🔥', f"🚨 {task['date']} 🚨") if time_left and time_left < timedelta(days=2) else ('*', task['date'])

        if task['important']:
            important.append(TASK_STYLE.format(num=i + 1, text=task['text'], sign=sign, date=date, prog=task['progress']))
            continue
        if sign != '*':             # it means the deadline is closed
            close_date.append(TASK_STYLE.format(num=i + 1, text=task['text'], sign='🔥', date=date, prog=task['progress']))

    important_str = '\n\n'.join(important)
    close_date_str = '\n\n'.join(close_date)
    return f"""
=====================
⚠️ IMPORTANT TASK ⚠️
{important_str}
=====================
    
{close_date_str}"""


def add_new_task(person_id, text, topic=None, date=None, progress=None, imp=False):
    with open(f"{PLANNER_PATH}/to_do.json", "r", encoding='utf-8') as file:
        all_planners = json.load(file)

    planner = all_planners.get(str(person_id))
    if planner is None:
        planner = all_planners[str(person_id)] = []
    # print(planner)

    task = {
        'text': text,
        'topic': topic.upper() if topic else 'GENERAL',
        'date': re.sub(r'[:.,]+', '.', date) if date else '<no_deadline>',
        'progress': progress if progress else '&#128997;',
        'important': imp
    }
    planner.append(task)

    # print(all_planners)
    with open(f"{PLANNER_PATH}/to_do.json", "w", encoding='utf-8') as file:
        json.dump(all_planners, file, indent=4, ensure_ascii=False)


def remove_task(person_id, task_id):
    with open(f"{PLANNER_PATH}/to_do.json", "r", encoding='utf-8') as file:
        all_planners = json.load(file)

    planner = all_planners.get(str(person_id))
    # print(planner)
    if not planner or len(planner) < task_id or task_id < 0:
        return False

    del planner[task_id-1]

    with open(f"{PLANNER_PATH}/to_do.json", "w", encoding='utf-8') as file:
        json.dump(all_planners, file, indent=4, ensure_ascii=False)

    return True


def upgrade_task_progress(person_id, task_id):
    progress_converter = {
        '&#128997;': '&#128999;',   # red -> orange
        '&#128999;': '&#129000;',   # orange -> yellow
        '&#129000;': '&#129001;',   # yellow -> green
        '&#129001;': '&#128997;'    # green -> red
    }

    with open(f"{PLANNER_PATH}/to_do.json", "r", encoding='utf-8') as file:
        all_planners = json.load(file)

    planner = all_planners.get(str(person_id))
    # print(planner)
    if not planner or len(planner) < task_id or task_id < 0:
        return False

    planner[task_id-1]['progress'] = progress_converter[planner[task_id-1]['progress']]     # proceed to the next stage

    with open(f"{PLANNER_PATH}/to_do.json", "w", encoding='utf-8') as file:
        json.dump(all_planners, file, indent=4, ensure_ascii=False)

    return True


if __name__ == '__main__':
    # add_new_task(587938956, 'do another math', topic='math')
    # add_new_task(587938956, 'kill myself', date='15.02', imp=True)
    # add_new_task(587938956, 'buy phone', date='12.02')
    # print(remove_task(587938956, 3))
    # print(get_to_do_important(587938956))
    # print(upgrade_task_progress(587938956, 10))
    # print(upgrade_task_progress(587938956, 4))
    # print(get_to_do_important(587938956))

    # print(get_to_do(587938956))

    print("DONE")
