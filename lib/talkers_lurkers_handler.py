#!/usr/bin/env python3

# Python 3 Core Libraries
import time

# Python 3 Third Party Libraries


# Python 3 Project Libraries


# --------------------------
#  Talkers/Lurkers
# --------------------------
from lib.redis_handler import RedisCache
from lib.remote_admin_handler import RemoteAdmin


class TalkerLurker:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name
        self.bot_username = client.bot_username

    def main(self, chat_message, prefix):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        if not group_data:
            return
        group_admins = group_data["group_admins"]
        all_admins = {**bot_admins, **group_admins}
        s = chat_message.body.lower()
        if s == prefix + "talkers":
            if chat_message.from_jid in all_admins:
                self.get_talkers(chat_message)
            else:
                RemoteAdmin(self).send_message(chat_message, "Not an admin, so no...")

        elif s[:8] == prefix + "lurkers":
            if chat_message.from_jid in all_admins:
                command = s.split()
                if len(command) == 1:
                    self.get_lurkers(chat_message, 0)
                elif len(command) == 2:
                    try:
                        minutes = int(command[1])
                    except Exception as e:
                        RemoteAdmin(self).send_message(chat_message, "Please give number after command +lurkers 2")
                        return
                    if minutes > 30:
                        RemoteAdmin(self).send_message(chat_message,
                                                              "Minutes should be less than 30")
                        return
                    else:
                        self.get_lurkers(chat_message, minutes)


            else:
                RemoteAdmin(self).send_message(chat_message, "Ha nice try, but you aren't an admin dingus.")

        else:
            RemoteAdmin(self).send_message(chat_message, "Read the manual, and try again.")

    def get_talkers(self, chat_message):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        if not group_data:
            return
        if "talkers" in group_data:
            talkers = group_data["talkers"]
        else:
            RemoteAdmin(self).send_message(chat_message, "No Talkers Data")
            if "group_members" in group_data:
                RedisCache(self.config).add_all_talker_lurker("talkers", group_data["group_members"], chat_message.group_jid)
            return
        members = group_data["group_members"]

        for t in talkers:
            if t not in members:
                RedisCache(self.config).remove_single_talker_lurker("talkers", t, chat_message.group_jid)
        for m in members:
            if m not in talkers:
                RedisCache(self.config).add_single_talker_lurker("talkers", m, chat_message.group_jid)
        current_talkers = RedisCache(self.config).get_all_talker_lurkers("talkers", chat_message.group_jid)
        sort_users = sorted(current_talkers.items(), key=lambda x: x[1], reverse=True)
        num_users = len(sort_users)
        req_type = "Talkers"
        self.build_output(chat_message, req_type, num_users, sort_users, members)

    def get_lurkers(self, chat_message, lurk_time):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        if not group_data:
            return

        if "lurkers" in group_data:
            lurkers = group_data["lurkers"]
        else:
            RemoteAdmin(self).send_message(chat_message, "No Lurkers Data")
            if "group_members" in group_data:
                RedisCache(self.config).add_all_talker_lurker("lurkers", group_data["group_members"], chat_message.group_jid)
            return

        members = group_data["group_members"]
        for u in lurkers:
            if u not in members:
                RedisCache(self.config).remove_single_talker_lurker("lurkers", u, chat_message.group_jid)
        for m in members:
            if m not in lurkers:
                RedisCache(self.config).add_single_talker_lurker("lurkers", m, chat_message.group_jid)

        raw_users = RedisCache(self.config).get_all_talker_lurkers("lurkers", chat_message.group_jid)
        if lurk_time == 0:
            sort_users = sorted(raw_users.items(), key=lambda x: x[1], reverse=True)
            num_users = len(sort_users)
        else:
            seconds = lurk_time * 60
            lurking_users = {}
            for u in raw_users:
                if (time.time() - raw_users[u]) <= seconds:
                    lurking_users[u] = raw_users[u]
            num_users = len(lurking_users)
            sort_users = sorted(lurking_users.items(), key=lambda x: x[1], reverse=True)

        req_type = "Lurkers"

        self.build_output(chat_message, req_type, num_users, sort_users, members)

    def build_output(self, chat_message, req_type, num_users, sort_users, user_data):

        message1 = "+-------" + req_type + " Activity-------+ \n"
        message1 += "Time".ljust(20) + "Member Name:\n"
        message1 += "+----------Page 1-------------+ \n"
        message2 = "+-------" + req_type + " Activity-------+ \n"
        message2 += "Time".ljust(20) + "Member Name:\n"
        message2 += "+----------Page 2-------------+ \n"

        count = 0
        for i in sort_users:
            if user_data[i[0]] is not None:
                count += 1
                if int(float(i[1])) == 0:
                    txt = '{:<25}{:<}'.format("--:--:--".rjust(16), user_data[i[0]]["display_name"][:10])
                    if count <= 50:
                        message1 += txt + "\n"
                    elif count > 50:
                        message2 += txt + "\n"
                else:
                    a = int(float(i[1]))
                    b = int(float(time.time()))
                    c = b - a
                    days = c // 86400
                    if days == 0:
                        days = ""
                        day_text = "    "
                    elif days < 10:
                        days = "    " + str(days)
                        day_text = "d, "
                    else:
                        day_text = "d, "
                    hours = c // 3600 % 24
                    if hours == 0:
                        hours = "00"
                    elif hours < 10:
                        hours = "0" + str(hours)
                    minutes = c // 60 % 60
                    if minutes == 0:
                        minutes = "00"
                    elif minutes < 10:
                        minutes = "0" + str(minutes)
                    seconds = c % 60
                    if seconds == 0:
                        seconds = "00"
                    elif seconds < 10:
                        seconds = "0" + str(seconds)
                    data = str(days) + day_text + str(hours) + ":" + str(minutes) + ":" + str(seconds)
                    txt = '{:<25}{:<}'.format(data.rjust(16), user_data[i[0]]["display_name"][:10])
                    if count <= 50:
                        message1 += txt + "\n"
                    elif count > 50:
                        message2 += txt + "\n"

        if count > 50:
            message2 += str("                           \n")
            message2 += str("Showing " + str(count) + " members of " + str(num_users) + "\n")
        else:
            message1 += str("                           \n")
            message1 += str("Showing " + str(count) + " members of " + str(num_users) + "\n")

        if count <= 50:
            RemoteAdmin(self).send_message(chat_message, message1)
        elif count > 50:
            RemoteAdmin(self).send_message(chat_message, message1)
            RemoteAdmin(self).send_message(chat_message, message2)
