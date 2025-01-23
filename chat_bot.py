import vk_api as vk
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import TOKEN, ID

vk_session = vk.VkApi(token=TOKEN)
longpoll = VkBotLongPoll(vk_session, ID)

def send_response(sender, message):
    vk_session.method("messages.send", {"chat_id": sender, "message": message, "random_id": 0})


for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
        command = event.message["text"]
        sender = event.chat_id
        if command == 'hi':
            send_response(sender, "I AM ALIVE!!!")
        else:
            send_response(sender, "what is my purpose?")