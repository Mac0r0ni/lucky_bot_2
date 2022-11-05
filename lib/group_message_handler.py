import random
import time

from colorama import Fore, Style

from lib.database_handler import Database
from lib.group_admin_tools import WelcomeMessage, Lock, Noob, Invite, NameGrab, Verification
from lib.group_fun_handler import ChanceGames
from lib.redis_handler import RedisCache
from lib.remote_admin_handler import RemoteAdmin
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

    def group_message_parser(self, chat_message):
        if self.config["general"]["debug"] == 1 or self.config["general"]["debug"] == 2:
            print(Fore.LIGHTGREEN_EX + f'[+] {chat_message.from_jid} from group ID {chat_message.group_jid} says: {chat_message.body}' + Style.RESET_ALL)

        gm = chat_message.body.lower()  # Get group message and make it lowercase
        prefix = self.config["general"]["prefix"]

        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        try:
            group_settings = group_data["group_settings"]
            group_admins = group_data["group_admins"]
        except Exception as e:
            return
        funny_names = ["Champ", "Young man", "Whats her face", "Chump", "Dingus", "McTitsMcGee"]
        try:
            name = group_data["group_members"][chat_message.from_jid]["display_name"]
        except:
            name = random.choice(funny_names)

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

        if gm.split()[0][0] == prefix:
            # if message starts with the prefix
            if gm == prefix + "welcome" or prefix + "welcome message" in gm or gm == prefix + "welcome status":
                # Welcome Message Status or Change
                WelcomeMessage(self).main(chat_message, prefix)
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
            elif gm == prefix + "grab" or gm == prefix + "grab status":
                # grab username change and status
                NameGrab(self).main(chat_message, prefix)
                return
            elif prefix + "trigger" in gm or prefix + "mode" in gm or prefix + "delete" in gm:
                Triggers(self).main(chat_message, prefix)
                return
            elif prefix + "verify" in gm:
                Verification(self).main(chat_message, prefix)
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
                deny_resp = ["Nice try dingus.", "Uhh No?", "Make me, " + name, "What if I don't want to?", "You don't have the power, nerrrrd.", "Maybe if you ask nicely. Nah, just kidding."]
                leave_response = ["Later boners.", "I didn't want to be here anyway.", "With pleasure... gross.", "Fine.... jerk.", "I'll start my own group then.. with hookers and Blackjack. Infact forget the Blackjack!", "I don't like you anyway. " + name, name + ", is a jerky-mc-jerkass and tried to get in my pants."]
                if group_admins:
                    if chat_message.from_jid in group_admins:
                        self.client.send_chat_message(chat_message.group_jid, random.choice(leave_response))
                        self.client.leave_group(chat_message.group_jid)
                        Database(self.config).remove_group(chat_message.group_jid)
                else:
                    RemoteAdmin(self).send_message(chat_message, random.choice(deny_resp))

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
                        RemoteAdmin(self).send_message(chat_message, "Fuck off, you aren't an admin...")
        else:
            if gm == "ping":
                ping_resp = ["What do you want boner?", "Yea I am here.. Unfortunately", "Polo... wait no Pong", "The person ^ gives good head.", "I'm with stupid ^", "Damn, you are so annoying.", "Ping your damn self.", "Hey dingus.", "Uhhh, I don't give a shit.", "Clingy much? Fuck dude..."]
                RemoteAdmin(self).send_message(chat_message, random.choice(ping_resp))

            elif "🎲" in gm and gm.split()[0][0] == "🎲":
                ChanceGames(self).main(chat_message, prefix, name)

            elif " >>+ " in gm or " >>- " in gm or " >+ " in gm or " >- " in gm or " > " in gm or " >> " in gm and "\">>\"" not in gm and "\">\"" not in gm:
                Triggers(self).main(chat_message, prefix)
                return

            elif gm == 'hey' or gm == "hello" or gm == "hi" or gm == "yo":
                greetings = ["What’s kickin’, " + name, "‘Ello, gov'nor!", "What's up bitches?", "Hey-oooo!", "What up forknuts?", "Ehh, It's " + name]
                RemoteAdmin(self).send_message(chat_message, random.choice(greetings))
                return

            else:
                if group_settings["trigger_status"] > 0:
                    Triggers(self).get_substitution(chat_message, chat_message.body,
                                                                          chat_message.group_jid,
                                                                          chat_message.from_jid)

        return
