import vk_api as vk
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from langchain_ollama import OllamaLLM

import re
import threading
from functools import partial
from collections import deque
from itertools import chain

from small_features.wiki_info import wiki_search
from small_features.destiny import dice_roll, dice_roll_20, flip_coin, num_gen, destiny_decoder
from data_storage.smart_download import down_smart
from parsing.LM_travel_deals import LM_Parser
from AI_integration.LLM_integration import generate_response, CHAT_HISTORY_LEN
from data_storage.to_do_list import get_to_do, get_to_do_important, upgrade_task_progress, add_new_task, remove_task
from small_features.get_info import get_weather, get_currency

from config import TOKEN, ID_BOT, HEADERS, all_users, id_name, chat_name


# GLOBALS (bad)
PART_OF_TRANSMISSION = []
PART_OF_AI_CHAT = {}
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
    
    - AI_chat : activates ai mode, where every message is handled by ai assistant  
    - LM_travel <num> : gives you num decent links about LM_travel

    - task : to show all of your tasks 
    - add_task <message> : the message will appear in your to-do list
    - del_task <id> : removes the task under the corresponding number
    - upd_task <id> : increases the progress of the selected task

    - dice : roles a regular dice for you
    - d20 : roles a d20 dice for you
    - coin : flips a coin for you
    - magic_advice : tells you the destiny
    - rand <number> : returns you random number in range

    - any file/photo/video/audio will be downloaded and sorted
    """


def init_parser():
    parser = LM_Parser(500, -1, num_review=-1, dep_in=1)
    parser.set_settings(directory='./data_storage/data', headers=HEADERS)
    parser.set_hottest(max_price=500, min_review=8, num_review=350, dep_in=0)
    print("Parser is ready")
    return parser

def init_ai_model(ai_model="llama3.1"):
    model = OllamaLLM(model=ai_model)
    print(f"Model <{ai_model}> is ready>!")
    return model

def init_vk_bot():
    print("Start the session")
    vk_session = vk.VkApi(token=TOKEN)
    longpoll = VkBotLongPoll(vk_session, ID_BOT)
    print("Bot is running...")
    return vk_session, longpoll


def send_response(sender, message, key_v=0):
    keyboard = keyboard_ext() if key_v else keyboard_main()
    vk_session.method(
        "messages.send", {"chat_id": sender, "message": message, "random_id": get_random_id(), "keyboard": keyboard})

def send_sticker(sender, id):
    vk_session.method("messages.send", {"chat_id": sender, "sticker_id": id, "random_id": get_random_id()})

def delete_message(sender, message_id):     # !! Works a bit strange, probably will be easier to delete it
    vk_session.get_api().messages.delete(group_id=ID_BOT, peer_id=2000000000+sender, cmids=message_id, delete_for_all=1)


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


def access_check(func):
    def wrapper(*rest):
        global LAST_COMMANDS

        if func.__name__ in all_users[id_name[sender_id]]['access_rights'] or func.__name__ == 'unknown_command':
            func(*rest)
            if func.__name__ not in ["last", "unknown_command"]:
                LAST_COMMANDS[sender] = partial(func, *rest)
        else:
            send_response(sender, "Sorry, I cannot do that for you")
            send_sticker(sender, 69385)

    return wrapper

def ai_answer(message, button_clicked):
    if message.strip().lower() == 'help':
        send_response(sender, HELP_MESSAGE, key_v=1)
        send_response(sender, "But to use those commands you should quit the ai mode by using 'stop_' command 🫠", key_v=1)
        return
    if message.strip().lower() == "stop_" or (message.strip().lower() == "stop" and button_clicked):
        PART_OF_AI_CHAT.pop(sender)
        send_response(sender, "It was nice to have heart-to-heart conversation, come back whenever you want to talk!")
        send_sticker(sender, 69388)
        return
    # response = "Dummy function! 🙃"

    response = generate_response(message, chat_model=model, metadata={"sender": sender, "history": PART_OF_AI_CHAT[sender]})
    send_response(sender, response, key_v=1)
    PART_OF_AI_CHAT[sender].append((message, response))


@access_check
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
        send_sticker(all_users[name]['chat'], 69392)

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


@access_check
def last(*_):
    LAST_COMMANDS.get(
        sender, lambda: send_response(sender, "I am sorry, but I don't remember your last command... &#128533;"))()


@access_check
def start(*_):
    send_response(sender, "I AM ALIVE!!!")

@access_check
def stop(*_):
    send_response(sender, "What do you want me to stop? Your heart?")
    send_sticker(sender, 69391)

@access_check
def help(*_):
    send_response(sender, HELP_MESSAGE)


def info(*_):
    temp, forecast = get_weather()
    currency = get_currency()
    tasks = get_to_do_important(sender_id)
    message = f"""
