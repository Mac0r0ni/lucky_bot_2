import os
import time
from threading import Timer, Thread

from colorama import Style, Fore

from lib.bot_utility import convert_time
from lib.database_handler import Database
from lib.feature_status_handler import FeatureStatus
from lib.image_response_handler import media_forward_timeout
from lib.message_processing_handler import process_message, MessageProcessing
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
        self.bot_username = client.bot_username
        self.debug = f'[' + Style.BRIGHT + Fore.CYAN + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.CYAN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_messages = group_data["group_messages"]
        group_settings = group_data["group_settings"]
        current_dir = os.getcwd() + "/"

        s = chat_message.body.lower()
        if s == prefix + "welcome":
            group_settings = group_data["group_settings"]
            if group_settings["welcome_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "welcome_status")

        elif s[:16] == prefix + "welcome message":
            new_welcome_message = chat_message.body[17:]
            if new_welcome_message[:2] == "$i" or new_welcome_message[:2] == "$g" or new_welcome_message[:2] == "$v":
                if new_welcome_message[:3] == "$gs" or new_welcome_message[:3] == "$gn" or new_welcome_message[
                                                                                           :3] == "$gh":
                    FeatureStatus(self).set_feature_message(chat_message, "welcome_message", new_welcome_message)
                    return
                else:

                    if current_dir + self.config["paths"]["message_media"] in group_messages["welcome_message"]:
                        if "] " in group_messages["welcome_message"]:
                            check = group_messages["welcome_message"].split("] ")[1]
                        else:
                            check = group_messages["welcome_message"]
                        if os.path.exists(check):
                            os.remove(check)
                    RedisCache(self.config).add_to_media_message_queue(new_welcome_message, "add", "welcome_message",
                                                                       chat_message.from_jid,
                                                                       chat_message.group_jid)
                    MessageProcessing(self).media_message_timeout(chat_message, chat_message.from_jid,
                                                                  chat_message.group_jid)
            else:
                FeatureStatus(self).set_feature_message(chat_message, "welcome_message", new_welcome_message)
            return
        elif s == prefix + "welcome status":

            welcome_status = group_settings["welcome_status"]
            welcome_message = group_messages["welcome_message"]

            if welcome_status == 1:
                status_string = "Welcome Status: On" + "\n"
                if welcome_message != "none":

                    if welcome_message[-4:] == "json" or welcome_message[-3:] == "png" or welcome_message[
                                                                                          -3:] == "jpg" or welcome_message[
                                                                                                           -3:] == "mp4":
                        if welcome_message[-4:] == "json":
                            media_type = "gif"
                        elif welcome_message[-3:] == "png" or welcome_message[-3:] == "jpg":
                            media_type = "Image"
                        elif welcome_message[-3:] == "mp4":
                            media_type = "Video"
                        else:
                            media_type = "Media"

                        if "] " in group_messages["welcome_message"]:
                            try:
                                text = group_messages["welcome_message"].split("] ")[0].replace("[", "")
                            except:
                                text = "Unknown"
                        else:
                            text = "None"

                        status_string += "Type: " + media_type + "\n" + "Text: " + str(text) + "\n"

                    else:
                        status_string += "Welcome Message: " + welcome_message + "\n"
                else:
                    status_string += "Welcome message is not set." + "\n"
            else:
                status_string = "Welcome Status: Off" + "\n"

            RemoteAdmin(self).send_message(chat_message, status_string)


class LeaveMessage:
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

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_settings = group_data["group_settings"]
        group_messages = group_data["group_messages"]
        current_dir = os.getcwd() + "/"
        s = chat_message.body.lower()
        if s == prefix + "exit":

            if group_settings["exit_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "exit_status")
        elif s[:13] == prefix + "exit message":
            welcome_message = chat_message.body[14:]
            if welcome_message[:2] == "$i" or welcome_message[:2] == "$g" or welcome_message[:2] == "$v":
                if welcome_message[:3] == "$gs" or welcome_message[:3] == "$gn" or welcome_message[:3] == "$gh":
                    FeatureStatus(self).set_feature_message(chat_message, "exit_message", welcome_message)
                    return
                else:

                    if current_dir + self.config["paths"]["message_media"] in group_messages["exit_message"]:
                        if "] " in group_messages["exit_message"]:
                            check = group_messages["exit_message"].split("] ")[1]
                        else:
                            check = group_messages["exit_message"]
                        if os.path.exists(check):
                            os.remove(check)
                    RedisCache(self.config).add_to_media_message_queue(welcome_message, "add", "exit_message",
                                                                       chat_message.from_jid,
                                                                       chat_message.group_jid)
                    MessageProcessing(self).media_message_timeout(chat_message, chat_message.from_jid,
                                                                  chat_message.group_jid)
            else:
                FeatureStatus(self).set_feature_message(chat_message, "exit_message", welcome_message)
            return
        elif s == prefix + "exit status":
            leave_status = group_settings["exit_status"]
            leave_message = group_messages["exit_message"]

            if leave_status == 1:
                status_string = "Exit Status: On" + "\n"
                if leave_message != "none":
                    if leave_message[-4:] == "json" or leave_message[-3:] == "png" or leave_message[
                                                                                      -3:] == "jpg" or leave_message[
                                                                                                       -3:] == "mp4":
                        if leave_message[-4:] == "json":
                            media_type = "gif"
                        elif leave_message[-3:] == "png" or leave_message[-3:] == "jpg":
                            media_type = "Image"
                        elif leave_message[-3:] == "mp4":
                            media_type = "Video"
                        else:
                            media_type = "Media"

                        if "] " in group_messages["exit_message"]:
                            try:
                                text = group_messages["exit_message"].split("] ")[0].replace("[", "")
                            except:
                                text = "Unknown"
                        else:
                            text = "None"

                        status_string += "Type: " + media_type + "\n" + "Text: " + str(text) + "\n"
                    else:
                        status_string += "Exit Message: " + leave_message + "\n"
                else:
                    status_string += "Exit message is not set."
            else:
                status_string = "Exit Status: Off"

            RemoteAdmin(self).send_message(chat_message, status_string)


class NameGrab:
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
        self.bot_username = client.bot_username
        self.debug = f'[' + Style.BRIGHT + Fore.CYAN + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.CYAN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

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
        self.bot_username = client.bot_username
        self.debug = f'[' + Style.BRIGHT + Fore.CYAN + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.CYAN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

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

        elif s[:10] == prefix + "noob days" in s:  # admin
            try:
                d = int(s.split(prefix + "noob days ")[1])
                FeatureStatus(self).set_feature_setting(chat_message, "noob_days", d)
            except Exception as e:
                print(repr(e))
                RemoteAdmin(self).send_message(chat_message,
                                               "Give only a number after command\n Example: " + prefix + "noob days 10")
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
        self.bot_username = client.bot_username
        self.debug = f'[' + Style.BRIGHT + Fore.CYAN + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.CYAN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

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


class GroupTimer:
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

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_messages = group_data["group_messages"]
        s = chat_message.body.lower()

        if s == prefix + "timer stop":  # admin
            Thread(target=self.stop_timer, args=(chat_message,)).start()

        elif s[:14] == prefix + "timer message":
            timer_msg = chat_message.body[15:]
            FeatureStatus(self).set_feature_message(chat_message, "timer_message", timer_msg)

        elif s == prefix + "timer status":
            if group_messages:
                timer_message = group_messages["timer_message"]
                if timer_message != 'none':
                    status_message = "Timer Message: " + timer_message
                else:
                    status_message = "Timer Message: Off"

                RemoteAdmin(self).send_message(chat_message, status_message)

        elif prefix + "timer " in s:  # admin
            try:
                timer_data = s.split(prefix + "timer ")[1]
                if timer_data.split(" ")[1] == "s":
                    timer_time = int(timer_data.split(" ")[0])
                    Thread(target=self.start_timer,
                           args=(chat_message, timer_time)).start()
                elif timer_data.split(" ")[1] == "m":
                    timer_time = int(timer_data.split(" ")[0]) * 60
                    Thread(target=self.start_timer,
                           args=(chat_message, timer_time)).start()
                else:
                    RemoteAdmin(self).send_message(chat_message, "Time needs specified "
                                                   + prefix + "timer 5 s")
                    return
            except Exception:
                RemoteAdmin(self).send_message(chat_message, "Give only a number after command: Example:\n" +
                                               prefix + "timer 5 s")

    def start_timer(self, chat_message, seconds):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        if not group_data:
            return
        group_messages = group_data["group_messages"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        admins = group_data["group_admins"]
        all_admins = {**bot_admins, **admins}
        if all_admins:
            if chat_message.from_jid in all_admins:
                if seconds > 3600:
                    RemoteAdmin(self).send_message(chat_message, "Time can't be set for more than 20 minutes.")
                    return
                timers = RedisCache(self.config).get_all_timer_cache(chat_message.group_jid)
                if not timers:
                    timers = {"None": "None"}
                if not chat_message.from_jid.encode("utf-8") in timers:
                    if seconds >= 60:
                        ctime = seconds // 60
                        if ctime == 1:
                            units = "minute"
                        else:
                            units = "minutes"
                    else:
                        ctime = seconds
                        if ctime == 1:
                            units = "second"
                        else:
                            units = "seconds"

                    RemoteAdmin(self).send_message(chat_message, "Timer started for: " + str(ctime) + " " + units + ".")
                    RedisCache(self.config).add_timer_cache(chat_message.from_jid, chat_message.group_jid)
                    while seconds > 0:
                        data = RedisCache(self.config).get_timer_cache(chat_message.from_jid, chat_message.group_jid)
                        if data["stop"]:
                            RemoteAdmin(self).send_message(chat_message, "Timer stopped.")
                            RedisCache(self.config).rem_from_timer_cache(chat_message.from_jid, chat_message.group_jid)
                            return
                        if seconds <= 3 and seconds != 0:
                            RemoteAdmin(self).send_message(chat_message, str(seconds))
                        seconds -= 1
                        time.sleep(1)

                    RedisCache(self.config).rem_from_timer_cache(chat_message.from_jid, chat_message.group_jid)
                    if group_messages["timer_message"] != 'none':
                        final = process_message(self.config, "group", group_messages["timer_message"],
                                                chat_message.from_jid,
                                                chat_message.group_jid, self.bot_id, "0")
                        RemoteAdmin(self).send_message(chat_message, final)
                    return
                else:
                    RemoteAdmin(self).send_message(chat_message, "Timer must be less than twenty minutes.")

            else:
                RemoteAdmin(self).send_message(chat_message, f'Only admins can use {chat_message.body}')

    def stop_timer(self, message):
        timers = RedisCache(self.config).get_all_timer_cache(message.group_jid)
        if message.from_jid.encode("utf-8") in timers:
            RedisCache(self.config).update_timer_cache(message.from_jid, message.group_jid)


class Verification:
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
                RemoteAdmin(self).send_message(chat_message,
                                               "Give only a number after command\n Example: " + prefix + "verification time 5")

        elif prefix + "verify days " in s:
            try:
                d = int(s.split(prefix + "verify days ")[1])
                FeatureStatus(self).set_feature_setting(chat_message, "verification_days", d)
            except Exception as e:
                print(e)
                RemoteAdmin(self).send_message(chat_message,
                                               "Give only a number after command\n Example: " + prefix + "verify days 10")

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
                            MessageProcessing(self).process_message_media("welcome_message",
                                                                          group_messages["welcome_message"], peer_jid,
                                                                          group_jid)
                    RedisCache(self.config).update_join_queue_user("verified", 1, peer_jid, self.bot_id)
                elif correct == 0:
                    verification_wrong_message = group_messages["verification_wrong_message"]
                    if verification_wrong_message:
                        vwrong_message = process_message(self.config, "join", verification_wrong_message,
                                                         peer_jid, peer_info['group_jid'],
                                                         self.bot_id, "0")
                        self.client.send_chat_message(group_jid, vwrong_message)


class Silent:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()

        if s == prefix + "silent":  # admin
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings["silent-join_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "silent-join_status")

        elif s[:15] == prefix + "silent message":
            silent_msg = chat_message.body[16:]
            FeatureStatus(self).set_feature_message(chat_message, "silent-join_message", silent_msg)

        elif prefix + "silent time " in s:
            try:
                ti = float(s.split(prefix + "silent time ")[1]) * 60
                FeatureStatus(self).set_feature_setting(chat_message, "silent-join_time", ti)
            except Exception:
                RemoteAdmin(self).send_message(chat_message,
                                               f'Use a number after command. Example: {prefix}silent time 5')

        elif s == prefix + "silent status":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            group_messages = group_data["group_messages"]
            silent_status = group_settings["silent-join_status"]
            silent_message = group_messages["silent-join_message"]
            silent_time = group_settings["silent-join_time"]
            if silent_time >= 60:
                s_time = silent_time / 60
                units = "min."
            else:
                s_time = silent_time
                units = "sec."
            if silent_status == 1:
                status_string = "Silent Joiner Status: On \n"
                status_string += "Silent Joiner Time: " + str(round(s_time)) + " " + units + "\n"
                if silent_message != "none":
                    status_string += "Silent Joiner Message: " + silent_message + "\n"
                else:
                    status_string += "Silent Joiner message: None\n"

            else:
                status_string = "Silent Joiner Status: Off\n"
            RemoteAdmin(self).send_message(chat_message, status_string)
        else:
            return

    def silent_timeout(self, peer_jid, group_jid, bot_id):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_settings = group_data["group_settings"]
        group_messages = group_data["group_messages"]
        time.sleep(group_settings["silent-join_time"])
        user_info = RedisCache(self.config).get_single_join_queue(peer_jid, bot_id)
        if user_info is not None and int(user_info["timeout"]) == 0:
            timeout_msg = group_messages["silent-join_message"]
            self.client.send_chat_message(group_jid, timeout_msg)
            self.client.remove_peer_from_group(group_jid, peer_jid)
            User(self).group_user_remove(peer_jid, group_jid)
        else:
            RedisCache(self).remove_from_join_queue(peer_jid, bot_id)


class Profile:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()

        if s == prefix + "pfp":  # admin
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings["profile_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "profile_status")

        elif s[:12] == prefix + "pfp message":
            pfp_msg = chat_message.body[13:]
            FeatureStatus(self).set_feature_message(chat_message, "profile_message", pfp_msg)

        elif s == prefix + "pfp status":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            group_messages = group_data["group_messages"]
            profile_status = group_settings["profile_status"]
            profile_message = group_messages["profile_message"]
            if profile_status == 1:
                status_string = "Default pfp Status: On\n"
                if profile_message != "none":
                    status_string += "Default pfp Message: " + profile_message + "\n"
                else:
                    status_string += "Default pfp message: None\n"
            else:
                status_string = "Default pfp Status: Off\n"

            RemoteAdmin(self).send_message(chat_message, status_string)
        else:
            return


class BotHelpers:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()

        if s == prefix + "helper":  # admin
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings["bot-helper_status"] == 1:
                status = 0
            else:
                status = 1

            FeatureStatus(self).set_feature_status(chat_message, status, "bot-helper_status")

        elif s == prefix + "helper status":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings:
                if group_settings["bot-helper_status"] == 1:
                    status_message = "Bot Helper Status: On"
                else:
                    status_message = "Bot Helper Status: Off"
                RemoteAdmin(self).send_message(chat_message, status_message)


class BotSFW:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()

        if s == prefix + "sfw":  # admin
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings["sfw_status"] == 1:
                status = 0
            else:
                status = 1

            FeatureStatus(self).set_feature_status(chat_message, status, "sfw_status")

        elif s == prefix + "sfw status":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings:
                if group_settings["sfw_status"] == 1:
                    status_message = "Safe For Work Mode: On"
                else:
                    status_message = "Safe For Work Mode: Off"
                RemoteAdmin(self).send_message(chat_message, status_message)


class Forward:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()

        if s == prefix + "bypass":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings["media-forward_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "media-forward_status")
        elif s == prefix + "forward":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            group_members = group_data["group_members"]
            if not group_settings:
                return
            if group_settings["media-forward_status"] == 1:

                if group_members:
                    if chat_message.from_jid in group_members:
                        if "jid" in group_members[chat_message.from_jid]:
                            if group_members[chat_message.from_jid]["jid"] != "Unknown":

                                RedisCache(self.config).add_to_media_forward_queue(
                                    group_members[chat_message.from_jid]["jid"],
                                    chat_message.group_jid, self.bot_id)
                                Thread(target=media_forward_timeout,
                                       args=(self.config, self.client, group_members[chat_message.from_jid]["jid"],
                                             chat_message.group_jid, self.bot_id)).start()
                            else:
                                RemoteAdmin(self).send_message(chat_message,
                                                               "PM is unavailable, please open a PM with me and rejoin group.")
            else:
                RemoteAdmin(self).send_message(chat_message, "Media Forward Disabled")

        elif s == prefix + "bypass status":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            grab_status = group_settings["media-forward_status"]

            if grab_status == 1:
                status_string = "Media Forward Status: On\n"
            else:
                status_string = "Media Forward Status: Off\n"

            RemoteAdmin(self).send_message(chat_message, status_string)


class Censor:
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

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_settings = group_data["group_settings"]
        s = chat_message.body.lower()
        if prefix + "censor time" in s:
            try:
                ti = float(s.split(prefix + "censor time ")[1]) * 60
                FeatureStatus(self).set_feature_setting(chat_message, "censor_time", ti)
            except Exception:
                RemoteAdmin(self).send_message(chat_message,
                                               f'give only a number after command\n Example: {prefix}censor time 5')

        elif s == prefix + "censor list":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
            group_admins = group_data["group_admins"]
            all_admins = {**bot_admins, **group_admins}
            if chat_message.from_jid in all_admins:
                group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
                censor_words = group_data["censor_words"]
                if censor_words:
                    censor_list = "Censored Words: \n"
                    length = len(censor_words)
                    count = 0
                    for w in censor_words:
                        count += 1
                        if length == 1:
                            censor_list += str(" " + w)
                        elif count == length:
                            censor_list += str(" " + w)
                        else:
                            censor_list += str(" " + w + " /")
                    RemoteAdmin(self).send_message(chat_message, censor_list)
                else:
                    censor_list = "Censored Words: "
                    RemoteAdmin(self).send_message(chat_message, censor_list)
            else:
                RemoteAdmin(self).send_message(chat_message, "Must be an admin to use " + s)

        elif s[:12] == prefix + "censor warn":
            verification_msg = chat_message.body[13:]
            FeatureStatus(self).set_feature_message(chat_message, "censor-warn_message", verification_msg)

        elif s[:12] == prefix + "censor kick":
            verification_phrase = chat_message.body[13:].lower()
            FeatureStatus(self).set_feature_message(chat_message, "censor-kick_message", verification_phrase)

        elif s == prefix + "censor":
            if group_settings["censor_status"] >= 1:
                status = 0
            else:
                status = 1

            FeatureStatus(self).set_feature_status(chat_message, status, "censor_status")

        elif prefix + "cmode " in s:
            try:
                mode = int(chat_message.body.split(prefix + "cmode ")[1])
            except Exception as e:
                self.client.send_chat_message(chat_message.group_jid, "Shut up Smithers: " + str(e))
                return

            FeatureStatus(self).set_censor_status(chat_message, mode, "censor_status")

        elif s == prefix + "censor status":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            group_messages = group_data["group_messages"]

            censor_status = group_settings["censor_status"]
            censor_time = group_settings["censor_time"]
            censor_warn = group_messages["censor-warn_message"]
            censor_kick = group_messages["censor-kick_message"]

            c_time, c_units = convert_time(censor_time)
            if censor_status == 1:  # Mode 1 Matches entire message
                status_message = "Censor Status: Message Mode\n"
                status_message += "Warn Time: " + str(c_time) + " " + str(c_units)
                status_message += "Warn Message: " + censor_warn + "\n"
                status_message += "Kick Message: " + censor_kick + "\n"

            elif censor_status == 2:  # Mode 2 Searches message for word match.
                status_message = "Censor Status: Search Mode\n"
                status_message += "Warn Time: " + str(c_time) + " " + str(c_units)
                status_message += "Warn Message: " + censor_warn + "\n"
                status_message += "Kick Message: " + censor_kick + "\n"
            else:
                status_message = "Censor Status: Off"

            RemoteAdmin(self).send_message(chat_message, status_message)

        elif s == prefix + "censor":
            if group_settings["censor_status"] >= 1:
                status = 0
            else:
                status = 1

            FeatureStatus(self).set_feature_status(chat_message, status, "censor_status")

        elif prefix + "censor " in s:
            word = s[8:]
            Censor(self).add_censor_word(word, chat_message)
        elif "-censor " in s:
            word = s[8:]
            Censor(self).remove_censor_word(word, chat_message)

        else:
            return

    def add_censor_word(self, word, chat_message):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        group_admins = group_data["group_admins"]
        all_admins = {**bot_admins, **group_admins}
        if chat_message.from_jid in all_admins:
            current_words = RedisCache(self.config).get_single_group_data("json", "censor_words",
                                                                          chat_message.group_jid)
            if current_words:
                if word not in current_words:
                    length = len(current_words)
                    current_words[word] = length + 1
                    Database(self.config).update_group_data("json", "censor_words", current_words,
                                                            chat_message.group_jid)
                    RemoteAdmin(self).send_message(chat_message, f'Added {word} to censor list.')
            else:
                current_words = {}
                current_words[word] = 1
                Database(self.config).update_group_data("list", "censor_words", current_words, chat_message.group_jid)
                RemoteAdmin(self).send_message(chat_message, f'Added {word} to censor list.')

        else:
            RemoteAdmin(self).send_message(chat_message, f'Only admins can use {chat_message.body[7:]}')

    def remove_censor_word(self, word, chat_message):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        group_admins = group_data["group_admins"]
        all_admins = {**bot_admins, **group_admins}
        if chat_message.from_jid in all_admins:
            current_words = RedisCache(self.config).get_single_group_data("json", "censor_words",
                                                                          chat_message.group_jid)
            if current_words:
                if word in current_words:
                    del current_words[word]
                    Database(self.config).update_group_data("json", "censor_words", current_words,
                                                            chat_message.group_jid)
                    RemoteAdmin(self).send_message(chat_message, f'Removed {word} to censor list.')
        else:
            RemoteAdmin(self).send_message(chat_message, f'Only admins can use {chat_message.body[7:]}')


class Purge:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()
        if s[:14] == prefix + "purge message":  # admin
            purge_msg = chat_message.body[15:]
            FeatureStatus(self).set_feature_message(chat_message, "purge_message", purge_msg)

        elif prefix + "purge status" in s:  # admin
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_messages = group_data["group_messages"]
            if group_messages:
                if group_messages["purge_message"] != 'none':
                    status_response = 'Purge Message: \n'
                    final = process_message(self.config, "group", group_messages["purge_message"],
                                            chat_message.from_jid,
                                            chat_message.group_jid, self.bot_id, "245")
                    status_response += final
                else:
                    status_response = 'Purge Message: Off'

                RemoteAdmin(self).send_message(chat_message, status_response)

        elif prefix + "purge " in s:
            cooldown = RedisCache(self.config).get_from_group_cooldown("purge", chat_message.group_jid)
            now = time.time()
            a = float(now) - float(cooldown)
            if a > 300 or cooldown == 0:
                count = int(s.split(prefix + "purge ")[1])
                group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
                bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
                group_admins = group_data["group_admins"]
                all_admins = {**bot_admins, **group_admins}
                if count <= 5:
                    if chat_message.from_jid in all_admins:
                        Purge(self).purge_inactive(chat_message, count)
                    else:
                        RemoteAdmin(self).send_message(chat_message, f'Only admins can use {prefix}purge {count}.')
                elif count > 5 and chat_message.from_jid in bot_admins:
                    Purge(self).purge_inactive(chat_message, count)
                else:
                    RemoteAdmin(self).send_message(chat_message, f'You can only purge 5 or less members at a time.')
            else:
                t_left, t_units = convert_time(300 - a)
                RemoteAdmin(self).send_message(chat_message,
                                               f'You must wait {str(round(t_left))} {t_units} to purge again.')

        else:
            RemoteAdmin(self).send_message(chat_message, "Invalid Option for Purge")

    def purge_inactive(self, chat_message, count):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_admins = group_data["group_admins"]
        members = group_data["group_members"]
        group_messages = group_data["group_messages"]
        talkers = RedisCache(self.config).get_all_talker_lurkers("talkers", chat_message.group_jid)
        exempt = []
        old_users = []
        for l in talkers:
            if l in group_admins:
                exempt.append(l)
            if l not in members:
                old_users.append(l)
            elif l in members:
                if members[l]["cap_whitelist"] == 1:
                    exempt.append(l)

        for u in exempt:
            if u in talkers:
                del talkers[u]

        for u in old_users:
            if u in talkers:
                del talkers[u]

        sort_talkers = {k: v for k, v in sorted(talkers.items(), key=lambda item: item[1], reverse=True)}
        length = len(sort_talkers) - count
        if length < 0:
            RemoteAdmin(self).send_message(chat_message, f'I can\'t do that! There aren\'t enough members to purge!')
        else:
            if group_messages:
                if group_messages["purge_message"] != 'none':
                    final = process_message(self.config, "group", group_messages["purge_message"],
                                            chat_message.from_jid,
                                            chat_message.group_jid, self.bot_id, "245")
                    RemoteAdmin(self).send_message(chat_message, final)
            while count > 0:
                oldest = len(sort_talkers) - count
                oldest_jid = list(sort_talkers)[oldest]
                # RemoteAdmin(self.client).send_message(chat_message,
                #                                      "Would have removed " + members[oldest_jid]["display_name"])
                # print(Fore.RED + "Removing User From Group, Cache and Database" + Style.RESET_ALL)
                User(self).group_user_remove(oldest_jid, chat_message.group_jid)
                self.client.remove_peer_from_group(chat_message.group_jid, oldest_jid)
                count -= 1
                time.sleep(1)

            RedisCache(self.config).add_to_group_cooldown("purge", chat_message.group_jid)


class Whitelist:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()
        if s[:11] == prefix + "whitelist ":
            Whitelist(self).add_to_whitelist(chat_message, prefix)

        elif s[:11] == "-whitelist ":
            Whitelist(self).remove_from_whitelist(chat_message)

        elif s[:10] == prefix + "whitelist":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            members = group_data["group_members"]
            whitelist_message_1 = str("++++++ User Whitelist ++++++\n")
            whitelist_message_1 += str("ID        Member\n")
            whitelist_message_1 += str("++++++++++++++++++++++++\n")
            whitelist_message_2 = str("+++++ User Whitelist 2 +++++\n")
            whitelist_message_2 += str("++++++++++++++++++++++++\n")
            whitelist_message_2 += str("ID        Member\n")
            count = 0
            for m in members:
                if members[m]["cap_whitelist"] == 1:
                    count += 1
                    if len(str(members[m]["uid"])) > 1:
                        uid = str(members[m]["uid"]) + "       "
                    elif len(str(members[m]["uid"])) == 2:
                        uid = str(members[m]["uid"]) + "      "
                    else:
                        uid = str(members[m]["uid"]) + "     "
                    if count <= 50:
                        whitelist_message_1 += uid + members[m]["display_name"][:10] + "\n"
                    else:
                        whitelist_message_2 += uid + members[m]["display_name"][:10] + "\n"

            if count <= 50:
                RemoteAdmin(self).send_message(chat_message, whitelist_message_1)
            elif count > 50:
                RemoteAdmin(self).send_message(chat_message, whitelist_message_1)
                RemoteAdmin(self).send_message(chat_message, whitelist_message_2)

    def add_to_whitelist(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        group_admins = group_data["group_admins"]
        members = group_data["group_members"]
        all_admins = {**bot_admins, **group_admins}

        if chat_message.from_jid in all_admins:
            s = chat_message.body.lower()
            try:
                user_uid = int(s[11:])
            except TypeError:
                RemoteAdmin(self).send_message(chat_message,
                                               f'give only a number after command\n Example: {prefix}whitelist 23')
                return
            selected_member = False
            for m in members:
                if members[m]["uid"] == user_uid:
                    selected_member = m
                    members[m]["cap_whitelist"] = 1

            if selected_member:
                Database(self.config).update_group_data("json", "group_members", members, chat_message.group_jid)
                status_message = f'Added {members[selected_member]["display_name"]} to whitelist.'
            else:
                status_message = f'Can\'t find user with id {user_uid}.'

            RemoteAdmin(self).send_message(chat_message, status_message)

        else:
            status_message = f'Only admins can use {prefix}whitelist.'
            RemoteAdmin(self).send_message(chat_message, status_message)

    def remove_from_whitelist(self, chat_message):
        s = chat_message.body.lower()
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        group_admins = group_data["group_admins"]
        members = group_data["group_members"]
        all_admins = {**bot_admins, **group_admins}
        if chat_message.from_jid in all_admins:
            try:
                user_uid = int(s[11:])
            except TypeError:
                RemoteAdmin(self).send_message(chat_message,
                                               f'give only a number after command\n Example: -whitelist 23')
                return
            selected_member = False
            for m in members:
                if members[m]["uid"] == user_uid:
                    selected_member = m
                    members[m]["cap_whitelist"] = 0

            if selected_member:
                Database(self.config).update_group_data("json", "group_members", members, chat_message.group_jid)
                status_message = f'Removed {members[selected_member]["display_name"]} from whitelist.'
            else:
                status_message = f'Can\'t find user with id {user_uid}.'
            RemoteAdmin(self).send_message(chat_message, status_message)
        else:
            status_message = f'Only admins can use -whitelist.'
            RemoteAdmin(self).send_message(chat_message, status_message)


class UserCap:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()

        if s == prefix + "cap":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings["cap_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "cap_status")

        elif prefix + "cap users " in s:
            try:
                u = int(s[11:])
                FeatureStatus(self).set_feature_setting(chat_message, "cap_users", u)
            except Exception as e:
                RemoteAdmin(self).send_message(chat_message,
                                               f'give only a number after command\n Example: {prefix}cap users 97')

        elif s[:12] == prefix + "cap message":
            cap_msg = chat_message.body[13:]
            FeatureStatus(self).set_feature_message(chat_message, "cap_message", cap_msg)

        elif s == prefix + "cap status":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_messages = group_data["group_messages"]
            group_settings = group_data["group_settings"]
            cap_status = group_settings["cap_status"]
            cap_message = group_messages["cap_message"]
            cap_users = group_settings["cap_users"]

            if cap_status == 1:
                status_string = "Group User Cap Status: On\n"
                status_string += "Max Users: " + str(cap_users) + "\n"
                if cap_message != "none":
                    status_string += "Group User Cap Message: " + cap_message + "\n"
                else:
                    status_string += "Group User Cap message: None \n"
            else:
                status_string = "Group User Cap Status: Off\n"

            RemoteAdmin(self).send_message(chat_message, status_string)

    def remove_last_active(self, chat_message):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_admins = group_data["group_admins"]
        group_members = group_data["group_members"]
        group_messages = group_data["group_messages"]
        group_settings = group_data["group_settings"]

        if len(chat_message.group.members) + 1 <= group_settings["cap_users"]:
            return
        else:
            talkers = RedisCache(self.config).get_all_talker_lurkers("talkers", chat_message.group_jid)
            exempt = []
            old_users = []
            for l in talkers:
                if l in group_admins:
                    exempt.append(l)
                if l not in group_members:
                    old_users.append(l)
                elif l in group_members:
                    if group_members[l]["cap_whitelist"] == 1:
                        exempt.append(l)

            for u in exempt:
                if u in talkers:
                    del talkers[u]

            for u in old_users:
                if u in talkers:
                    del talkers[u]

            if chat_message.status_jid in talkers:
                del talkers[chat_message.status_jid]

            sort_talkers = {k: v for k, v in sorted(talkers.items(), key=lambda item: item[1], reverse=True)}
            length = len(sort_talkers)

            if length < 1:
                return
            else:
                oldest_jid = list(sort_talkers)[length - 1]
                if group_messages["cap_message"].lower() != "none":
                    cap_message = process_message(self.config, "group", group_messages["cap_message"],
                                                  oldest_jid, chat_message.group_jid, self.bot_id, "0")
                    self.client.send_chat_message(chat_message.group_jid, cap_message)
                # RemoteAdmin(self.client).send_message(chat_message,
                #                                      "Would have removed " + members[oldest_jid]["display_name"])
                # print(Fore.RED + "Removing User From Group, Cache and Database" + Style.RESET_ALL)
                User(self).group_user_remove(oldest_jid, chat_message.group_jid)
                self.client.remove_peer_from_group(chat_message.group_jid, oldest_jid)


class BackupRestore:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()
        if s == prefix + "backup":
            BackupRestore(self).backup(chat_message)
        elif s == prefix + "restore":
            BackupRestore(self).restore(chat_message)
        else:
            RemoteAdmin(self).send_message(chat_message, "Invalid Backup/Restore Option")

    def backup(self, chat_message):
        result = Database(self.config).backup_group_database(chat_message.from_jid, chat_message.group_jid, self.bot_id)
        if result == 1:
            RemoteAdmin(self).send_message(chat_message, "Backup Complete.")
        else:
            RemoteAdmin(self).send_message(chat_message, f'Only admins can use {chat_message.body}.')

    def restore(self, chat_message):
        result = Database(self.config).restore_group_database(chat_message.from_jid, chat_message.group_jid,
                                                              self.bot_id)
        if result == 1:
            RemoteAdmin(self).send_message(chat_message, "Restore Complete")
        else:
            RemoteAdmin(self).send_message(chat_message, f'Only admins can use {chat_message.body}.')


class DataTransfer:
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

    def main(self, message, prefix, message_source):
        s = message.body.lower()
        if s[:10] == prefix + "transfer ":
            hashes = s.split(prefix + "transfer ")[1]
            source_hash = hashes.split(" ")[0]
            destination_hash = hashes.split(" ")[1]
            result, destination_gjid = Database(self.config).transfer_group_database(source_hash, destination_hash,
                                                                                     message.from_jid, message_source,
                                                                                     self.bot_id)
            if result == 1:
                if message_source == "gm":
                    RemoteAdmin(self).send_message(message,
                                                   f'Transfer Complete: \nFrom: {source_hash} To: {destination_hash}')
                else:
                    self.client.send_chat_message(message.from_jid,
                                                  f'Transfer Complete: \nFrom: {source_hash} To: {destination_hash}')
                self.client.send_chat_message(destination_gjid, "Remote Data Transfer Complete.")
            elif result == 2:
                if message_source == "gm":
                    RemoteAdmin(self).send_message(message,
                                                   f'Error: {str(result)} \nMust be admin in source group. {source_hash}')
                else:
                    self.client.send_chat_message(message.from_jid,
                                                  f'Error: {str(result)} \nMust be admin in source group. {source_hash}')
            elif result == 3:
                if message_source == "gm":
                    RemoteAdmin(self).send_message(message,
                                                   f'Error: {str(result)} \nMust be admin in destination group. {destination_hash}')
                else:
                    self.client.send_chat_message(message.from_jid,
                                                  f'Error: {str(result)} \nMust be admin in destination group. {destination_hash}')
            elif result == 4:
                if message_source == "gm":
                    RemoteAdmin(self).send_message(message, f'Error: {str(result)} \nTransfer Data Corrupt')
                else:
                    self.client.send_chat_message(message.from_jid, f'Error: {str(result)} \nTransfer Data Corrupt')
            elif result == 5:
                if message_source == "gm":
                    RemoteAdmin(self).send_message(message,
                                                   f'Error: {str(result)} \nSource group not found, check for correct hash. {source_hash}')
                else:
                    self.client.send_chat_message(message.from_jid,
                                                  f'Error: {str(result)} \nSource group not found, check for correct hash. {source_hash}')
            elif result == 6:
                if message_source == "gm":
                    RemoteAdmin(self).send_message(message,
                                                   f'Error: {str(result)} \nDestination group not found, check for correct hash. {destination_hash}')
                else:
                    self.client.send_chat_message(message.from_jid,
                                                  f'Error: {str(result)} \nDestination group not found, check for correct hash. {destination_hash}')
            elif result == 7:
                if message_source == "gm":
                    RemoteAdmin(self).send_message(message,
                                                   f'Error: {str(result)} \nCan not get your user info from source group. {source_hash}')
                else:
                    self.client.send_chat_message(message.from_jid,
                                                  f'Error: {str(result)} \nCan not get your user info from source group. {source_hash}')
            elif result == 8:
                if message_source == "gm":
                    RemoteAdmin(self).send_message(message,
                                                   f'Error: {str(result)} \nCan not get your user info from destination group. {destination_hash}')
                else:
                    self.client.send_chat_message(message.from_jid,
                                                  f'Error: {str(result)} \nCan not get your user info from destination group. {destination_hash}')
            else:
                if message_source == "gm":
                    RemoteAdmin(self).send_message(message,
                                                   f'Error: {str(result)} \nUnknown Error.')
                else:
                    self.client.send_chat_message(message.from_jid,
                                                  f'Error: {str(result)} \nUnknown Error.')
        else:
            if message_source == "gm":
                RemoteAdmin(self).send_message(message, 'Invalid Transfer Option')
            else:
                self.client.send_chat_message(message.from_jid, 'Invalid Transfer Option')


class GroupStats:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()
        if s == prefix + "stats":
            GroupStats(self).get_group_stats(chat_message)

    def get_group_stats(self, chat_message):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_hash = group_data["group_hash"]
        group_name = group_data["group_name"]
        group_owner = group_data["group_owner"]
        group_admins = group_data["group_admins"]
        group_members = group_data["group_members"]
        group_history = group_data["history"]

        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        all_admins = {**bot_admins, **group_admins}
        if all_admins:
            if chat_message.from_jid in all_admins:
                talkers = RedisCache(self.config).get_all_talker_lurkers("talkers", chat_message.group_jid)
                sort_users = sorted(talkers.items(), key=lambda x: x[1], reverse=True)
                active_count = 0
                count = 0
                activity = 0
                for u in sort_users:
                    count += 1
                    if count == 1 and u[0] != chat_message.from_jid:
                        activity = u[1]
                    elif count == 2 and u[0] != chat_message.from_jid:
                        activity = u[1]
                    if time.time() - u[1] <= 86400:
                        active_count += 1
                last_activity = round(time.time() - activity)
                if last_activity >= 86400:
                    ctime = (last_activity // 86400)
                    if ctime == 1:
                        c_units = "day"
                    else:
                        c_units = "days"
                elif 86400 > last_activity >= 3600:
                    ctime = (last_activity // 36000)
                    if ctime == 1:
                        c_units = "hour"
                    else:
                        c_units = "hours"
                elif 3600 > last_activity >= 60:
                    ctime = (last_activity // 60)
                    if ctime == 1:
                        c_units = "minute"
                    else:
                        c_units = "minutes"
                elif 60 > last_activity > 0:
                    ctime = last_activity
                    if ctime == 1:
                        c_units = "second"
                    else:
                        c_units = "seconds"
                if os.path.exists(self.config["paths"]["backup"] + chat_message.group_jid + "/database.json"):
                    last_backup = round(time.time() - os.path.getmtime(
                        self.config["paths"]["backup"] + chat_message.group_jid + "/database.json"))
                    if last_backup >= 86400:
                        btime = (last_backup // 86400)
                        if btime == 1:
                            b_units = "day"
                        else:
                            b_units = "days"
                    elif 86400 > last_backup >= 3600:
                        btime = (last_backup // 36000)
                        if btime == 1:
                            b_units = "hour"
                        else:
                            b_units = "hours"
                    elif 3600 > last_backup >= 60:
                        btime = (last_backup // 60)
                        if btime == 1:
                            b_units = "minute"
                        else:
                            b_units = "minutes"
                    elif 60 > last_backup > 0:
                        btime = last_backup
                        if btime == 1:
                            b_units = "second"
                        else:
                            b_units = "seconds"
                else:
                    btime = "None"
                    b_units = "None"

                group_activity = {"message": 0, "image": 0, "gif": 0, "video": 0}
                for ac in group_history:
                    group_activity["message"] += group_history[ac]["message"]
                    group_activity["image"] += group_history[ac]["image"]
                    group_activity["gif"] += group_history[ac]["gif"]
                    group_activity["video"] += group_history[ac]["video"]

                stats_response = f"++ {group_name} ++\n"
                stats_response += f"Hash: {group_hash}\n"
                stats_response += f'Last Backup: {str(round(btime)) + " " + b_units + " ago." if btime != "None" else btime}\n'
                for o in group_owner:
                    stats_response += "Owner: " + group_members[o]["display_name"] + "\n"
                stats_response += "Admins: " + str(len(group_admins)) + "\n"
                stats_response += "Members: " + str(len(group_members)) + "\n"
                stats_response += str("                           \n")
                stats_response += "++++ Activity Stats ++++\n"
                stats_response += "Last Activity: " + str(round(ctime)) + " " + c_units + " ago.\n"
                stats_response += "Active Users: " + str(active_count) + "/" + str(
                    len(group_members)) + " last 24 hrs.\n"
                stats_response += "Chat Messages: " + str(group_activity["message"]) + "\n"
                stats_response += "Chat Images: " + str(group_activity["image"]) + "\n"
                stats_response += "Chat GIFs: " + str(group_activity["gif"]) + "\n"
                stats_response += "Chat Video: " + str(group_activity["video"]) + "\n"
                stats_response += str("                           \n")
                stats_response += "++++ Protected By ++++\n"
                stats_response += "Lucky 🍀 bot number " + str(self.bot_id)
                RemoteAdmin(self).send_message(chat_message, stats_response)
            else:
                RemoteAdmin(self).send_message(chat_message, f"Only Admins can use {chat_message.body}")


class BotStatus:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()
        if s == prefix + "status":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_admins = group_data["group_admins"]
            group_settings = group_data["group_settings"]
            bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
            all_admins = {**bot_admins, **group_admins}
            if chat_message.from_jid in all_admins:
                settings_message = "++ Settings for: $gh ++\n"
                on = "🟢"
                off = "🔴"

                for status in group_settings:
                    if "users" in status or "language" in status or "time" in status or "days" in status or "max" in status or "confessions" in status or "casino" in status or "jackpot" in status:
                        continue
                    if "-" in status:
                        feature_name = status.split('-')[0].capitalize() + " " + status.split('-')[1].split('_')[
                            0].capitalize()
                        feature_type = status.split("_")[1].capitalize()
                    else:
                        feature_name = str(status.split("_")[0]).capitalize()
                        feature_type = status.split("_")[1].capitalize()

                    if group_settings[status] > 0:
                        if status == "trigger_status":
                            if group_settings[status] == 1:
                                settings_message += on + " " + feature_name + ": Normal Mode\n"
                            elif group_settings[status] == 2:
                                settings_message += on + " " + feature_name + ": Mixed Mode\n"
                            elif group_settings[status] == 3:
                                settings_message += on + " " + feature_name + ": Admin Mode\n"
                        elif status == "censor_status":
                            if group_settings[status] == 1:
                                settings_message += on + " " + feature_name + ": Message Mode\n"
                            elif group_settings[status] == 2:
                                settings_message += on + " " + feature_name + ": Search Mode\n"
                        else:
                            settings_message += on + " " + feature_name + "\n"
                    else:
                        settings_message += off + " " + feature_name + " " + feature_type + "\n"

                final = process_message(self.config, "group", settings_message, chat_message.from_jid,
                                        chat_message.group_jid, self.bot_id, "0")
                RemoteAdmin(self).send_message(chat_message, final)
            else:
                RemoteAdmin(self).send_message(chat_message, f"Only Admins can use {chat_message.body}")
