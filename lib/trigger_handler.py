# Python 3 Core Libraries
import string
import random
import os
import re
import subprocess
import time
import json
import urllib.request
from threading import Thread
import uuid

# Python 3 Third Party Libraries
import cv2

# Python 3 Project Libraries
import requests

from lib.message_processing_handler import process_message
from lib.redis_handler import RedisCache
from lib.database_handler import Database
from lib.feature_status_handler import FeatureStatus
from lib.remote_admin_handler import RemoteAdmin


class Triggers:
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
        group_admins = group_data["group_admins"]
        admin_triggers = group_data["admin_triggers"]
        user_triggers = group_data["user_triggers"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        all_admins = {**bot_admins, **group_admins}
        sub_status = group_settings["trigger_status"]

        if s == prefix + "trigger":
            if group_settings["trigger_status"] >= 1:
                status = 0
            else:
                status = 2

            FeatureStatus(self).set_feature_status(chat_message, status, "trigger_status")

        elif prefix + "mode " in s:
            try:
                mode = int(chat_message.body.split(prefix + "mode ")[1])
            except Exception as e:
                self.client.send_chat_message(chat_message.group_jid, "Shut up Smithers: " + str(e))
                return

            FeatureStatus(self).set_trigger_status(chat_message, mode, "trigger_status", chat_message.group_jid,
                                                   chat_message.from_jid)

        elif s == prefix + "trigger status":

            if sub_status == 1:  # Mode 1 Everyone Can Add/Delete
                RemoteAdmin(self).send_message(chat_message, "Trigger Status: Normal Mode")
            elif sub_status == 2:  # Mode 1 Everyone Can Add/Delete
                RemoteAdmin(self).send_message(chat_message, "Trigger Status: Mixed Mode")
            elif sub_status == 3:  # Mode 1 Everyone Can Add/Delete
                RemoteAdmin(self).send_message(chat_message, "Trigger Status: Admin Mode")
            else:
                RemoteAdmin(self).send_message(chat_message, "Trigger Status: Off")

        elif s == prefix + "trigger list" and sub_status != 0:
            if sub_status > 1:

                if chat_message.from_jid not in all_admins:
                    return

            admin_list = ""
            user_list = ""

            for key in admin_triggers:
                admin_list += str(" " + key + " /")
            for key in user_triggers:
                user_list += str(" " + key + " /")

            RemoteAdmin(self).send_message(chat_message, "Triggers:" + user_list[:-1])
            RemoteAdmin(self).send_message(chat_message, "Admin Triggers: " + admin_list[:-1])

        elif s == prefix + "delete all":
            Triggers(self).delete_all_subs(chat_message, chat_message.group_jid, chat_message.from_jid)

        elif prefix + "trigger " in s and sub_status != 0:
            sub_list = ""
            merged_subs = {**user_triggers, **admin_triggers}
            sub_key = s.split(prefix + "trigger ")[1]

            if merged_subs.get(sub_key):
                for x in merged_subs[sub_key]:
                    if merged_subs[sub_key][x][-3:] == "png":
                        if merged_subs[sub_key][x][:1] == "[":
                            text = merged_subs[sub_key][x].split("] ")[0].split("[")[1]
                        else:
                            text = ""
                        sub_list += "[" + x + "]" + ": image " + text + "\n"

                    elif merged_subs[sub_key][x][-3:] == "jpg":
                        if merged_subs[sub_key][x][:1] == "[":
                            text = merged_subs[sub_key][x].split("] ")[0].split("[")[1]
                        else:
                            text = ""
                        sub_list += "[" + x + "]" + ": image " + text + "\n"
                    elif merged_subs[sub_key][x][-3:] == "mp4":
                        if merged_subs[sub_key][x][:1] == "[":
                            text = merged_subs[sub_key][x].split("] ")[0].split("[")[1]
                        else:
                            text = ""
                        sub_list += "[" + x + "]" + ": video " + text + "\n"
                    elif merged_subs[sub_key][x][-4:] == "json":
                        if merged_subs[sub_key][x][:1] == "[":
                            text = merged_subs[sub_key][x].split("] ")[0].split("[")[1]
                        else:
                            text = ""
                        sub_list += "[" + x + "]" + ": gif " + text + "\n"
                    else:
                        sub_list += "[" + x + "]" + ": " + merged_subs[sub_key][x] + " \n"
                RemoteAdmin(self).send_message(chat_message, "Responses for " + sub_key + " : \n" + sub_list)
            else:
                RemoteAdmin(self).send_message(chat_message, "Trigger not found.")

        elif prefix + "delete " in s and sub_status != 0:
            try:
                sub_key = s.split(prefix + "delete ")[1]

            except Exception as e:
                RemoteAdmin(self).send_message(chat_message, "Please give the sub to delete.")
                return
            Triggers(self).delete_substitution(chat_message, sub_key, chat_message.group_jid,
                                               chat_message.from_jid)

        elif " > " in chat_message.body and "\">\"" not in s and sub_status != 0:
            sub = [x.strip() for x in chat_message.body.split(" > ")]
            if sub[0].count(' ') > 4 or len(sub[0]) > 75:

                RemoteAdmin(self).send_message(chat_message,
                                               "Invalid Substitution:\n\nThe phrase being substituted can only be a "
                                               "maximum of 5 words and cannot be longer then 75 characters long!")
            else:
                if admin_triggers:
                    if sub[0].lower() in admin_triggers:
                        RemoteAdmin(self).send_message(chat_message,
                                                       sub[0] + " already exists as admin trigger.")
                        return

                if sub[0].split(" ")[0] == "all":
                    return

                if sub[1].split(" ")[0] == prefix + "trigger":
                    return

                if sub[1][:2] == "$i" or sub[1][:2] == "$g" or sub[1][:2] == "$v":

                    if sub[1][:3] == "$gs" or sub[1][:3] == "$gn" or sub[1][:3] == "$gh":
                        Triggers(self).add_substitution(chat_message, "set", "user_triggers", sub,
                                                        chat_message.group_jid,
                                                        chat_message.from_jid)
                        return
                    else:

                        RedisCache(self.config).add_to_media_sub_queue(sub[0], sub[1], "set", "user_triggers",
                                                                chat_message.from_jid,
                                                                chat_message.group_jid)
                        media_sub_timeout(self, chat_message, chat_message.from_jid, chat_message.group_jid)

                else:
                    Triggers(self).add_substitution(chat_message, "set", "user_triggers", sub,
                                                    chat_message.group_jid,
                                                    chat_message.from_jid)
        elif " >+ " in chat_message.body and "\">+\"" not in s and sub_status != 0:
            sub = [x.strip() for x in chat_message.body.split(" >+ ")]
            if sub[0].count(' ') > 4 or len(sub[0]) > 75:
                self.client.send_chat_message(chat_message.group_jid,
                                              "Invalid Substitution:\n\nThe phrase being substituted can only be a "
                                              "maximum of 5 words and cannot be longer then 75 characters long!"
                                              )  # has more than 1 word
            else:
                if user_triggers:
                    if sub[0].lower() not in user_triggers:
                        RemoteAdmin(self).send_message(chat_message,
                                                       sub[0] + " doesn't exist.")
                        return
                    if sub[0].split(" ")[0] == "all":
                        return

                    if sub[1].split(" ")[0] == prefix + "trigger":
                        return
                if sub[1][:2] == "$i" or sub[1][:2] == "$g" or sub[1][:2] == "$v":
                    if sub[1][:3] == "$gs" or sub[1][:3] == "$gn" or sub[1][:3] == "$gh":
                        Triggers(self).add_substitution(chat_message, "set", "user_triggers", sub,
                                                        chat_message.group_jid,
                                                        chat_message.from_jid)
                        return
                    else:
                        RedisCache(self.config).add_to_media_sub_queue(sub[0], sub[1], "add", "user_triggers",
                                                                       chat_message.from_jid,
                                                                       chat_message.group_jid)
                        media_sub_timeout(self, chat_message, chat_message.from_jid,
                                          chat_message.group_jid)
                else:
                    Triggers(self).add_substitution(chat_message, "add", "user_triggers", sub,
                                                    chat_message.group_jid,
                                                    chat_message.from_jid)

        elif " >- " in s and "\">-\"" not in s and sub_status != 0:
            try:
                sub_key = s.split(" >- ")[0]
                sub_number = s.split(" >- ")[1]
            except Exception as e:
                print(e)
                RemoteAdmin(self).send_message(chat_message, "Please give the sub to delete.")
                return
            Triggers(self).delete_sub_substitution(chat_message, sub_key, sub_number,
                                                   chat_message.group_jid,
                                                   chat_message.from_jid)

        elif " >> " in chat_message.body and "\">>\"" not in s and sub_status != 0:
            sub = [x.strip() for x in chat_message.body.split(" >> ")]
            if sub[0].count(' ') > 4 or len(sub[0]) > 75:
                RemoteAdmin(self).send_message(chat_message,
                                               "Invalid Substitution:\n\nThe phrase being substituted can only be a "
                                               "maximum of 5 words and cannot be longer then 75 characters long!"
                                               )  # has more than 1 word
            else:

                if sub[0].split(" ")[0] == "all":
                    return

                if sub[1].split(" ")[0] == prefix + "trigger":
                    return

                if sub[1][:2] == "$i" or sub[1][:2] == "$g" or sub[1][:2] == "$v":
                    if sub[1][:3] == "$gs" or sub[1][:3] == "$gn" or sub[1][:3] == "$gh":
                        Triggers(self).add_substitution(chat_message, "set", "admin_triggers", sub,
                                                        chat_message.group_jid,
                                                        chat_message.from_jid)
                        return
                    else:
                        RedisCache(self.config).add_to_media_sub_queue(sub[0], sub[1], "set", "admin_triggers",
                                                                       chat_message.from_jid,
                                                                       chat_message.group_jid)
                        media_sub_timeout(self, chat_message, chat_message.from_jid, chat_message.group_jid)
                else:
                    Triggers(self).add_substitution(chat_message, "set", "admin_triggers", sub,
                                                    chat_message.group_jid,
                                                    chat_message.from_jid)

        elif " >>+ " in chat_message.body and "\">>+\"" not in s and sub_status != 0:
            sub = [x.strip() for x in chat_message.body.split(" >>+ ")]
            if sub[0].count(' ') > 4 or len(sub[0]) > 75:
                RemoteAdmin(self).send_message(chat_message,
                                               "Invalid Substitution:\n\nThe phrase being substituted can only be a "
                                               "maximum of 5 words and cannot be longer then 75 characters long!"
                                               )  # has more than 1 word
            else:
                if admin_triggers:
                    if sub[0].lower() not in admin_triggers:
                        RemoteAdmin(self).send_message(chat_message,
                                                       sub[0] + " doesn't exist.")
                        return

            if sub[1][:2] == "$i" or sub[1][:2] == "$g" or sub[1][:2] == "$v":
                if sub[1][:3] == "$gs" or sub[1][:3] == "$gn" or sub[1][:3] == "$gh":
                    Triggers(self).add_substitution(chat_message, "set", "admin_triggers", sub,
                                                    chat_message.group_jid,
                                                    chat_message.from_jid)
                    return
                else:
                    RedisCache(self.config).add_to_media_sub_queue(sub[0], sub[1], "add", "admin_triggers",
                                                                   chat_message.from_jid,
                                                                   chat_message.group_jid)
                    media_sub_timeout(self.client, chat_message, chat_message.from_jid, chat_message.group_jid)
            else:
                Triggers(self).add_substitution(chat_message, "add", "admin_triggers", sub,
                                                chat_message.group_jid,
                                                chat_message.from_jid)

        elif " >>- " in s and "\">>-\"" not in s and sub_status != 0:
            try:
                sub_key = s.split(" >>- ")[0]
                sub_number = s.split(" >>- ")[1]
            except Exception as e:
                print(e)
                RemoteAdmin(self).send_message(chat_message, "Please give the sub to delete.")
                return
            Triggers(self).delete_sub_substitution(chat_message, sub_key, sub_number,
                                                   chat_message.group_jid,
                                                   chat_message.from_jid)

    def add_substitution(self, chat_message, action, sub_type, substitution, group_jid, peer_jid):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_messages = group_data["group_messages"]
        group_settings = group_data["group_settings"]
        group_admins = group_data["group_admins"]
        admin_triggers = group_data["admin_triggers"]
        user_triggers = group_data["user_triggers"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        all_admins = {**bot_admins, **group_admins}

        if not group_data:
            return
        sub_status = group_settings["trigger_status"]
        if sub_status == 0:  # Mode 0 Off
            return
        elif sub_status == 1:  # Mode 1 Normal
            if action == "set":
                result = Database(self.config).set_substitution(sub_type, substitution, group_jid, peer_jid,
                                                                self.bot_id)
            else:
                result = Database(self.config).update_substitution(sub_type, substitution, group_jid, peer_jid,
                                                                   self.bot_id)
            if result == 1 or result == 3:
                RemoteAdmin(self).send_message(chat_message, "Done")
            elif result == 4:
                RemoteAdmin(self).send_message(chat_message, "Already a trigger use >+ or >>+ to add responses.")
            elif result == 5:
                RemoteAdmin(self).send_message(chat_message, "Maximum responses reached. 40")
            else:
                RemoteAdmin(self).send_message(chat_message, "Only admins can add admin triggers.")
        elif sub_status == 2 or sub_status == 3:
            # Mode 2: Admin only Create User/Admin Trigger Mode 3: Admin Only Create/Trigger
            if peer_jid in all_admins:
                if action == "set":
                    result = Database(self.config).set_substitution(sub_type, substitution, group_jid, peer_jid,
                                                                    self.bot_id)
                else:
                    result = Database(self.config).update_substitution(sub_type, substitution, group_jid, peer_jid,
                                                                       self.bot_id)
                if result == 1 or result == 3:
                    RemoteAdmin(self).send_message(chat_message, "Done")
                elif result == 4:
                    RemoteAdmin(self).send_message(chat_message,
                                                   "Already a trigger use >+ or >>+ to add responses.")
                elif result == 5:
                    RemoteAdmin(self).send_message(chat_message, "Maximum responses reached. 40")
                else:
                    RemoteAdmin(self).send_message(chat_message, "Only admins can add triggers.")
            else:
                RemoteAdmin(self).send_message(chat_message, "Only admins can add triggers.")
        else:
            return

    def delete_all_subs(self, chat_message, group_jid, peer_jid):
        result = Database(self.config).delete_all_substitutions(group_jid, peer_jid, self.bot_id)
        if result == 1:
            RemoteAdmin(self).send_message(chat_message, "Deleted all substitutions")
        elif result == 2:
            RemoteAdmin(self).send_message(chat_message, "Only admins can delete all substitutions.")
        elif result == 3:
            RemoteAdmin(self).send_message(chat_message,
                                           "Group database uninitialized. Add a new member to the group to fix.")
        else:
            RemoteAdmin(self).send_message(chat_message, "If you got here you broke something horribly.")

    def delete_substitution(self, message, substitution, group_jid, peer_jid):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_messages = group_data["group_messages"]
        group_settings = group_data["group_settings"]
        group_admins = group_data["group_admins"]
        admin_triggers = group_data["admin_triggers"]
        user_triggers = group_data["user_triggers"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        all_admins = {**bot_admins, **group_admins}

        if not group_data:
            return
        sub_status = group_settings["trigger_status"]

        if sub_status == 1:  # Mode 1 Everyone Can Add/Delete
            for k in user_triggers:
                if k == substitution.lower():
                    result = Database(self.config).delete_substitution("user_triggers", k, group_jid, peer_jid,
                                                                       self.bot_id)
                    if result == 1 or result == 4:
                        RemoteAdmin(self).send_message(message, "Deleted: " + substitution)
                    elif result == 2:
                        RemoteAdmin(self).send_message(message, "Only admins can delete triggers.")

            for k in admin_triggers:
                if k == substitution.lower():
                    result = Database(self.config).delete_substitution("admin_triggers", k, group_jid, peer_jid,
                                                                       self.bot_id)
                    if result == 1 or result == 4:
                        RemoteAdmin(self).send_message(message, "Deleted: " + substitution)
                    elif result == 2:
                        RemoteAdmin(self).send_message(message, "Only admins can delete admin triggers.")

        elif sub_status == 2 or sub_status == 3:  # Mode 2/3 Only Admins Can Add/Delete
            if peer_jid not in all_admins:
                RemoteAdmin(self).send_message(message, "Only admins can delete admin triggers.")
                return
            for k in admin_triggers:
                if k == substitution.lower():
                    result = Database(self.config).delete_substitution("admin_triggers", k, group_jid, peer_jid,
                                                                       self.bot_id)
                    if result == 1 or result == 4:
                        RemoteAdmin(self).send_message(message, "Deleted: " + substitution)
                    elif result == 2:
                        RemoteAdmin(self).send_message(message, "Only admins can delete admin triggers.")
            for k in user_triggers:
                if k == substitution.lower():
                    result = Database(self.config).delete_substitution("user_triggers", k, group_jid, peer_jid,
                                                                       self.bot_id)
                    if result == 1 or result == 4:
                        RemoteAdmin(self).send_message(message, "Deleted: " + substitution)
                    elif result == 2:
                        RemoteAdmin(self).send_message(message, "Only admins can delete admin triggers.")

    def delete_sub_substitution(self, message, substitution, number, group_jid, peer_jid):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_messages = group_data["group_messages"]
        group_settings = group_data["group_settings"]
        group_admins = group_data["group_admins"]
        admin_triggers = group_data["admin_triggers"]
        user_triggers = group_data["user_triggers"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        all_admins = {**bot_admins, **group_admins}

        if not group_settings:
            return
        sub_status = group_settings["trigger_status"]

        if sub_status == 1:  # Mode 1 Everyone Can Add/Delete
            for k in user_triggers:
                if k == substitution.lower():
                    result = Database(self.config).delete_sub_substitution("user_triggers", k, number, group_jid,
                                                                           peer_jid,
                                                                           self.bot_id)
                    if result == 1 or result == 4:
                        if user_triggers[k][number][-3:] == "png" or user_triggers[k][number][-3:] == "jpg":
                            RemoteAdmin(self).send_message(message,
                                                           "Deleted: Response Image \n From: " + substitution)
                        elif user_triggers[k][number][-4:] == "json":
                            RemoteAdmin(self).send_message(message,
                                                           "Deleted: Response GIF \n From: " + substitution)
                        else:
                            RemoteAdmin(self).send_message(message, "Deleted: " + user_triggers[k][
                                number] + "\n From: " + substitution)


                    elif result == 2:
                        RemoteAdmin(self).send_message(message, "Only admins can delete triggers.")

            for k in admin_triggers:
                if k == substitution.lower():
                    result = Database(self.config).delete_sub_substitution("admin_triggers", k, number, group_jid,
                                                                           peer_jid,
                                                                           self.bot_id)
                    if result == 1 or result == 4:
                        if admin_triggers[k][number][-3:] == "png" or admin_triggers[k][number][-3:] == "jpg":
                            RemoteAdmin(self).send_message(message,
                                                           "Deleted: Response Image \n From: " + substitution)
                        elif admin_triggers[k][number][-4:] == "json":
                            RemoteAdmin(self).send_message(message,
                                                           "Deleted: Response GIF \n From: " + substitution)
                        else:
                            RemoteAdmin(self).send_message(message, "Deleted: " + admin_triggers[k][
                                number] + "\n From: " + substitution)
                    elif result == 2:
                        RemoteAdmin(self).send_message(message, "Only admins can delete admin triggers.")

        elif sub_status == 2 or sub_status == 3:  # Mode 2/3 Only Admins Can Add/Delete

            if peer_jid not in all_admins:
                RemoteAdmin(self).send_message(message, "Only admins can delete admin triggers.")
                return
            for k in admin_triggers:
                if k == substitution.lower():
                    result = Database(self.config).delete_sub_substitution("admin_triggers", k, number, group_jid,
                                                                           peer_jid,
                                                                           self.bot_id)
                    if result == 1 or result == 4:
                        if admin_triggers[k][number][-3:] == "png" or admin_triggers[k][number][-3:] == "jpg":
                            RemoteAdmin(self).send_message(message,
                                                           "Deleted: Response Image \n From: " + substitution)
                        elif admin_triggers[k][number][-4:] == "json":
                            RemoteAdmin(self).send_message(message,
                                                           "Deleted: Response GIF \n From: " + substitution)
                        else:
                            RemoteAdmin(self).send_message(message, "Deleted: " + admin_triggers[k][
                                number] + "\n From: " + substitution)
                    elif result == 2:
                        RemoteAdmin(self).send_message(message, "Only admins can delete admin triggers.")
            for k in user_triggers:
                if k == substitution.lower():
                    result = Database(self.config).delete_sub_substitution("user_triggers", k, number, group_jid,
                                                                           peer_jid,
                                                                           self.bot_id)
                    if result == 1 or result == 4:
                        if user_triggers[k][number][-3:] == "png" or user_triggers[k][number][-3:] == "jpg":
                            RemoteAdmin(self).send_message(message,
                                                           "Deleted: Response Image \n From: " + substitution)
                        elif user_triggers[k][number][-4:] == "json":
                            RemoteAdmin(self).send_message(message,
                                                           "Deleted: Response GIF \n From: " + substitution)
                        else:
                            RemoteAdmin(self).send_message(message, "Deleted: " + user_triggers[k][
                                number] + "\n From: " + substitution)
                    elif result == 2:
                        RemoteAdmin(self).send_message(message, "Only admins can delete admin triggers.")

    def get_substitution(self, chat_message, substitution, group_jid, peer_jid):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_messages = group_data["group_messages"]
        group_settings = group_data["group_settings"]
        group_admins = group_data["group_admins"]
        admin_triggers = group_data["admin_triggers"]
        user_triggers = group_data["user_triggers"]
        all_subs = {**user_triggers, **admin_triggers}
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        all_admins = {**bot_admins, **group_admins}

        if not group_settings or hasattr(chat_message, "remote_jid") is True:
            return
        sub_status = group_settings["trigger_status"]
        if sub_status == 0:  # Mode 0 Off
            return

        elif sub_status == 1:  # Mode 1 Normal Everyone can add/delete/trigger
            if "*" in all_subs:
                chance = .01
                if random.random() < chance:
                    sub_list = []
                    for x in all_subs["*"]:
                        sub_list.append(x)
                    response = random.choice(sub_list)

                    process_trigger(self, chat_message, "*", response, all_subs, peer_jid,
                                    group_jid)
                    return

            for k in all_subs:
                if k == "*":
                    continue
                regk = k
                punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
                for ele in regk:
                    if ele in punc:
                        regk = regk.replace(ele, "")
                if k == substitution.lower():
                    sub_list = []
                    for x in all_subs[k]:
                        sub_list.append(x)
                    response = random.choice(sub_list)

                    process_trigger(self, chat_message, k, response, all_subs, peer_jid, group_jid)
                    return

                elif regk and regk != "s ":
                    if k[:2] == "$s" and re.search(r"\b{}\b".format(k[3:]), substitution, re.IGNORECASE):
                        sub_list = []
                        for x in all_subs[k]:
                            sub_list.append(x)
                        response = random.choice(sub_list)
                        process_trigger(self, chat_message, k, response, all_subs, peer_jid, group_jid)
                        return

                    else:
                        pass

                    if k[:2] == "$s" and k[3:] in substitution.lower().split():
                        sub_list = []
                        for x in all_subs[k]:
                            sub_list.append(x)
                        response = random.choice(sub_list)

                        process_trigger(self, chat_message, k, response, all_subs, peer_jid, group_jid)
                        return

        elif sub_status == 2:
            if peer_jid in all_admins:
                if "*" in all_subs:
                    chance = .01
                    if random.random() < chance:
                        sub_list = []
                        for x in all_subs["*"]:
                            sub_list.append(x)
                        response = random.choice(sub_list)
                        process_trigger(self, chat_message, "*", response, all_subs,
                                        peer_jid,
                                        group_jid)
                        return
                for k in all_subs:
                    if k == "*":
                        continue
                    regk = k
                    punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
                    for ele in regk:
                        if ele in punc:
                            regk = regk.replace(ele, "")
                    if k == substitution.lower():
                        sub_list = []
                        for x in all_subs[k]:
                            sub_list.append(x)
                        response = random.choice(sub_list)

                        process_trigger(self, chat_message, k, response, all_subs, peer_jid, group_jid)
                        return

                    elif regk and regk != "s ":
                        if k[:2] == "$s" and re.search(r"\b{}\b".format(k[3:]), substitution, re.IGNORECASE):
                            sub_list = []
                            for x in all_subs[k]:
                                sub_list.append(x)
                            response = random.choice(sub_list)

                            process_trigger(self, chat_message, k, response, all_subs, peer_jid, group_jid)
                            return
                        else:
                            pass
                    if k[:2] == "$s" and k[3:] in substitution.lower().split():
                        sub_list = []
                        for x in all_subs[k]:
                            sub_list.append(x)
                        response = random.choice(sub_list)

                        process_trigger(self, chat_message, k, response, all_subs, peer_jid, group_jid)
                        return

            else:
                if "*" in user_triggers:
                    chance = .01
                    if random.random() < chance:
                        sub_list = []
                        for x in user_triggers["*"]:
                            sub_list.append(x)
                        response = random.choice(sub_list)
                        process_trigger(self, chat_message, "*", response, user_triggers,
                                        peer_jid,
                                        group_jid)
                        return
                for k in user_triggers:
                    if k == "*":
                        continue
                    regk = k
                    punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
                    for ele in regk:
                        if ele in punc:
                            regk = regk.replace(ele, "")
                    if k == substitution.lower():
                        sub_list = []
                        for x in user_triggers[k]:
                            sub_list.append(x)
                        response = random.choice(sub_list)
                        process_trigger(self, chat_message, k, response, user_triggers, peer_jid, group_jid)
                        return

                    elif regk and regk != "s ":
                        if k[:2] == "$s" and re.search(r"\b{}\b".format(k[3:]), substitution, re.IGNORECASE):
                            sub_list = []
                            for x in user_triggers[k]:
                                sub_list.append(x)
                            response = random.choice(sub_list)
                            process_trigger(self, chat_message, k, response, user_triggers, peer_jid, group_jid)
                            return
                        else:
                            pass
                    if k[:2] == "$s" and k[3:] in substitution.split():
                        sub_list = []
                        for x in user_triggers[k]:
                            sub_list.append(x)
                        response = random.choice(sub_list)

                        process_trigger(self, chat_message, k, response, user_triggers, peer_jid, group_jid)
                        return

        elif sub_status == 3:  # Mode 3 Admin Only Create/Trigger (user subs ignored)

            if peer_jid in all_admins:

                if "*" in admin_triggers:
                    chance = .01
                    if random.random() < chance:
                        sub_list = []
                        for x in admin_triggers["*"]:
                            sub_list.append(x)
                        response = random.choice(sub_list)
                        process_trigger(self, chat_message, "*", response, admin_triggers,
                                        peer_jid,
                                        group_jid)
                for k in admin_triggers:
                    if k == "*":
                        continue
                    regk = k
                    punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
                    for ele in regk:
                        if ele in punc:
                            regk = regk.replace(ele, "")
                    if k == substitution.lower():
                        sub_list = []
                        for x in admin_triggers[k]:
                            sub_list.append(x)
                        response = random.choice(sub_list)
                        process_trigger(self, chat_message, k, response, admin_triggers, peer_jid, group_jid)
                        return
                    elif regk and regk != "s ":
                        if k[:2] == "$s" and re.search(r"\b{}\b".format(k[3:]), substitution, re.IGNORECASE):
                            sub_list = []
                            for x in admin_triggers[k]:
                                sub_list.append(x)
                            response = random.choice(sub_list)
                            process_trigger(self, chat_message, k, response, admin_triggers, peer_jid, group_jid)
                            return
                        else:
                            pass

                    if k[:2] == "$s" and k[3:] in substitution.lower().split():
                        sub_list = []
                        for x in admin_triggers[k]:
                            sub_list.append(x)
                        response = random.choice(sub_list)
                        process_trigger(self, chat_message, k, response, admin_triggers, peer_jid,
                                        group_jid)
                        return

            else:
                return
        else:
            return


def process_image_sub(client, message, action, sub_type, sub, response, img_url, peer_jid, group_jid):
    sub_id = uuid.uuid4()
    current_dir = os.getcwd() + "/"
    if "https://platform.kik.com/" in img_url:
        if not os.path.exists(current_dir + client.config["paths"]["trigger_media"] + group_jid):
            os.makedirs(current_dir + client.config["paths"]["trigger_media"] + group_jid)
        time.sleep(1)
        result = urllib.request.urlretrieve(img_url,
                                            current_dir + client.config["paths"][
                                                "trigger_media"] + group_jid + "/" + str(sub_id) + ".jpg")
        if result:
            if len(response.split(" ")) > 1:
                text = response.split("$i ")[1] + " "
            else:
                text = ''

            Triggers(client).add_substitution(message, action, sub_type,
                                              [sub, f'{text}' + current_dir + client.config["paths"][
                                                  "trigger_media"] + group_jid +
                                               "/" + str(sub_id) + ".jpg"], group_jid, peer_jid)
            RedisCache(client.config).rem_from_media_sub_queue(peer_jid, group_jid)


def process_gif_sub(client, message, action, sub_type, sub, response, gif_data, peer_jid, group_jid):
    current_dir = os.getcwd() + "/"
    if gif_data:
        gif_id = uuid.uuid4()
        if len(response.split(" ")) > 1:
            text = response.split("$g ")[1] + " "
        else:
            text = ''
        if not os.path.exists(current_dir + client.config["paths"]["trigger_media"] + group_jid):
            os.makedirs(current_dir + client.config["paths"]["trigger_media"] + group_jid)
        with open(current_dir + client.config["paths"]["trigger_media"] + group_jid + "/" + str(gif_id) + ".json",
                  "w+") as gif_save:
            json.dump(gif_data, gif_save, indent=4)
        gif_save.close()
        Triggers(client).add_substitution(message, action, sub_type,
                                          [sub, f'{text}' + current_dir + client.config["paths"][
                                              "trigger_media"] + group_jid + "/"
                                           + str(gif_id) + ".json"], group_jid, peer_jid)
        RedisCache(client.config).rem_from_media_sub_queue(peer_jid, group_jid)


def process_vid_sub(client, message, action, sub_type, sub, response, vid_url, peer_jid, group_jid):
    current_dir = os.getcwd() + "/"
    vid_id = uuid.uuid4()
    if "https://platform.kik.com/" in vid_url:
        if not os.path.exists(current_dir + client.config["paths"]["trigger_media"] + group_jid):
            os.makedirs(current_dir + client.config["paths"]["trigger_media"] + group_jid)
        time.sleep(1)
        vid = requests.get(vid_url, stream=True)
        if vid.status_code == 200:
            with open(current_dir + client.config["paths"]["trigger_media"] + group_jid + "/" + str(vid_id) + ".mp4",
                      'wb') as f:
                for chunk in vid.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                f.close()
            thumbnail = current_dir + client.config["paths"]["trigger_media"] + group_jid + "/" + str(vid_id) + ".jpg"
            video = current_dir + client.config["paths"]["trigger_media"] + group_jid + "/" + str(vid_id) + ".mp4"
            command = "ffmpeg -i {} -ss 00:00:00.000 -vframes 1 {}".format(video, thumbnail)
            if len(response.split(" ")) > 1:
                text = response.split("$v ")[1] + " "
            else:
                text = ''
            result = subprocess.run(
                # Command as a list, to avoid shell=True
                command.split(),
                # Expect textual output, not bytes; let Python .decode() on the fly
                text=True,
                # Shorthand for stdout=PIPE stderr=PIPE etc etc
                capture_output=True,
                # Raise an exception if ping fails (maybe try/except it separately?)
                check=True)
            Triggers(client).add_substitution(message, action, sub_type,
                                              [sub, f'{text}' + current_dir + client.config["paths"][
                                                  "trigger_media"] + group_jid +
                                               "/" + str(vid_id) + ".mp4"], group_jid, peer_jid)
            RedisCache(client.config).rem_from_media_sub_queue(peer_jid, group_jid)


def media_sub_timeout(client, chat_message, peer_jid, group_jid):
    RemoteAdmin(client).send_message(chat_message, "Send media you would like to set, you have 3 minutes.")
    time.sleep(180)
    sub_queue = RedisCache(client.config).get_all_media_sub_queue(group_jid)
    for su in sub_queue:
        if str(su.decode("utf-8")) == peer_jid:
            RedisCache(client.config).rem_from_media_sub_queue(peer_jid, group_jid)


def process_trigger(client, chat_message, trigger, trigger_response, sub_dict, peer_jid, group_jid):
    if sub_dict[trigger][trigger_response][-3:] == "mp4":
        if sub_dict[trigger][trigger_response][:1] == "[":
            text_response = sub_dict[trigger][trigger_response].split("] ")[0].replace("[", "").replace("]", "")
            vid_response = sub_dict[trigger][trigger_response].split("] ")[1]
            text_message = process_message(client.config, "group", text_response,
                                           peer_jid,
                                           group_jid,
                                           "0", "0")
            video = vid_response
            thumbnail = vid_response.replace("mp4", "jpg")
            dur = cv2.VideoCapture(video)
            duration = dur.get(cv2.CAP_PROP_POS_MSEC)
            client.client.send_chat_video(group_jid, video, thumbnail, duration)
            time.sleep(1.5)
            client.client.send_chat_message(group_jid, text_message)
        else:
            video = sub_dict[trigger][trigger_response]
            thumbnail = sub_dict[trigger][trigger_response].replace("mp4", "jpg")
            dur = cv2.VideoCapture(video)
            duration = dur.get(cv2.CAP_PROP_POS_MSEC)
            client.client.send_chat_video(group_jid, video, thumbnail, duration)
        return
    elif sub_dict[trigger][trigger_response][-3:] == "png" or sub_dict[trigger][trigger_response][-3:] == "jpg":
        if sub_dict[trigger][trigger_response][:1] == "[":
            text_response = sub_dict[trigger][trigger_response].split("] ")[0].replace("[", "").replace("]", "")
            image_response = sub_dict[trigger][trigger_response].split("] ")[1]
            text_message = process_message(client.config, "group", text_response,
                                           peer_jid,
                                           group_jid,
                                           "0", "0")
            client.client.send_chat_image(group_jid, image_response)
            time.sleep(1.5)
            client.client.send_chat_message(group_jid, text_message)
        else:
            client.client.send_chat_image(group_jid, sub_dict[trigger][trigger_response])
        return
    elif sub_dict[trigger][trigger_response][-4:] == "json":
        print(sub_dict[trigger][trigger_response])
        if sub_dict[trigger][trigger_response][:1] == "[":
            text_response = sub_dict[trigger][trigger_response].split("] ")[0].replace("[", "").replace("]", "")
            image_response = sub_dict[trigger][trigger_response].split("] ")[1]
            text_message = process_message(client.config, "group", text_response,
                                           peer_jid,
                                           group_jid,
                                           "0", "0")
            client.client.send_gif_image_sub(group_jid, image_response)
            time.sleep(1.5)
            client.client.send_chat_message(group_jid, text_message)
        else:
            print(sub_dict[trigger][trigger_response])
            client.client.send_gif_image_sub(group_jid, sub_dict[trigger][trigger_response])
        return
    elif sub_dict[trigger][trigger_response][:3] == "$gs":
        if "[" in sub_dict[trigger][trigger_response][4:]:
            text_response = sub_dict[trigger][trigger_response][4:].split("] ")[0].replace("[", "").replace("]", "")
            search_term = sub_dict[trigger][trigger_response][4:].split("] ")[1]
            text_message = process_message(client.config, "group", text_response,
                                           peer_jid,
                                           group_jid,
                                           "0", "0")
            client.client.send_gif_image(group_jid, search_term)
            time.sleep(1.5)
            client.client.send_chat_message(group_jid, text_message)
            return
        else:
            search_term = sub_dict[trigger][trigger_response][4:]
            client.client.send_gif_image(group_jid, search_term)
            return
    elif sub_dict[trigger][trigger_response][:2] == "$l":
        title = sub_dict[trigger][trigger_response].split("$l ")[1].split("\n")[0]
        text = sub_dict[trigger][trigger_response].split("$l ")[1].split("\n")[1]
        link = sub_dict[trigger][trigger_response].split("$l ")[1].split("\n")[2]
        app = link.lower().split("https://")[1].split("/")[0]
        client.client.send_link(group_jid, link, title, text, app)
        return
    # elif sub_dict[trigger][trigger_response][:2] == "$a":
    #     command = sub_dict[trigger][trigger_response].split("$a ")[1]
    #     chat_message.body = command
    #     chat_message.from_jid = bot_jid
    #     callback.on_group_message_received(chat_message)
    #     return
    # elif sub_dict[trigger][trigger_response][:1] == "(":
    #     choice_text = sub_dict[trigger][trigger_response].split(") ")[0]
    #     choice_text = choice_text.replace("(", "").replace(") ", "")
    #     choices_list = sub_dict[trigger][trigger_response].split(") ")[1].replace("[", "").replace("]", "")
    #     choices_list = choices_list.split(", ")
    #     choices_list = list(choices_list)
    #     choice = random.choice(choices_list)
    #     choice_text = process_message("group", choice_text, peer_jid, group_jid, 0, 0)
    #     message = choice_text + " " + choice
    #     client.send_chat_message(group_jid, message)
    #     return

    elif "]" in sub_dict[trigger][trigger_response] and "[" in sub_dict[trigger][trigger_response]:
        choice_list_count = sub_dict[trigger][trigger_response].count("[")
        if choice_list_count == 1:
            choices_list = sub_dict[trigger][trigger_response].split("[")[1].split("]")[0]
            choice_text_1 = sub_dict[trigger][trigger_response].split("]")[1]
            choice_text_2 = sub_dict[trigger][trigger_response].split("[")[0]
            choices_list = choices_list.split(", ")
            choices_list = list(choices_list)
            choice = random.choice(choices_list)
            unproc_message = str(choice_text_2) + str(choice) + str(choice_text_1)
            message = process_message(client.config, "group", unproc_message, peer_jid, group_jid, 0, 0)
            client.client.send_chat_message(group_jid, message)
        elif choice_list_count > 1:
            random_options = sub_dict[trigger][trigger_response].count("[")
            choices_list = sub_dict[trigger][trigger_response].split("[")[1].split("]")[0]
            choice_text_1 = sub_dict[trigger][trigger_response].split("]", 1)[1]
            choice_text_2 = sub_dict[trigger][trigger_response].split("[", 1)[0]
            choices_list = choices_list.split(", ")
            choices_list = list(choices_list)
            choice = random.choice(choices_list)
            unproc_message = str(choice_text_2) + str(choice) + str(choice_text_1)
            for i in range(random_options - 1):
                if "[" in unproc_message:
                    choices_list = unproc_message.split("[")[1].split("]")[0]
                    choice_text_1 = unproc_message.split("]", 1)[1]
                    choice_text_2 = unproc_message.split("[", 1)[0]
                    choices_list = choices_list.split(", ")
                    choices_list = list(choices_list)
                    choice = random.choice(choices_list)
                    unproc_message = str(choice_text_2) + str(choice) + str(choice_text_1)

            message = process_message(client.config, "group", unproc_message, peer_jid, group_jid, 0, 0)
            client.client.send_chat_message(group_jid, message)
        return
    else:
        message = process_message(client.config, "group", sub_dict[trigger][trigger_response],
                                  peer_jid,
                                  group_jid,
                                  "0", "0")
        client.client.send_chat_message(group_jid, message)
        return
