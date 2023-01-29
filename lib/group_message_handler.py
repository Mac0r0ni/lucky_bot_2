import random
import re
import time

from colorama import Fore, Style

from lib.database_handler import Database
from lib.group_admin_tools import WelcomeMessage, Lock, Noob, Invite, NameGrab, Verification, GroupTimer, LeaveMessage, \
    BotHelpers, Silent, Censor, Forward, Profile, Purge, UserCap, Whitelist, BotSFW, BackupRestore, DataTransfer, \
    BotStatus, GroupStats
from lib.group_fun_handler import ChanceGames
from lib.history_handler import GroupHistory
from lib.message_processing_handler import process_message
from lib.redis_handler import RedisCache
from lib.remote_admin_handler import RemoteAdmin
from lib.search_handler import Search
from lib.talkers_lurkers_handler import TalkerLurker
from lib.trigger_handler import Triggers
from lib.user_handler import User


class GroupMessage:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name
        self.bot_username = client.bot_username
        self.debug = f'[' + Style.BRIGHT + Fore.MAGENTA + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.GREEN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

    def group_message_parser(self, chat_message):
        if self.config["general"]["debug"] >= 1:
            print(self.debug + f'{chat_message.from_jid} from group ID {chat_message.group_jid} says: {chat_message.body}' + Style.RESET_ALL)

        gm = chat_message.body.lower()  # Get group message and make it lowercase
        prefix = self.config["general"]["prefix"]

        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        try:
            group_settings = group_data["group_settings"]
            group_members = group_data["group_members"]
            group_admins = group_data["group_admins"]
            censor_words = group_data["censor_words"]
            group_messages = group_data["group_messages"]
        except Exception as e:
            return

        try:
            name = group_data["group_members"][chat_message.from_jid]["display_name"]
        except:
            if group_settings["sfw_status"] == 1:
                name = random.choice(self.config["responses"]["sfw_names"])
            else:
                name = random.choice(self.config["responses"]["nsfw_names"])

        if "46.30." in gm or "91.228." in gm or "212.224." in gm or "195.245." in gm or "to show you my naked pics" in gm or "let's fun " in gm or "lets fun " in gm:
            user_info = RedisCache(self.config).get_single_last_queue("joiner", chat_message.group_jid)
            if user_info:
                if chat_message.from_jid == user_info["alias_jid"]:
                    self.client.send_chat_message(chat_message.group_jid, "Bye Hoe-bot")
                    self.client.remove_peer_from_group(chat_message.group_jid, chat_message.from_jid)
                    User(self).group_user_remove(chat_message.from_jid, chat_message.group_jid)
                    return

                # add talker/lurker time
        RedisCache(self.config).set_single_talker_lurker("talkers", time.time(), chat_message.from_jid, chat_message.group_jid)
        RedisCache(self.config).set_single_talker_lurker("lurkers", time.time(), chat_message.from_jid, chat_message.group_jid)
        RedisCache(self.config).set_single_history("message", chat_message.from_jid, chat_message.group_jid)


        if group_settings["bot-helper_status"] == 0:
            if name == "Rage bot" or name == "Navi 🦋" or name == "C​а​s​i​n​ο​ B​ο​t​":
                return

        if group_settings["verification_status"] == 1:
            join_queue = RedisCache(self.config).get_all_join_queue(self.bot_id)
            if join_queue:
                if chat_message.from_jid.encode("utf-8") in join_queue:
                    peer_data = RedisCache(self.config).get_single_join_queue(chat_message.from_jid, self.bot_id)
                    if peer_data:
                        if time.time() - int(peer_data["join_time"]) <= group_settings["verification_time"]:
                            if int(peer_data["verified"]) == 0:
                                Verification(self).eval_message(chat_message.from_jid,
                                                                       chat_message.group_jid, chat_message.body)
                                return

        if group_settings["censor_status"] >= 1:
            if chat_message.from_jid not in group_members:
                return
            if chat_message.from_jid not in group_admins:
                #if "cap_whitelist" not in members[chat_message.from_jid]:
                #    members[chat_message.from_jid]["cap_whitelist"] = 0
                #    Database().update_group_json("group_members", members, chat_message.group_jid)
                #    members = RedisCache().get_group_json("group_members", chat_message.group_jid)
                if group_members[chat_message.from_jid]["cap_whitelist"] == 0:
                    censored = False
                    word = ""
                    if group_settings["censor_status"] == 1:
                        for c in censor_words:
                            if chat_message.body.lower() == c.lower():
                                word = c
                                censored = True
                    elif group_settings["censor_status"] == 2:
                        for w in censor_words:
                            result = re.search(r"\b{}\b".format(w), gm, re.IGNORECASE)
                            if result:
                                word = w
                                censored = True
                    if censored:
                        if group_settings["censor_time"] >= 1:
                            warned = RedisCache(self.config).get_all_censor_cache(chat_message.group_jid)
                            if not warned:
                                warned = {"None": "None"}
                            if chat_message.from_jid.encode("utf-8") in warned:
                                user_info = RedisCache(self.config).get_censor_cache(chat_message.from_jid, chat_message.group_jid)
                                warn_time = (int(user_info["warn_time"]))
                                now = time.time()
                                a = float(now) - float(warn_time)
                                if a < int(group_settings["censor_time"]):
                                    remove_message = process_message(self.config, "group", group_messages["censor-kick_message"],
                                                                     chat_message.from_jid,
                                                                     chat_message.group_jid, self.bot_id, "245")
                                    self.client.send_chat_message(chat_message.group_jid, remove_message)
                                    self.client.remove_peer_from_group(chat_message.group_jid, chat_message.from_jid)
                                    RedisCache(self.config).rem_from_censor_cache(chat_message.from_jid, chat_message.group_jid)
                                    return
                                else:
                                    warn_message = process_message(self.config, "group", group_messages["censor-warn_message"].replace("$cw", word),
                                                                     chat_message.from_jid,
                                                                     chat_message.group_jid, self.bot_id, "245")
                                    self.client.send_chat_message(chat_message.group_jid, warn_message)

                                    RedisCache(self.config).add_censor_cache(chat_message.from_jid, chat_message.group_jid)
                                    return
                            else:
                                warn_message = process_message(self.config, "group",
                                                               group_messages["censor-warn_message"].replace("$cw",
                                                                                                             word),
                                                               chat_message.from_jid,
                                                               chat_message.group_jid, self.bot_id, "245")
                                self.client.send_chat_message(chat_message.group_jid, warn_message)
                                RedisCache(self.config).add_censor_cache(chat_message.from_jid, chat_message.group_jid)
                                return

                        else:
                            remove_message = process_message(self.config, "group",
                                                             group_messages["censor-kick_message"],
                                                             chat_message.from_jid,
                                                             chat_message.group_jid, self.bot_id, "245")
                            self.client.send_chat_message(chat_message.group_jid, remove_message)
                            self.client.remove_peer_from_group(chat_message.group_jid, chat_message.from_jid)
                            User(self).group_user_remove(chat_message.from_jid, chat_message.group_jid)
                            RedisCache(self.config).rem_from_censor_cache(chat_message.from_jid, chat_message.group_jid)
                            return

        if gm.split()[0][0] == prefix:
            # if message starts with the prefix
            if gm == prefix + "welcome" or prefix + "welcome message" in gm or gm == prefix + "welcome status":
                # Welcome Message Status or Change
                WelcomeMessage(self).main(chat_message, prefix)
                return
            elif gm == prefix + "exit" or prefix + "exit message" in gm or gm == prefix + "exit status":
                # Welcome Message Status or Change
                LeaveMessage(self).main(chat_message, prefix)
                return
            elif gm == prefix + "lock" or prefix + "lock message" in gm or gm == prefix + "lock status":
                # Lock Status, Message Change, Or Status Change
                Lock(self).main(chat_message, prefix)
                return
            elif prefix + "noob" in gm:
                Noob(self).main(chat_message, prefix)
                return
            elif prefix + "invite" in gm:
                Invite(self).main(chat_message, prefix)
                return
            elif prefix + "helper" in gm:
                BotHelpers(self).main(chat_message, prefix)
                return
            elif prefix + "silent" in gm:
                Silent(self).main(chat_message, prefix)
                return
            elif prefix + "censor" in gm or prefix + "cmode" in gm:
                Censor(self).main(chat_message, prefix)
                return
            elif prefix + "bypass" in gm or prefix + "forward" in gm:
                Forward(self).main(chat_message, prefix)
                return
            elif prefix + "pfp" in gm:
                Profile(self).main(chat_message, prefix)
                return
            elif prefix + "cap" in gm:
                UserCap(self).main(chat_message, prefix)
                return
            elif prefix + "whitelist" in gm:
                Whitelist(self).main(chat_message, prefix)
                return
            elif prefix + "purge" in gm:
                Purge(self).main(chat_message, prefix)
                return
            elif prefix + "sfw" in gm:
                BotSFW(self).main(chat_message, prefix)
                return
            elif gm == prefix + "backup" or prefix + "restore" in gm:
                BackupRestore(self).main(chat_message, prefix)
                return
            elif prefix + "transfer" in gm:
                DataTransfer(self).main(chat_message, prefix, "gm")
                return
            elif gm == prefix + "grab" or gm == prefix + "grab status":
                # grab username change and status
                NameGrab(self).main(chat_message, prefix)
                return
            elif prefix + "history" in gm:
                GroupHistory(self).main(chat_message, prefix)
                return
            elif prefix + "trigger" in gm or prefix + "mode" in gm or prefix + "delete" in gm:
                Triggers(self).main(chat_message, prefix)
                return
            elif prefix + "verify" in gm:
                Verification(self).main(chat_message, prefix)
                return
            elif prefix + "timer" in gm:
                GroupTimer(self).main(chat_message, prefix)
                return
            elif prefix + "search" in gm or prefix + "youtube" in gm or prefix + "yt" in gm or prefix + "who" in gm or prefix + "urban" in gm:
                Search(self).main(chat_message, prefix)
                return
            elif gm == prefix + "status":
                BotStatus(self).main(chat_message, prefix)
                return
            elif gm == prefix + "stats":
                GroupStats(self).main(chat_message, prefix)
                return
            elif gm == prefix + "gjid":  # check if the message is equal to gjid
                # if it is send a group message with the group jid
                RemoteAdmin(self).send_message(chat_message, "Group JID: " + chat_message.group_jid)
            elif prefix + "roll" in gm or prefix + "8ball " in gm or gm == "🎲":
                ChanceGames(self).main(chat_message, prefix, name)

            elif prefix + "say" in gm:
                if hasattr(chat_message, "remote_jid"):
                    self.client.send_chat_message(chat_message.group_jid, chat_message.body[4:])
                    RemoteAdmin(self).send_message(chat_message, "Said " + chat_message.body[4:])
            elif prefix + "talkers" in gm or prefix + "lurkers" in gm:
                TalkerLurker(self).main(chat_message, prefix)
                return

            elif gm == prefix + "leave":
                if group_settings["sfw_status"] == 1:
                    deny_resp = self.config["responses"]["sfw_leave_deny"]
                    leave_response = self.config["responses"]["sfw_leave"]
                else:
                    deny_resp = self.config["responses"]["nsfw_leave_deny"]
                    leave_response = self.config["responses"]["nsfw_leave"]
                if group_admins:
                    if chat_message.from_jid in group_admins:
                        self.client.send_chat_message(chat_message.group_jid, str(random.choice(leave_response))).format(name)
                        self.client.leave_group(chat_message.group_jid)
                        Database(self.config).remove_group(chat_message.group_jid)
                else:
                    RemoteAdmin(self).send_message(chat_message, str(random.choice(deny_resp))).format(name)

            elif gm == prefix + "members":
                bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
                group_admins = group_data["group_admins"]
                all_admins = {**bot_admins, **group_admins}
                if all_admins:
                    if chat_message.from_jid in all_admins:
                        if chat_message.group_jid:
                            list_message_1 = str("+++++++ User List +++++++\n")
                            list_message_1 += str("ID        Member\n")
                            list_message_1 += str("++++++++++++++++++++++++\n")
                            list_message_2 = str("++++++ User List 2 ++++++\n")
                            list_message_2 += str("ID        Member\n")
                            list_message_2 += str("++++++++++++++++++++++++\n")
                            count = 0
                            member_list = group_data["group_members"]
                            member_dict = {}
                            for m in member_list:
                                member_dict[member_list[m]["display_name"][:10]] = int(member_list[m]["uid"])
                            sorted_members = {k: v for k, v in sorted(member_dict.items(), key=lambda item: item[1])}
                            for u in sorted_members:
                                count += 1
                                if len(str(sorted_members[u])) > 1:
                                    uid = str(sorted_members[u]) + "       "
                                elif len(str(sorted_members[u])) == 2:
                                    uid = str(sorted_members[u]) + "      "
                                else:
                                    uid = str(sorted_members[u]) + "     "
                                if count <= 50:
                                    list_message_1 += uid + u[:10] + "\n"
                                else:
                                    list_message_2 += uid + u[:10] + "\n"

                            if count <= 50:
                                RemoteAdmin(self).send_message(chat_message, list_message_1)
                            elif count > 50:
                                RemoteAdmin(self).send_message(chat_message, list_message_1)
                                RemoteAdmin(self).send_message(chat_message, list_message_2)
                    else:
                        if group_settings["sfw_status"] == 1:
                            RemoteAdmin(self).send_message(chat_message, "Nope, you aren't an admin...")
                        else:
                            RemoteAdmin(self).send_message(chat_message, f"Fuck off, you aren't an admin {name}.")
        else:
            if gm == "ping":
                if group_settings["sfw_status"] == 1:
                    ping_resp = self.config["responses"]["sfw_ping"]
                else:
                    ping_resp = self.config["responses"]["nsfw_ping"]
                RemoteAdmin(self).send_message(chat_message, str(random.choice(ping_resp)).format(name))

            elif "🎲" in gm and gm.split()[0][0] == "🎲":
                ChanceGames(self).main(chat_message, prefix, name)

            elif "-censor" in gm and gm.split()[0] == "-censor":
                Censor(self).main(chat_message, prefix)
                return

            elif " >>+ " in gm or " >>- " in gm or " >+ " in gm or " >- " in gm or " > " in gm or " >> " in gm and "\">>\"" not in gm and "\">\"" not in gm:
                Triggers(self).main(chat_message, prefix)
                return

            elif gm == 'hey' or gm == "hello" or gm == "hi" or gm == "yo":
                if group_settings["sfw_status"] == 1:
                    greetings = self.config["responses"]["sfw_greetings"]
                else:
                    greetings = self.config["responses"]["nsfw_greetings"]
                RemoteAdmin(self).send_message(chat_message, str(random.choice(greetings)).format(name))
                return

            else:
                if group_settings["trigger_status"] > 0:
                    Triggers(self).get_substitution(chat_message, chat_message.body,
                                                                          chat_message.group_jid,
                                                                          chat_message.from_jid)

        return
