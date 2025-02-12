import vk_api as vk
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import requests
from functools import partial
from itertools import chain

from small_features.wiki_info import wiki_search
from small_features.destiny import dice_roll, flip_coin, num_gen, destiny_decoder
from data_storage.smart_download import down_smart
from parsing.LM_travel_deals import LM_Parser

from config import TOKEN, ID_BOT, HEADERS

def send_response(sender, message):
    vk_session.method("messages.send", {"chat_id": sender, "message": message, "random_id": get_random_id()})
def send_sticker(sender, id):
    vk_session.method("messages.send", {"chat_id": sender, "sticker_id": id, "random_id": get_random_id()})

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
    - stop : Stops the current process and returns to the main functionality
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
    lang_codes = ['aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'ar', 'as', 'av', 'ay', 'az', 'ba', 'be', 'bg', 'bh', 'bi', 'bm', 'bn', 'bo', 'br', 'bs', 'ca', 'ce', 'ch', 'co', 'cr', 'cs', 'cu', 'cv', 'cy', 'da', 'de', 'dv', 'dz', 'ee', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'ff', 'fi', 'fj', 'fo', 'fr', 'fy', 'ga', 'gd', 'gl', 'gn', 'gu', 'gv', 'ha', 'he', 'hi', 'ho', 'hr', 'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie', 'ig', 'ii', 'ik', 'io', 'is', 'it', 'iu', 'ja', 'jv', 'ka', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn', 'ko', 'kr', 'ks', 'ku', 'kv', 'kw', 'ky', 'la', 'lb', 'lg', 'li', 'ln', 'lo', 'lt', 'lu', 'lv', 'mg', 'mh', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 'my', 'na', 'nb', 'nd', 'ne', 'ng', 'nl', 'nn', 'no', 'nr', 'nv', 'ny', 'oc', 'oj', 'om', 'or', 'os', 'pa', 'pi', 'pl', 'ps', 'pt', 'qu', 'rm', 'rn', 'ro', 'ru', 'rw', 'sa', 'sc', 'sd', 'se', 'sg', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st', 'su', 'sv', 'sw', 'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw', 'ty', 'ug', 'uk', 'ur', 'uz', 've', 'vi', 'vo', 'wa', 'wo', 'xh', 'yi', 'yo', 'za', 'zh', 'zu']
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


def stopper(command):
    send_response(sender, f"Did you mean <{command}> ? \nThen I cannot help you :<")
    # the way to send a sticker, if you want to send emoji use this in your message: &#000000; (id)
    send_sticker(sender, 69407)

COMMANDS = {
    'start': start,
    'help': help,
    'info': partial(stopper, 'info'),
    'stop': partial(stopper, 'stop'),
    'list': partial(stopper, 'list'),
    'add_task': partial(stopper, 'add_task'),
    'forward': partial(stopper, 'forward'),
    'finish_reminder': partial(stopper, 'finish_reminder'),
    'wiki': wiki,
    'lm_travel': lm_travel,

    'dice': dice,
    'coin': coin,
    'magic_advice': magic_advice,
    'rand': rand
}




if __name__ == '__main__':

    parser = LM_Parser(500, -1, num_review=-1, dep_in=1)
    parser.set_settings(directory='./data_storage/data', headers=HEADERS)
    parser.set_hottest(max_price=500, min_review=8, num_review=350, dep_in=0)

    print("Start the session")
    vk_session = vk.VkApi(token=TOKEN)
    longpoll = VkBotLongPoll(vk_session, ID_BOT)
    print("Bot is running...")
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
            attachments = event.message["attachments"] + list(chain(*[m.get("attachments", []) for m in event.message['fwd_messages']]))
            sender = event.chat_id
            if not attachments:
                print("New Message")
                received_message = event.message["text"].split()
                command = received_message[0].lower().strip()
                rest = received_message[1:]
                sender = event.chat_id
                # print(sender)
                COMMANDS.get(command, unknown_command)(*rest)
            else:
                important = event.message["text"][2:] if event.message["text"][:2] == '-i' else None
                for att in attachments:
                    download(att, imp=important)

        else:
            print('UNKNOWN EVENT')
