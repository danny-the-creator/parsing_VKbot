import vk_api as vk
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import re
import threading
from functools import partial
from itertools import chain

from small_features.wiki_info import wiki_search
from small_features.destiny import dice_roll, flip_coin, num_gen, destiny_decoder
from data_storage.smart_download import down_smart
from parsing.LM_travel_deals import LM_Parser
from data_storage.to_do_list import get_to_do, get_to_do_important, upgrade_task_progress, add_new_task, remove_task

from config import TOKEN, ID_BOT, HEADERS, all_users, id_name, chat_name


# GLOBALS (bad)
PART_OF_TRANSMISSION = []
LAST_COMMANDS = {}

HELP_MESSAGE = """
    Greetings Commander! 
    I am your personal assistant and I am ready to follow your orders!
    At least orders from the list below...
    Please type:
    - help : To get this list again 
    - info : Get your day-to-day information
    - forward <ID_1 ID_2 ID_3> : after that all the messages will be send to the indicated receiver's IDs
    - stop_ : Stops the current process and returns to the main functionality
    - finish_reminder <number> : mark the reminder as done and stops reminding about it
    - wiki <your statement> : To get info about your statement from wiki
    - LM_travel : gives you several decent links about LM_travel

    - task : to show all of your tasks 
    - add_task <message>: the message will appear in your to-do list
    - del_task <id>: removes the task under the corresponding number
    - upd_task <id>: increases the progress of the selected task

    - dice : roles a dice for you
    - coin : flips a coin for you
    - magic_advice : tells you the destiny
    - rand <number> : returns you random number in range

    - any file/photo/video/audio will be downloaded and sorted
    """


def send_response(sender, message, key_v=0):
    keyboard = keyboard_ext() if key_v else keyboard_main()
    vk_session.method(
        "messages.send", {"chat_id": sender, "message": message, "random_id": get_random_id(), "keyboard": keyboard})

def send_sticker(sender, id):
    vk_session.method("messages.send", {"chat_id": sender, "sticker_id": id, "random_id": get_random_id()})

def delete_message(sender, message_id):     # !! Works a bit strange, probably will be easier to delete it
    vk_control.messages.delete(group_id=ID_BOT, peer_id=2000000000+sender, cmids=message_id, delete_for_all=1)


