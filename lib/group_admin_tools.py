from threading import Timer, Thread

from lib.feature_status_handler import FeatureStatus
from lib.message_processing_handler import process_message
from lib.redis_handler import RedisCache
from lib.remote_admin_handler import RemoteAdmin
from lib.user_handler import User


class WelcomeMessage:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        s = chat_message.body.lower()
        if s == prefix + "welcome":
            group_settings = group_data["group_settings"]
            if group_settings["welcome_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "welcome_status")
        elif s[:16] == prefix + "welcome message":
            welcome_message = chat_message.body[17:]
            FeatureStatus(self).set_feature_message(chat_message, "welcome_message", welcome_message)
            return
        elif s == prefix + "welcome status":
            group_messages = group_data["group_messages"]
            group_settings = group_data["group_settings"]

            welcome_status = group_settings["welcome_status"]
            welcome_message = group_messages["welcome_message"]

            if welcome_status == 1:
                status_string = "Welcome Status: On \n"
                if welcome_message != "none":
                    status_string += "Welcome Message: " + welcome_message + "\n"
                else:
                    status_string += "Welcome message is not set \n"
            else:
                status_string = "Welcome Status: Off \n"

            RemoteAdmin(self).send_message(chat_message, status_string)

class NameGrab:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_messages = group_data["group_messages"]
        group_settings = group_data["group_settings"]
        if s == prefix + "grab":
            print(type(group_settings["grab_status"]))
            print(group_settings["grab_status"])
            if group_settings["grab_status"] == 1:
                status = 0
            else:
                status = 1

            FeatureStatus(self).set_feature_status(chat_message, status, "grab_status")
        elif s == prefix + "grab status":

            grab_status = group_settings["grab_status"]

            if grab_status == 1:
                status_string = "Name Grab Status: On" + "\n"
            else:
                status_string = "Name Grab Status: Off" + "\n"

            RemoteAdmin(self).send_message(chat_message, status_string)

class Lock:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_settings = group_data["group_settings"]
        group_messages = group_data["group_messages"]
        s = chat_message.body.lower()
        if s == prefix + "lock":
            if group_settings["lock_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "lock_status")
        elif s[:13] == prefix + "lock message":
            lock_message = chat_message.body[14:]
            FeatureStatus(self).set_feature_message(chat_message, "lock_message", lock_message)
        elif s == prefix + "lock status":
            lock_status = group_settings["lock_status"]
            lock_message = group_messages["lock_message"]
            if lock_status == 1:
                status_string = "Lock Status: On" + "\n"
                if lock_message != "none":
                    status_string += "Lock Message: " + lock_message + "\n"
                else:
                    status_string += "Lock message is not set." + "\n"
            else:
                status_string = "Lock Status: Off" + "\n"

            RemoteAdmin(self).send_message(chat_message, status_string)
        else:
            return


class Noob:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_settings = group_data["group_settings"]
        group_messages = group_data["group_messages"]
        s = chat_message.body.lower()
        if s == prefix + "noob":  # admin
            if group_settings["noob_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "noob_status")

        elif prefix + "noob days" in s:  # admin
            try:
                d = int(s.split(prefix + "noob days ")[1])
                FeatureStatus(self).set_feature_setting(chat_message, "noob_days", d)
            except Exception:
                RemoteAdmin(self).send_message(chat_message, "Give only a number after command\n Example: " + prefix + "noob days 10")
        elif s[:13] == prefix + "noob message":
            noob_msg = chat_message.body[14:]
            FeatureStatus(self).set_feature_message(chat_message, "noob_message", noob_msg)

        elif s == prefix + "noob status":
            noob_status = group_settings["noob_status"]
            noob_days = group_settings["noob_days"]
            noob_message = group_messages["noob_message"]

            if noob_status == 1:
                status_string = "Noob Filter Status: On" + "\n"
                status_string += "Filter Days: " + str(noob_days) + " days.\n"
                if noob_message != "none":
                    status_string += "Noob Removal Message: " + noob_message + "\n"
                else:
                    status_string += "Noob Removal message isnot set." + "\n"
            else:
                status_string = "Noob Filter Status: Off" + "\n"

            RemoteAdmin(self).send_message(chat_message, status_string)

        else:
            return


class Invite:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_settings = group_data["group_settings"]
        group_messages = group_data["group_messages"]
        s = chat_message.body.lower()

        if s == prefix + "invite":

            if group_settings["lock-invite_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "lock-invite_status")
        elif s == prefix + "invite verify" in s:
            if group_settings["invite-verification_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "invite-verification_status")

        elif s[:15] == prefix + "invite message" in s:
            invite_msg = chat_message.body[16:]
            FeatureStatus(self).set_feature_message(chat_message, "lock-invite_message", invite_msg)

        elif s == prefix + "invite status":
            invite_status = group_settings["lock-invite_status"]
            invite_verification = group_settings["invite-verification_status"]
            invite_message = group_messages["lock-invite_message"]
            if invite_status == 1:
                status_string = "Invite Lock Status: On" + "\n"
                if invite_message != "none":
                    status_string += "Invite Lock Message: " + invite_message + "\n"
                else:
                    status_string += "Invite Lock message is not set." + "\n"
            else:
                status_string = "Invite Lock Status: Off" + "\n"

            if invite_verification == 1:
                status_string += "Invite Verify Status: On" + "\n"
            else:
                status_string += "Invite Verify Status: Off" + "\n"
            RemoteAdmin(self).send_message(chat_message, status_string)
        else:
            return


class Verification:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_settings = group_data["group_settings"]
        group_messages = group_data["group_messages"]
        s = chat_message.body.lower()

        if s == prefix + "verify":
            if group_settings["verification_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "verification_status")

        elif prefix + "verify time " in s:
            try:
                ti = float(s.split(prefix + "verify time ")[1]) * 60
                FeatureStatus(self).set_feature_setting(chat_message, "verification_time", ti)
            except Exception:
                RemoteAdmin(self).send_message(chat_message, "Give only a number after command\n Example: " + prefix + "verification time 5")

        elif prefix + "verify days " in s:
            try:
                d = int(s.split(prefix + "verify days ")[1])
                FeatureStatus(self).set_feature_setting(chat_message, "verification_days", d)
            except Exception as e:
                print(e)
                RemoteAdmin(self).send_message(chat_message, "Give only a number after command\n Example: " + prefix + "verify days 10")

        elif s == prefix + "verify invite" in s:
            if group_settings["invite-verification_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "invite-verification_status")

        elif s[:15] == prefix + "verify message":
            verification_msg = chat_message.body[16:]
            FeatureStatus(self).set_feature_message(chat_message, "verification_message", verification_msg)

        elif s[:14] == prefix + "verify phrase":
            verification_phrase = chat_message.body[15:].lower()
            FeatureStatus(self).set_feature_message(chat_message, "verification_phrase", verification_phrase)

        elif s[:12] == prefix + "verify fail":
            verification_msg = chat_message.body[13:]
            FeatureStatus(self).set_feature_message(chat_message, "verification_wrong_message", verification_msg)
        elif s[:11] == prefix + "verify end":
            verification_msg = chat_message.body[12:]
            FeatureStatus(self).set_feature_message(chat_message, "verification_ended_message", verification_msg)

        elif s == prefix + "verify status":
            verification_status = group_settings["verification_status"]
            verification_phrase = group_messages["verification_phrase"]
            verification_message = group_messages["verification_message"]
            verification_wrong_message = group_messages["verification_wrong_message"]
            verification_ended_message = group_messages["verification_ended_message"]
            verification_days = group_settings["verification_days"]
            verification_time = group_settings["verification_time"]
            invite_verification = group_settings["invite-verification_status"]
            v_time = verification_time / 60
            if verification_status == 1:
                status_string = "Verify Status: On" + "\n"
                status_string += "Verify Days: " + str(verification_days) + " days.\n"
                status_string += "Verify Time: " + str(v_time) + " minutes.\n"
                if invite_verification == 1:
                    status_string += "Invite Verify: On" + "\n"
                else:
                    status_string += "Invite Verify: Off" + "\n"
                status_string += "Verify Phrase: " + str(verification_phrase) + "\n"
                status_string += "Verify Message: " + verification_message + "\n"
                status_string += "Verify Fail: " + verification_wrong_message + "\n"
                status_string += "Verify End: " + verification_ended_message + "\n"
            else:
                status_string = "Verify Status: Off" + "\n"
            RemoteAdmin(self).send_message(chat_message, status_string)

        else:
            return

    def send_verification(self, peer_jid, group_jid):
        peer_info = RedisCache(self.config).get_single_join_queue(peer_jid, self.bot_id)
        if peer_info is not None:
            group_data = RedisCache(self.config).get_all_group_data(group_jid)
            group_settings = group_data["group_settings"]
            group_messages = group_data["group_messages"]

            if group_settings:
                verification_message = group_messages["verification_message"]
                verification_time = group_settings["verification_time"]
                verification_phrase = group_messages["verification_phrase"]

                if verification_message != 'none':
                    v_message = process_message(self.config, "join", verification_message, peer_jid,
                                                peer_info['group_jid'], self.bot_id, "0")
                    self.client.send_chat_message(peer_info['group_jid'], v_message)

                RedisCache(self.config).update_join_queue_user('phrase', verification_phrase, peer_jid, self.bot_id)
                verify_thread = Timer(int(verification_time), self.removal_check,
                                      args=(peer_jid, peer_info['group_jid']))
                verify_thread.start()

    def eval_message(self, peer_jid, group_jid, body):
        peer_info = RedisCache(self.config).get_single_join_queue(peer_jid, self.bot_id)
        if peer_info["group_jid"] == group_jid:
            phrase_thread = Thread(target=self.response_eval,
                                   args=(peer_jid, group_jid, body))
            phrase_thread.daemon = True
            phrase_thread.start()

    def removal_check(self, user_jid, group_jid):
        peer_info = RedisCache(self.config).get_single_join_queue(user_jid, self.bot_id)
        if not peer_info:
            return
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_settings = group_data["group_settings"]
        group_messages = group_data["group_messages"]
        if peer_info:
            if peer_info["verified"] == 1:
                RedisCache(self.config).remove_from_join_queue(user_jid, self.bot_id)
            else:
                if group_settings:
                    verification_ended_message = group_messages["verification_ended_message"]
                    if verification_ended_message != "none":
                        vended_message = process_message(self.config, "join", verification_ended_message,
                                                         user_jid, peer_info['group_jid'],
                                                         self.bot_id, "0")
                        self.client.send_chat_message(peer_info['group_jid'], vended_message)

                    self.client.remove_peer_from_group(peer_info['group_jid'], user_jid)
                    User(self).group_user_remove(user_jid, peer_info['group_jid'])

        else:
            return

    def response_eval(self, peer_jid, group_jid, response):
        peer_info = RedisCache(self.config).get_single_join_queue(peer_jid, self.bot_id)
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_settings = group_data["group_settings"]
        group_messages = group_data["group_messages"]
        if peer_info:
            if "phrase" in peer_info.keys():
                phrase_answer = response.lower()
                if peer_info["phrase"] == phrase_answer:
                    correct = 1
                else:
                    correct = 0

                if correct == 1:
                    # can add another welcome thingy here welcome_image
                    # this wont happen unless phrase is correct
                    if group_messages:
                        welcome_message = group_messages["welcome_message"]
                        if welcome_message != "none":
                            welcome_message = process_message(self.config, "join", welcome_message,
                                                             peer_jid, peer_info['group_jid'],
                                                             self.bot_id, "0")
                            self.client.send_chat_message(peer_info['group_jid'], welcome_message)
                    RedisCache(self.config).update_join_queue_user("verified", 1, peer_jid, self.bot_id)
                elif correct == 0:
                    verification_wrong_message = group_messages["verification_wrong_message"]
                    if verification_wrong_message:
                        vwrong_message = process_message(self.config, "join", verification_wrong_message,
                                                         peer_jid, peer_info['group_jid'],
                                                         self.bot_id, "0")
                        self.client.send_chat_message(group_jid, vwrong_message)
