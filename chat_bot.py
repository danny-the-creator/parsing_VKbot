import vk_api as vk
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import TOKEN, ID
from functools import partial
from itertools import chain


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


def stopper(command):
    send_response(sender, f"Did you mean <{command}> ? \nThen I cannot help you :<")
    # the way to send a sticker, if you want to send emodji use this in your message: &#000000; (id)
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
    longpoll = VkBotLongPoll(vk_session, ID)
    print("Bot is running...")
    for event in longpoll.listen():
        # print(event.message['text'])
        # print(event.message)
        print('---------------------------------------------------------')
        # print(event.message['attachments'])
        # print(event.message.get('reply_message'))           # ignore
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
            attachments = event.message["attachments"] + list(chain(*[m.get("attachments", []) for m in event.message['fwd_messages']]))
            if not attachments:
                print("New Message")
                received_message = event.message["text"]
                command = received_message.split()[0].lower().strip()
                sender = event.chat_id
                # print(sender)
                COMMANDS.get(command, unknown_command)()
            else:
                print(attachments)
                for att in attachments:
                    print()
                    if att.get('type') == 'photo':
                        print('photo')
                        print(f"url: {att['photo']['orig_photo']['url']}")
                    elif att.get('type') == 'video':
                        print('video')
                        print(f"access_key: {att['video']['track_code']}")
                    elif att.get('type') == 'doc':
                        print('doc')
                        print(f"url: {att['doc']['url']}")
                        print(f"ext: {att['doc']['ext']}")
                    elif att.get('type') == 'audio_message':
                        print('audio_message')
                        print(f"url: {att['audio_message']['link_mp3']}")
                    else:
                        print('UNKNOWN')

        else:
            print('UNKNOWN EVENT')