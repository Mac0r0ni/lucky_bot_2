import random
import time

from colorama import Fore, Style

from lib.redis_handler import RedisCache
from lib.remote_admin_handler import RemoteAdmin


class PrivateMessage:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def private_message_parser(self, chat_message):
        if self.config["general"]["debug"] == 1:
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "[+] '{}' says: {}".format(chat_message.from_jid,
                                                                                chat_message.body) + Style.RESET_ALL)
        pm = chat_message.body.lower()
        jid = chat_message.from_jid
        prefix = self.config["general"]["prefix"]

        if pm == "ping":
            ping_resp = ["What do you want boner?", "Yea I am here.. Unfortunately", "Polo... wait no Pong",
                         "The person ^ gives good head.", "I'm with stupid ^", "Damn, you are so annoying.",
                         "Ping your damn self.", "Hey dingus.", "Uhhh, I don't give a shit.",
                         "Clingy much? Fuck dude..."]
            self.client.send_chat_message(jid, random.choice(ping_resp))
        elif pm == "friend":
            self.client.add_friend(jid)
            self.client.send_chat_message(jid, "Today is your lucky day, we are now friends.")

        elif pm[:13] == prefix + "start remote":
            print("Starting Remote")
            RemoteAdmin(self).main(chat_message, prefix)

        elif pm == prefix + "stop remote":
            print("Stopping Remote")
            RemoteAdmin(self).main(chat_message, prefix)

        else:
            remote_sessions = RedisCache(self.config).get_all_remote_sessions(self.bot_id)
            if chat_message.from_jid.encode('utf-8') in remote_sessions:
                session_data = RedisCache(self.config).get_remote_session_data(chat_message.from_jid, self.bot_id)
                chat_message.remote_jid = chat_message.from_jid
                chat_message.group_jid = str(session_data["group_jid"]) + '@groups.kik.com'
                chat_message.from_jid = session_data["user_ajid"]
                RedisCache(self.config).update_remote_session_data(chat_message.from_jid, "last_activity", time.time(), self.bot_id)

                self.callback.on_group_message_received(chat_message)