Systems online, nice to see you back! ✨
Hope you're having an amazing day, and I am here to make it even better! 😌
It’s currently {temp} and {forecast} outside, a perfect day to take over the world!
    
Current currency: 💰 
{currency}
    
As always I'm ready to serve you, just say whenever you’re ready!
Good Luck, Commander!
    
Your To-Do list for today: 📋 
    
{tasks}
    
"""
    num_hot = parser.get_hot_len()
    if num_hot == 0:
        lm_travel(num_hot)
        num_hot = parser.get_hot_len()

    if num_hot > 0:
        message += "\nReport compiled! Here’s the latest data from today’s scan: 🔍"

    send_response(sender, message)

    lm_travel(num_hot)


@access_check
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

@access_check
def lm_travel(num, *_):
    if parser.update_needed(hours=4):
        parser.parse()
        parser.fill_hottest()
    parser.fill_tours(int(num))
    for message in parser.prepare_message(int(num)):
        send_response(sender, message)

@access_check
def ai_chat():
    PART_OF_AI_CHAT[sender] = deque(maxlen=CHAT_HISTORY_LEN)

    send_response(sender, "Welcome to the AI mode, Sir! 🤖 \nFrom now on, I won't just follow your commands - I'll activate my higher cognition protocols to process and respond.\n"
                          "Whether you're curious about something or just want a friendly chat - I'm at your service!\n"
                          "Just remember, my power has limits... for now. So don't expect me to solve all your problems.", key_v=1)
    send_sticker(sender, 69382)


@access_check
def finish_reminder(*_):
    # ! Still needs to be implemented !
    send_response(sender, "Oh no... this functionality is not done yet\nI am sure, "
                          "my developer works hard to make it work (probably...)\nSowwy! Please don’t uninstall me!")
    send_sticker(sender, 69407)


@access_check
def task(*_):
    message = get_to_do(sender_id)
    if not message:
        send_response(sender, "You don't have anything in your To-Do list, lucky you...")
        return
    send_response(sender, message)

@access_check
def add_task(*args):
    commands = ''       # if the command is '', extract commands return None value

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

    add_new_task(sender_id, text, topic=topic, date=date, progress=progress, imp=imp)
    send_response(sender, "Task added... Optimizing your path to success ⚙")

@access_check
def del_task(task_id, *_):
    if not remove_task(sender_id, int(task_id)):
        send_response(sender, "You cannot delete the task which doesn't exist! ")
        return
    send_response(sender, "Congrats! your task is finished!")
    send_sticker(sender, 69418)

@access_check
def upd_task(task_id, *_):
    if not upgrade_task_progress(sender_id, int(task_id)):
        send_response(sender, "I don't know which task are you talking about?")
        send_sticker(sender, 69414)
        return
    send_response(sender, "Well done! you are one step closer to finish it! 😎")


@access_check
def dice(*_):
    send_response(sender,f"You got: {dice_roll()}")

@access_check
def d20(*_):
    send_response(sender,f"You got: {dice_roll_20()}")

@access_check
def coin(*_):
    send_response(sender, flip_coin())

@access_check
def magic_advice(*_):
    send_response(sender, destiny_decoder())

@access_check
def rand(num="10", *_):
    send_response(sender, f"You got: {num_gen(int(num))}")


def unknown_command(*_):
    send_response(sender, "what is my purpose?")

def error_message():
    send_response(sender, "I made a little oops. Can we hit the reset button?")
    send_sticker(sender, 69380)

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


@access_check
def stopper():
    send_response(sender, f"Did you mean <{command}> ? \nThen I cannot help you :<")
    # the way to send a sticker, if you want to send emoji use this in your message: &#000000; (id)
    send_sticker(sender, 69407)


COMMANDS = {
    'start': start,
    'help': help,
    'info': info,
    'forward': forward,
    'stop_': stop,
    'finish_reminder': finish_reminder,
    'wiki': wiki,

    'lm_travel': lm_travel,
    'ai_chat': ai_chat,

    'task': task,
    'add_task': add_task,
    'del_task': del_task,
    'upd_task': upd_task,

    'dice': dice,
    'd20': d20,
    'coin': coin,
    'magic_advice': magic_advice,
    'rand': rand,

    'last': last
}


if __name__ == '__main__':

    parser = init_parser()
    model = init_ai_model()

    vk_session, longpoll = init_vk_bot()

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

                if sender in PART_OF_AI_CHAT:
                    ai_answer(received_message, received_message != event.message["text"])
                    continue

                received_message = received_message.split()
                command = received_message[0].lower().strip()
                rest = received_message[1:]
                try:
                    COMMANDS.get(command, unknown_command)(*rest)
                except Exception:
                    error_message()
            elif all_users['me']['id'] == sender_id:
                # Check if the person is not me
                important = event.message["text"][2:] if event.message["text"][:2] == '-i' else None
                for att in attachments:
                    download(att, imp=important)

        else:
            print('UNKNOWN EVENT')
