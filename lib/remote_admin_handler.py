#Python 3 Core Libraries
import time
from threading import Thread

# Python 3 Third Party Libraries
from colorama import Fore, Back, Style

# Python 3 Project Libraries
from lib.database_handler import Database
from lib.redis_handler import RedisCache


class RemoteAdmin:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()

        if s[:13] == prefix + "start remote":
            # *** get jid of remote #grouphash
            remote_gjid = Database(self.config).get_group_data_by_hash("str", "group_jid", (s[14:]))
            if not remote_gjid:
                self.client.send_chat_message(chat_message.from_jid,  # send error message
                                              "Invalid #grouphash")
            else:
                group_data = RedisCache(self.config).get_all_group_data(remote_gjid)
                admins = group_data["group_admins"]
                members = group_data["group_members"]
                bot_admins = RedisCache(self.config).get_bot_config_data("list", "bot_admins", self.bot_id)

                # allow bot admins to admin groups
                if chat_message.from_jid in bot_admins:
                    RedisCache(self.config).add_remote_session_data(chat_message.from_jid, chat_message.from_jid, remote_gjid,
                                                         self.bot_id)
                    # set_user_remote(chat_message.from_jid, remote_jid)  # store remote_jid for this user/group combo
                    Thread(target=self.session_timer_thread, args=(chat_message.from_jid, self.bot_id, s[13:],)).start()
                    self.client.send_chat_message(chat_message.from_jid, "Remote started")

                else:
                    for a in admins:
                        if members[a]["jid"] == chat_message.from_jid:
                            RedisCache(self.config).add_remote_session_data(members[a]["jid"], a, remote_gjid, self.bot_id)
                            Thread(target=self.session_timer_thread, args=(members[a]["jid"], self.bot_id, s[13:],)).start()
                            self.client.send_chat_message(chat_message.from_jid, "Remote started")
                            break

        elif s == prefix + "stop remote":
            # *** get remote_jid for this user
            remote_jid = RedisCache(self.config).get_remote_session_data(chat_message.from_jid, self.bot_id)
            if remote_jid:
                RedisCache(self.config).remove_remote_session_data(chat_message.from_jid, self.bot_id)
                self.client.send_chat_message(chat_message.from_jid,
                                              "Remote stopped.")
            else:
                self.client.send_chat_message(chat_message.from_jid,
                                              "You are not running a remote session.")

    def send_message(self, chat_message, output):
        if hasattr(chat_message, "remote_jid"):
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_hash = group_data["group_hash"]
            group_name = group_data["group_name"]
            self.client.send_chat_message(chat_message.remote_jid, "From " + str(group_name) + "\n(" + str(group_hash) +
                                          ")\n\n" + output)
        else:
            self.client.send_chat_message(chat_message.group_jid, output)

    def send_image(self, chat_message, image):
        if hasattr(chat_message, "remote_jid"):
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_hash = group_data["group_hash"]
            group_name = group_data["group_name"]
            self.client.send_chat_message(chat_message.remote_jid, "From " + str(group_name) + "\n(" + str(group_hash) +
                                          ")\n")
            self.client.send_chat_image(chat_message.remote_jid, image)
        else:
            self.client.send_chat_image(chat_message.group_jid, image)

    def session_timer_thread(self, user_jid, bot_id, group_hash):
        while True:
            session_data = RedisCache(self.config).get_remote_session_data(user_jid, bot_id)
            if not session_data:
                break
            elif (time.time() - session_data["last_activity"]) > 300:
                RedisCache(self.config).remove_remote_session_data(user_jid, bot_id)
                self.client.send_chat_message(user_jid, "Remote Admin Ended for: " + group_hash)
                break
            time.sleep(30)