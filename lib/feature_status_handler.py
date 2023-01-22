# Python 3 Core Libraries


# Python 3 Third Party Libraries

# Python 3 Project Libraries
import os
import re

from colorama import Style, Fore

from lib.database_handler import Database
from lib.remote_admin_handler import RemoteAdmin


class FeatureStatus:
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

    def set_feature_status(self, chat_message, status, feature):
        exit_code = Database(self.config).change_feature_status(status, feature, chat_message.group_jid,
                                                                chat_message.from_jid, self.bot_id)

        if "-" in feature:
            feature_name = feature.split('-')[0].capitalize() + " " + feature.split('-')[1].split('_')[0].capitalize()
            feature_type = feature.split("_")[1].capitalize()
        else:
            feature_name = str(feature.split("_")[0]).capitalize()
            feature_type = feature.split("_")[1].capitalize()

        if status == 0:
            RemoteAdmin(self).send_message(chat_message,
                                                  feature_name + ": Off" if exit_code == 1
                                                  else feature_name + " " + feature_type +
                                                       " can only be changed by admin!" if exit_code == 3
                                                  else feature_name + ": is already off.")
        else:
            RemoteAdmin(self).send_message(chat_message,
                                                  feature_name + ": On" if exit_code == 1
                                                  else feature_name + " " + feature_type +
                                                       " can only be changed by admin!" if exit_code == 3
                                                  else feature_name + ": is already off.")

    def set_feature_message(self, chat_message, setting, value):
        current_dir = os.getcwd() + "/"
        # remove \ from messages if they are in there. They do not convert to or from json correctly
        exit_code = Database(self.config).change_feature_message(setting, value, chat_message.group_jid,
                                                                 chat_message.from_jid, self.bot_id)
        if "-" in setting:
            feature_name = setting.split('-')[0].capitalize() + " " + setting.split('-')[1].split('_')[
                0].capitalize() + " " + \
                           setting.split("_")[1].capitalize()
        else:
            feature_name = str(setting.split("_")[0]).capitalize() + " " + str(setting.split("_")[1]).capitalize()

        if current_dir in value and value[-4:] == "json":
            value = "gif"
        elif current_dir in value and value[-3:] == "png" or value[-3:] == "jpg":
            value = "Image"
        elif current_dir in value and value[-3:] == "mp4":
            value = "Video"

        RemoteAdmin(self).send_message(chat_message,
                                              feature_name + " set to:\n {}".format(value) if exit_code == 1
                                              else feature_name +
                                                   " can only be changed by admin.")

    def set_feature_setting(self, chat_message, setting, value):
        exit_code = Database(self.config).change_feature_setting(setting, value, chat_message.from_jid, chat_message.group_jid,
                                                      self.bot_id)
        if "days" in setting:
            units = " days."
        elif "time" in setting:
            if value > 60:
                value = value / 60
                units = " minutes."
            else:
                units = " seconds."
        elif "max" in setting:
            units = " bans."
        else:
            units = "."

        if "-" in setting:
            feature_name = setting.split('-')[0].capitalize() + " " + setting.split('-')[1].split('_')[
                0].capitalize() + " " + \
                           setting.split("_")[1].capitalize()
        else:
            feature_name = str(setting.split("_")[0]).capitalize() + " " + str(setting.split("_")[1]).capitalize()

        RemoteAdmin(self).send_message(chat_message,
                                              feature_name + " set to " +
                                              " {}".format(str(round(value))) + units if exit_code == 1
                                              else feature_name + " can only be set by admin")

    def set_trigger_status(self, chat_message, status, feature, group_jid, peer_jid):
        exit_code = Database(self.config).change_feature_status(status, feature, group_jid, peer_jid, self.bot_id)
        if status == 0:
            RemoteAdmin(self).send_message(chat_message,
                                                  str(feature.split("_")[0]).capitalize() + ": Off" if exit_code == 1
                                                  else str(feature.split("_")[0]).capitalize() + " " +
                                                       feature.split("_")[1] +
                                                       " can only be changed by admin." if exit_code == 3
                                                  else str(feature.split("_")[0]).capitalize() + " is already off")
        elif status == 1:
            RemoteAdmin(self).send_message(chat_message,
                                                  str(feature.split("_")[
                                                          0]).capitalize() + ": Normal Mode" if exit_code == 1
                                                  else str(feature.split("_")[0]).capitalize() + " " +
                                                       feature.split("_")[1] +
                                                       " can only be changed by admin." if exit_code == 3
                                                  else str(feature.split("_")[
                                                               0]).capitalize() + " Normal Mode already enabled")
        elif status == 2:
            RemoteAdmin(self).send_message(chat_message,
                                                  str(feature.split("_")[
                                                          0]).capitalize() + ": Mixed Mode" if exit_code == 1
                                                  else str(feature.split("_")[0]).capitalize() + " " +
                                                       feature.split("_")[1] +
                                                       " can only be changed by admin." if exit_code == 3
                                                  else str(feature.split("_")[
                                                               0]).capitalize() + " Mixed Mode already enabled")
        elif status == 3:
            RemoteAdmin(self).send_message(chat_message,
                                                  str(feature.split("_")[
                                                          0]).capitalize() + ": Admin Mode" if exit_code == 1
                                                  else str(feature.split("_")[0]).capitalize() + " " +
                                                       feature.split("_")[1] +
                                                       " can only be changed by admin." if exit_code == 3
                                                  else str(feature.split("_")[
                                                               0]).capitalize() + " Admin Mode already enabled")

    def set_censor_status(self, chat_message, status, feature):
        exit_code = Database(self.config).change_feature_status(status, feature, chat_message.group_jid, chat_message.from_jid, self.bot_id)
        if status == 0:
            RemoteAdmin(self).send_message(chat_message,
                                                  str(feature.split("_")[0]).capitalize() + ": Off" if exit_code == 1
                                                  else str(feature.split("_")[0]).capitalize() + " " +
                                                       feature.split("_")[1] +
                                                       " can only be changed by admin." if exit_code == 3
                                                  else str(feature.split("_")[0]).capitalize() + " is already off")
        elif status == 1:
            RemoteAdmin(self).send_message(chat_message,
                                                  str(feature.split("_")[
                                                          0]).capitalize() + ": Message Mode" if exit_code == 1
                                                  else str(feature.split("_")[0]).capitalize() + " " +
                                                       feature.split("_")[1] +
                                                       " can only be changed by admin." if exit_code == 3
                                                  else str(feature.split("_")[
                                                               0]).capitalize() + " Message Mode already enabled")
        elif status == 2:
            RemoteAdmin(self).send_message(chat_message,
                                                  str(feature.split("_")[
                                                          0]).capitalize() + ": Search Mode" if exit_code == 1
                                                  else str(feature.split("_")[0]).capitalize() + " " +
                                                       feature.split("_")[1] +
                                                       " can only be changed by admin." if exit_code == 3
                                                  else str(feature.split("_")[
                                                               0]).capitalize() + " Search Mode already enabled")
