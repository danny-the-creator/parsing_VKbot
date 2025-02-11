import json
from config import PLANNER_PATH

VK_TASK = "{num}. {text}\n" \
          "{sign} needs to be finished before {date} (progress: {prog})\n"

def get_to_do(person_id):
    with open(f"{PLANNER_PATH}/to_do.json", "r") as file:
        all_planners = json.load(file)
    planner = all_planners.get(person_id)
    if not planner:
        return False

    message_list = {}
    # for task in planner:



#     <TOPIC>:
#     1. <text>
#     🔥 needs to be finished before *<date>* (progress right now: <progress>)

#     ==⚠️========⚠️==          # if the task marked important
#     2. <text>
#     *  needs to be finished before <date> (progress right now: <progress>)
#     ================

#     3. <text>
#     *  doesn't have a deadline (progress right now: <progress>)

def get_to_do_important(person_id):
    with open(f"{PLANNER_PATH}/to_do.json", "r") as file:
        all_planners = json.load(file)
    planner = all_planners.get(person_id)
    if not planner:
        return False

    important = []
    close_date = []
    # for task in planner:
    #     sign = '*'
    #     if task['important']:
    #         important.append(VK_TASK.format(num=1, text=task['text'], sign=sign, date=task['date'], prog=task['progress']))


def add_task(person_id, text, topic=None, date=None, progress=None, imp=False):
    with open(f"{PLANNER_PATH}/to_do.json", "r", encoding='utf-8') as file:
        all_planners = json.load(file)

    planner = all_planners.get(str(person_id))
    if planner is None:
        planner = all_planners[str(person_id)] = []
    # print(planner)
    task = {
        'text': text,
        'topic': topic.upper() if topic else 'GENERAL',
        'date': date if date else '<no_deadline>',
        'progress': progress if progress else '🟥',
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





if __name__ == '__main__':
    # add_task(587938956, 'do another math', topic='math', imp=True)
    # print(remove_task(587938956, 3))
    print("DONE")