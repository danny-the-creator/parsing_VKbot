import vk_api as vk
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import TOKEN, ID_BOT, all_users, id_name
import threading

from small_features.wiki_info import wiki_search
from small_features.destiny import dice_roll, flip_coin, num_gen, destiny_decoder

def send_response(sender, message):
    vk_session.method("messages.send", {"chat_id": sender, "message": message, "random_id": get_random_id()})
def send_sticker(sender, id):
    vk_session.method("messages.send", {"chat_id": sender, "sticker_id": id, "random_id": get_random_id()})


PART_OF_TRANSMISSION = []

def forward(*args):
    receivers = []
    for receiver in args:
        receiver = receiver.replace(',', '').lower().strip()
        if receiver.replace('-', '') in all_users.keys():
            hidden = True if receiver[-1] == '-' else False
            receivers.append((receiver.replace('-', ''), hidden))
    if receivers == []:
        send_response(sender, f"You should select (existing) receivers\nI won't forward your message to <NOONE>!")
    else:
        send_response(sender, f"All the following messages will be transmitted to: "
                              f"{', '.join([r[0] for r in receivers])}\nto stop it type: stop_ ")
        thread = threading.Thread(target=transmission, args=(receivers,))
        thread.start()

def transmission(receivers):
    global PART_OF_TRANSMISSION
    PART_OF_TRANSMISSION = [all_users[r[0]]['chat'] for r in receivers] + [all_users['me']['chat']]
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and event.chat_id in PART_OF_TRANSMISSION:
            user_name = id_name[event.message['from_id']]
            if user_name == 'me':
                if len(event.message['text']) > 4 and event.message['text'] == 'stop_':
                    send_response(all_users[user_name]['chat'], "End of transmission, ready to serve your orders, Commander!")
                    PART_OF_TRANSMISSION = []
                    break
                for receiver in receivers:
                    if receiver[1]:
                        message = event.message['text']
                    else:
                        message = f'message from my overlord:\n\"{event.message["text"]}\"'
                    send_response(all_users[receiver[0]]['chat'], message)
            if user_name in [r[0] for r in receivers]:
                send_response(all_users['me']['chat'], f"{user_name} sends: \"{event.message['text']}\"")






def execute(func, user, *rest):
    if func.__name__ in all_users[id_name[user]]['access_rights'] or func.__name__ == 'unknown_command':
        func(*rest)
    else:
        send_response(sender, "Sorry, I cannot do that for you")
        send_sticker(sender, 69385)

def start():
    send_response(sender, "I AM ALIVE!!!")


def help():
    HELP_MESSAGE = """
    Greetings Commander! 
    I am your personal assistant and I am ready to follow your orders!
    At least orders from the list below...
    Please type:
    - help : To get this list again 
    - info : Get your day-to-day information
    - add_task : every message after this command will appear in to-do list
    - stop_ : Stops the current process and returns to the main functionality
    - list : to show all of your tasks 
    - forward <ID_1 ID_2 ID_3> : after that all the messages will be send to the indicated receiver's IDs
    - finish_reminder <number> : mark the reminder as done and stops reminding about it
    - wiki <your statement> : To get info about your statement from wiki
    - LM_travel : gives you several decent links about LM_travel

    - dice : roles a dice for you
    - coin : flips a coin for you
    - magic_advice : tells you the destiny
    - rand <number> : returns you random number in range

    - any file/photo/video/audio will be downloaded and sorted
    """
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

def stopper():
    send_response(sender, f"Did you mean <{command}> ? \nThen I cannot help you :<")
    # the way to send a sticker, if you want to send emodji use this in your message: &#000000; (id)
    send_sticker(sender, 69407)

COMMANDS = {
    'start': start,
    'help': help,
    'info': stopper,
    'stop': stopper,
    'list': stopper,
    'add_task': stopper,
    'forward': forward,
    'finish_reminder': stopper,
    'wiki': wiki,
    'lm_travel': stopper,

    'dice': dice,
    'coin': coin,
    'magic_advice': magic_advice,
    'rand': rand
}




if __name__ == '__main__':
    print("Start the session")
    vk_session = vk.VkApi(token=TOKEN)
    longpoll = VkBotLongPoll(vk_session, ID_BOT)
    print("Bot is running...")
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
            print("New Message")
            sender = event.chat_id
            if sender in PART_OF_TRANSMISSION:
                continue
            received_message = event.message["text"].split()
            command = received_message[0].lower().strip()
            rest = received_message[1:]
            sender_id = event.message['from_id']
            execute(COMMANDS.get(command, unknown_command), sender_id, *rest)
        else:
            print('UNKNOWN EVENT')