def keyboard_main():
    """Setting up the Keyboard for most of the functions"""
    keyboard = VkKeyboard()
    keyboard.add_button('HELP', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('LAST', color=VkKeyboardColor.POSITIVE)
    return keyboard.get_keyboard()

def keyboard_ext():
    """Setting up the Keyboard during the retransmission"""
    keyboard = VkKeyboard()
    keyboard.add_button('HELP', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('STOP', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def forward(*args):
    receivers = []
    for receiver in args:
        receiver = receiver.replace(',', '').lower().strip()

        if receiver.replace('-', '') in all_users.keys():
            hidden = True if receiver[-1] == '-' else False
            receivers.append((receiver.replace('-', ''), hidden))

    if not receivers:
        send_response(sender, f"You should select (existing) receivers\nI won't forward your message to <NOONE>!")
    else:
        send_response(sender, f"All the following messages will be transmitted to: "
                              f"{', '.join([r[0] for r in receivers])}\nto stop it type: stop_ ", key_v=1)

        thread = threading.Thread(target=transmission, args=(receivers,))
        thread.start()


def transmission(receivers):
    global PART_OF_TRANSMISSION         # !! very bad

    def inner_handle_stop_command(name):
        if name == 'me':
            send_response(all_users[name]['chat'], "End of transmission, ready to serve your orders, Commander!")
            return True
        send_response(all_users[name]['chat'], f"Do you think you really can stop me, {name}?")
        send_sticker(all_users[name]['chat'], 69384)

    PART_OF_TRANSMISSION = [all_users[r[0]]['chat'] for r in receivers] + [all_users['me']['chat']]

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and event.chat_id in PART_OF_TRANSMISSION:
            user_name = id_name[event.message['from_id']]
            message = event.message['text'].replace("[club229115083|@you_pressed]", '')

            if message != event.message['text']:         # button was clicked
                delete_message(event.chat_id, event.message["conversation_message_id"])     # not always works
                if message.strip().lower() == 'help':
                    send_response(event.chat_id, HELP_MESSAGE, key_v=1)
                    continue
                message += '_'      # in order to get stop_


            if message.strip().lower() == 'stop_':
                if inner_handle_stop_command(user_name):
                    PART_OF_TRANSMISSION = []
                    break
                continue

            if user_name == 'me':
                for receiver in receivers:
                    message = message if receiver[1] else f'message from my overlord:\n\"{message}\"'
                    send_response(all_users[receiver[0]]['chat'], message, key_v=1)
            elif user_name in [r[0] for r in receivers]:
                send_response(all_users['me']['chat'], f"{user_name} sends: \"{message}\"", key_v=1)


def execute(func, user, *rest):
    global LAST_COMMANDS
    print(user)
    if func.__name__ in all_users[id_name[user]]['access_rights'] or func.__name__ == 'unknown_command':
        func(*rest)
        if func.__name__ not in ["last", "unknown_command"]:
            LAST_COMMANDS[sender] = partial(func, *rest)
    else:
        send_response(sender, "Sorry, I cannot do that for you")
        send_sticker(sender, 69385)

def last():
    LAST_COMMANDS.get(
        sender, lambda: send_response(sender, "I am sorry, but I don't remember your last command... &#128533;"))()



def start():
    send_response(sender, "I AM ALIVE!!!")

def stop():
    send_response(sender, "What do you want me to stop? Your heart?")
    send_sticker(sender, 69391)

def help():
    send_response(sender, HELP_MESSAGE)

def wiki(query='nothing', *args):
    lang_codes = ['aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'ar', 'as', 'av', 'ay', 'az', 'ba', 'be', 'bg', 'bh', 'bi',
                  'bm', 'bn', 'bo', 'br', 'bs', 'ca', 'ce', 'ch', 'co', 'cr', 'cs', 'cu', 'cv', 'cy', 'da', 'de', 'dv',
                  'dz', 'ee', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'ff', 'fi', 'fj', 'fo', 'fr', 'fy', 'ga', 'gd',
                  'gl', 'gn', 'gu', 'gv', 'ha', 'he', 'hi', 'ho', 'hr', 'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie', 'ig',
                  'ii', 'ik', 'io', 'is', 'it', 'iu', 'ja', 'jv', 'ka', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn', 'ko',
                  'kr', 'ks', 'ku', 'kv', 'kw', 'ky', 'la', 'lb', 'lg', 'li', 'ln', 'lo', 'lt', 'lu', 'lv', 'mg', 'mh',
                  'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 'my', 'na', 'nb', 'nd', 'ne', 'ng', 'nl', 'nn', 'no', 'nr',
                  'nv', 'ny', 'oc', 'oj', 'om', 'or', 'os', 'pa', 'pi', 'pl', 'ps', 'pt', 'qu', 'rm', 'rn', 'ro', 'ru',
                  'rw', 'sa', 'sc', 'sd', 'se', 'sg', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st', 'su',
                  'sv', 'sw', 'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw', 'ty', 'ug',
                  'uk', 'ur', 'uz', 've', 'vi', 'vo', 'wa', 'wo', 'xh', 'yi', 'yo', 'za', 'zh', 'zu']
    if query in lang_codes:
        lang = query
        query = ' '.join(args) if len(args) > 0 else 'nothing'
    else:
        lang = 'en'
        query = query + ' ' + ' '.join(args)
    resp, exp = wiki_search(query, lang)
    send_response(sender, resp)
    if exp:
        send_sticker(sender, 69407)

def lm_travel(num):
    if parser.update_needed(hours=4):
        parser.parse()
        parser.fill_hottest()
    parser.fill_tours(int(num))
    for message in parser.prepare_message(int(num)):
        send_response(sender, message)


def task():
    user = all_users[chat_name[sender]]['id']
    message = get_to_do(user)
    if not message:
        send_response(sender, "You don't have anything in your To-Do list, lucky you...")
        return
    send_response(sender, message)

def add_task(*args):
    commands = ''       # if the command is '', extract commands return None value
    user = all_users[chat_name[sender]]['id']

    def inner_extract_command(pattern, commands):
        match = re.search(pattern, commands)
        return (match.group(0), commands[:match.start()] + commands[match.end():]) if match else (None, commands)

    text = " ".join(args).split('#', 1)     # check if we have any commands
    commands = text[0] if len(text) > 1 else commands
    text = text[-1]

    # signs in the command message which represent parameters of the function
    imp, commands = inner_extract_command("-i ", commands)
    date, commands = inner_extract_command(r"\d\d[;:.,|]\d\d", commands)
    progress, commands = inner_extract_command(r"[🟩🟨🟧🟥]", commands)

    # the last option which is left should be the topic, if it doesn't exist than it will be set to None (default)
    rest_commands = [i for i in commands.split() if len(i)>0]
    topic = rest_commands[0].lower() if rest_commands != [] else None

    if len(rest_commands) > 1:
        # If more than two words are left, then something went wrong and command is invalid
        send_response(sender, "Oops, something went wrong...\n"
                            "please, make sure your topic is one word and all other parameters are correct")
        send_sticker(sender, 69398)
        return

    add_new_task(user, text, topic=topic, date=date, progress=progress, imp=imp)
    send_response(sender, "Task added... Optimizing your path to success ⚙")

def del_task(task_id):
    user = all_users[chat_name[sender]]['id']
    if not remove_task(user, int(task_id)):
        send_response(sender, "You cannot delete the task which doesn't exist! ")
        return
    send_response(sender, "Congrats! your task is finished!")
    send_sticker(sender, 69418)

def upd_task(task_id):
    user = all_users[chat_name[sender]]['id']
    if not upgrade_task_progress(user, int(task_id)):
        send_response(sender, "I don't know which task are you talking about?")
        send_sticker(sender, 69414)
        return
    send_response(sender, "Well done! you are one step closer to finish it! 😎")


def dice():
    send_response(sender,f"You got: {dice_roll()}")

def coin():
    send_response(sender, flip_coin())

def magic_advice():
    send_response(sender, destiny_decoder())

def rand(num="10"):
    send_response(sender, f"You got: {num_gen(int(num))}")


def unknown_command():
    send_response(sender, "what is my purpose?")


def download(attachment, imp=None):
    def inner_handle_photo():
        print('photo')
        url = attachment['photo']['orig_photo']['url']
        down_smart(url, ext='jpg', imp=imp)

    def inner_handle_video():
        print('video')
        send_response(sender, "My Lord, the quality of this video is unworthy of you.\n"
                              "I beg you, send it as a file to protect its brilliance. ✨")

    def inner_handle_audio_message():
        if attachment['audio_message'].get('transcript_state') in ('in_progress', None):
            return  # Skip if still in progress
        print('audio_message')

        url = attachment['audio_message']['link_ogg']
        down_smart(url, ext='mp3', imp=imp)
        send_response(sender, "Your voice message is saved!")

    def inner_handle_doc():
        print('doc')
        url = attachment['doc']['url']
        ext = attachment['doc']['ext'].replace('tui', 'mp3')
        down_smart(url, ext=ext, imp=imp)
        send_response(sender, f"I got your <{ext}> file 😊")

    def inner_handle_unknown():
        print('UNKNOWN')
        send_response(sender, "I don't support that kind of input...")
        send_sticker(sender, 69407)

    handlers = {
        'photo': inner_handle_photo,
        'video': inner_handle_video,
        'audio_message': inner_handle_audio_message,
        'doc': inner_handle_doc,
    }
    print(sender)
    handlers.get(attachment.get('type'), inner_handle_unknown)()


def stopper():
    send_response(sender, f"Did you mean <{command}> ? \nThen I cannot help you :<")
    # the way to send a sticker, if you want to send emoji use this in your message: &#000000; (id)
    send_sticker(sender, 69407)


COMMANDS = {
    'start': start,
    'help': help,
    'info': stopper,
    'forward': forward,
    'stop_': stop,
    'finish_reminder': stopper,
    'wiki': wiki,
    'lm_travel': lm_travel,

    'task': task,
    'add_task': add_task,
    'del_task': del_task,
    'upd_task': upd_task,

    'dice': dice,
    'coin': coin,
    'magic_advice': magic_advice,
    'rand': rand,

    'last': last
}


if __name__ == '__main__':

    parser = LM_Parser(500, -1, num_review=-1, dep_in=1)
    parser.set_settings(directory='./data_storage/data', headers=HEADERS)
    parser.set_hottest(max_price=500, min_review=8, num_review=350, dep_in=0)

    print("Start the session")
    vk_session = vk.VkApi(token=TOKEN)
    longpoll = VkBotLongPoll(vk_session, ID_BOT)
    vk_control = vk_session.get_api()
    print("Bot is running...")

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
            attachments = event.message["attachments"] + list(chain(*[m.get("attachments", []) for m in event.message['fwd_messages']]))
            sender = event.chat_id
            sender_id = event.message['from_id']
            if not attachments:
                print("New Message")
                if sender in PART_OF_TRANSMISSION:
                    continue

                received_message = event.message["text"].replace("[club229115083|@you_pressed]", '')
                if received_message != event.message["text"]:  # not always works !
                    delete_message(sender, event.message["conversation_message_id"])  # !!

                received_message = received_message.split()
                command = received_message[0].lower().strip()
                rest = received_message[1:]

                execute(COMMANDS.get(command, unknown_command), sender_id, *rest)
            elif all_users['me']['id'] == sender_id:
                # Check if the person is not me
                important = event.message["text"][2:] if event.message["text"][:2] == '-i' else None
                for att in attachments:
                    download(att, imp=important)

        else:
            print('UNKNOWN EVENT')
