import vk_api as vk
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import TOKEN, ID_BOT, GET_TOK, VK_VER
from functools import partial
from itertools import chain

from data_storage.smart_download import down_smart

# !!!!!!!!!!!!
import requests

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
    - magic_advice : tells you the future


    - any file/photo/video/audio will be downloaded and sorted
    """
    send_response(sender, HELP_MESSAGE)


def unknown_command():
    send_response(sender, "what is my purpose?")


def download(attachment):
    def inner_handle_photo():
        print('photo')
        url = attachment['photo']['orig_photo']['url']
        down_smart(url, ext='jpg')

    def inner_handle_video():
        print('video')
        send_response(sender, "My Lord, the quality of this video is unworthy of you.\n"
                              "I beg you, send it as a file to protect its brilliance. ✨")

    def inner_handle_audio_message():
        if attachment['audio_message'].get('transcript_state') in ('in_progress', None):
            return  # Skip if still in progress
        print('audio_message')

        url = attachment['audio_message']['link_ogg']
        down_smart(url, ext='mp3')
        send_response(sender, "Your voice message is saved!")

    def inner_handle_doc():
        print('doc')
        url = attachment['doc']['url']
        ext = attachment['doc']['ext'].replace('tui', 'mp3')
        down_smart(url, ext)
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
    'wiki': partial(stopper, 'wiki'),
    'lm_travel': partial(stopper, 'lm_travel'),
    'dice': partial(stopper, 'dice'),
    'coin': partial(stopper, 'coin'),
    'magic_advice': partial(stopper, 'magic_advice'),

}




if __name__ == '__main__':
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
                received_message = event.message["text"]
                command = received_message.split()[0].lower().strip()
                # print(sender)
                COMMANDS.get(command, unknown_command)()
            else:
                # print(attachments)
                for att in attachments:
                    download(att)

        else:
            print('UNKNOWN EVENT')