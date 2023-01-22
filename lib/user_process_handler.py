import os
import shutil
import time

import numpy as np
import requests
from colorama import Style, Fore

from lib.group_admin_tools import Verification, Silent
from lib.image_response_handler import check_pfp
from lib.message_processing_handler import process_message, MessageProcessing
from lib.redis_handler import RedisCache
from lib.user_handler import User


class UserProcess:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name
        self.bot_username = client.bot_username
        self.debug = f'[' + Style.BRIGHT + Fore.CYAN + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.CYAN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

    def process_join_user(self, peer_data, peer_info, peer_jid, join_data):
        user_days = (time.time() - peer_info.creation_date_seconds) / 86400

        RedisCache(self.config).update_join_queue_user("days", user_days, peer_jid, self.bot_id)
        group_data = RedisCache(self.config).get_all_group_data(join_data["group_jid"])
        group_settings = group_data["group_settings"]
        group_messages = group_data["group_messages"]

        noob_status = group_settings["noob_status"]
        noob_days = group_settings["noob_days"]
        noob_message = group_messages["noob_message"]

        if peer_data:
            if group_settings["profile_status"] == 1:
                print("Process Default PFP")
                if peer_data["pfp"] == "default.jpg":
                    self.client.send_chat_message(join_data["group_jid"],
                                                  "You need to set a profile picture to join this group.")
                    self.client.remove_peer_from_group(join_data["group_jid"], peer_jid)
                    User(self).group_user_remove(peer_jid, join_data["group_jid"])
                    if os.path.exists(self.config["paths"]["user_img"] + peer_jid + ".jpg"):
                        os.remove(self.config["paths"]["user_img"] + peer_jid + ".jpg")
                    return

                picurl = requests.get(peer_data["pfp"], stream=True)
                if picurl.status_code == 200:
                    save_path = self.config["paths"]["user_img"] + peer_jid + ".jpg"
                    with open(save_path, 'wb') as f:
                        picurl.raw.decode_content = True
                        shutil.copyfileobj(picurl.raw, f)
                        f.close()
                    if os.path.exists(self.config["paths"]["user_img"] + peer_jid + ".jpg"):
                        result = check_pfp(self.config, peer_jid)
                        if result >= 1:
                            self.client.send_chat_message(join_data["group_jid"],
                                                     "You need to set a profile picture to join this group.")
                            self.client.remove_peer_from_group(join_data["group_jid"], peer_jid)
                            User(self).group_user_remove(peer_jid, join_data["group_jid"])
                            if os.path.exists(self.config["paths"]["user_img"] + peer_jid + ".jpg"):
                                os.remove(self.config["paths"]["user_img"] + peer_jid + ".jpg")
                            return
                        else:
                            if os.path.exists(self.config["paths"]["user_img"] + peer_jid + ".jpg"):
                                os.remove(self.config["paths"]["user_img"] + peer_jid + ".jpg")

        if noob_status == 1 and user_days <= int(noob_days):
            # remove noob activated
            if noob_message != "none":
                noob_message = process_message(self.config, "join", noob_message, peer_jid, join_data["group_jid"],
                                               self.bot_id, round(np.ceil(user_days)))
                self.client.send_chat_message(join_data["group_jid"], noob_message)

            # remove user
            self.client.remove_peer_from_group(join_data["group_jid"], peer_jid)
            User(self).group_user_remove(peer_jid, join_data["group_jid"])

        elif group_settings["verification_status"] == 1:
            if user_days <= group_settings["verification_days"]:
                # verification triggered

                # do verification
                Verification(self).send_verification(peer_jid, join_data["group_jid"])


            else:
                if group_settings["welcome_status"] == 1:
                    print("Welcome Message Triggered")
                    if group_messages["welcome_message"] != "none":
                        # process and send welcome message
                        MessageProcessing(self).process_message_media("welcome_message",
                                                                      group_messages["welcome_message"], peer_jid,
                                                                      join_data["group_jid"])

        elif group_settings["silent-join_status"] == 1:
            # silent join triggered
            if group_settings["welcome_status"] == 1:
                # welcome message triggered
                if group_messages["welcome_message"] != "none":
                    # process and send welcome message
                    MessageProcessing(self).process_message_media("welcome_message", group_messages["welcome_message"],
                                                                  peer_jid,
                                                                  join_data["group_jid"])

            # Start Silent Timer
            Silent(self).silent_timeout(peer_jid, join_data["group_jid"], self.bot_id)
            print("Start Silent Timer")

        else:
            # welcome message sent if verification is off and passed other checks like noob
            if group_settings["welcome_status"] == 1:
                # welcome message triggered
                if group_messages["welcome_message"] != "none":
                    # process and send welcome message
                    MessageProcessing(self).process_message_media("welcome_message", group_messages["welcome_message"], peer_jid,
                                          join_data["group_jid"])